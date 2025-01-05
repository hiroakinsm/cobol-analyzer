from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from dataclasses import dataclass
import asyncio
import docker
import kubernetes
from kubernetes import client, config
import yaml
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class DeploymentConfig:
    """デプロイメント設定"""
    app_name: str = "cobol-analyzer"
    version: str = "latest"
    namespace: str = "default"
    replicas: int = 3
    docker_registry: str = ""
    kube_config: str = "~/.kube/config"
    env_file: str = ".env"
    health_check_path: str = "/health"
    resource_limits: Dict[str, str] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                'cpu': '1000m',
                'memory': '2Gi'
            }

class DeploymentManager:
    """デプロイメント処理を管理するクラス"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self._docker_client = docker.from_env()
        self._setup_kubernetes()
        self._deployment_status: Dict[str, Any] = {}

    def _setup_kubernetes(self):
        """Kubernetes設定の初期化"""
        try:
            config.load_kube_config(self.config.kube_config)
            self._kube_client = client.CoreV1Api()
            self._kube_apps = client.AppsV1Api()
        except Exception as e:
            logger.error(f"Kubernetes設定でエラー: {str(e)}")

    async def deploy(self) -> Dict[str, Any]:
        """アプリケーションのデプロイ"""
        try:
            # Dockerイメージのビルドとプッシュ
            image_result = await self._handle_docker_image()
            if not image_result.get('success'):
                return self._create_result('image_failed', image_result)

            # Kubernetesリソースの作成
            k8s_result = await self._create_kubernetes_resources()
            if not k8s_result.get('success'):
                return self._create_result('k8s_failed', k8s_result)

            # デプロイメントの監視
            status = await self._monitor_deployment()
            
            return self._create_result('success', status)
            
        except Exception as e:
            logger.error(f"デプロイでエラー: {str(e)}")
            return self._create_result('error', {'error': str(e)})

    async def _handle_docker_image(self) -> Dict[str, Any]:
        """Dockerイメージの処理"""
        try:
            # イメージのビルド
            image_tag = f"{self.config.docker_registry}/{self.config.app_name}:{self.config.version}"
            image = self._docker_client.images.build(
                path=".",
                tag=image_tag,
                rm=True
            )

            # レジストリへのプッシュ
            if self.config.docker_registry:
                self._docker_client.images.push(
                    repository=f"{self.config.docker_registry}/{self.config.app_name}",
                    tag=self.config.version
                )

            return {
                'success': True,
                'message': 'イメージ処理成功',
                'image_tag': image_tag
            }
        except Exception as e:
            logger.error(f"Dockerイメージ処理でエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _create_kubernetes_resources(self) -> Dict[str, Any]:
        """Kubernetesリソースの作成"""
        try:
            # 環境変数の読み込み
            env_vars = self._load_env_vars()

            # Deploymentの作成
            deployment = self._create_deployment_object(env_vars)
            self._kube_apps.create_namespaced_deployment(
                body=deployment,
                namespace=self.config.namespace
            )

            # Serviceの作成
            service = self._create_service_object()
            self._kube_client.create_namespaced_service(
                body=service,
                namespace=self.config.namespace
            )

            return {
                'success': True,
                'message': 'Kubernetesリソース作成成功'
            }
        except Exception as e:
            logger.error(f"Kubernetesリソース作成でエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _create_deployment_object(self, env_vars: List[Dict[str, str]]) -> Dict[str, Any]:
        """Deploymentオブジェクトの作成"""
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': self.config.app_name,
                'namespace': self.config.namespace
            },
            'spec': {
                'replicas': self.config.replicas,
                'selector': {
                    'matchLabels': {
                        'app': self.config.app_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': self.config.app_name
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': self.config.app_name,
                            'image': f"{self.config.docker_registry}/{self.config.app_name}:{self.config.version}",
                            'env': env_vars,
                            'resources': {
                                'limits': self.config.resource_limits
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': self.config.health_check_path,
                                    'port': 8080
                                }
                            }
                        }]
                    }
                }
            }
        }

    def _create_service_object(self) -> Dict[str, Any]:
        """Serviceオブジェクトの作成"""
        return {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': self.config.app_name,
                'namespace': self.config.namespace
            },
            'spec': {
                'selector': {
                    'app': self.config.app_name
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': 80,
                    'targetPort': 8080
                }],
                'type': 'LoadBalancer'
            }
        }

    def _load_env_vars(self) -> List[Dict[str, str]]:
        """環境変数の読み込み"""
        try:
            env_vars = []
            if os.path.exists(self.config.env_file):
                with open(self.config.env_file, 'r') as f:
                    env_data = yaml.safe_load(f)
                    for key, value in env_data.items():
                        env_vars.append({
                            'name': key,
                            'value': str(value)
                        })
            return env_vars
        except Exception as e:
            logger.error(f"環境変数読み込みでエラー: {str(e)}")
            return []

    async def _monitor_deployment(self) -> Dict[str, Any]:
        """デプロイメントの監視"""
        try:
            retries = 0
            max_retries = 30
            while retries < max_retries:
                deployment = self._kube_apps.read_namespaced_deployment_status(
                    name=self.config.app_name,
                    namespace=self.config.namespace
                )
                
                if deployment.status.available_replicas == self.config.replicas:
                    return {
                        'success': True,
                        'message': 'デプロイメント完了',
                        'replicas': deployment.status.available_replicas
                    }
                
                await asyncio.sleep(10)
                retries += 1
            
            return {
                'success': False,
                'message': 'デプロイメントタイムアウト'
            }
        except Exception as e:
            logger.error(f"デプロイメント監視でエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _create_result(self, status: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """結果オブジェクトの作成"""
        return {
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        } 