from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from dataclasses import dataclass
import asyncio
import docker
import kubernetes
from kubernetes import client, config
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class RollbackConfig:
    """ロールバック設定"""
    app_name: str = "cobol-analyzer"
    namespace: str = "default"
    backup_limit: int = 5
    health_check_path: str = "/health"
    health_check_timeout: int = 300
    retry_limit: int = 3
    backup_dir: str = "backups"

class RollbackManager:
    """ロールバック処理を管理するクラス"""
    
    def __init__(self, config: RollbackConfig):
        self.config = config
        self._docker_client = docker.from_env()
        self._setup_kubernetes()
        self._deployment_history: List[Dict[str, Any]] = []
        self._ensure_backup_dir()

    def _setup_kubernetes(self):
        """Kubernetes設定の初期化"""
        try:
            config.load_kube_config()
            self._kube_client = client.CoreV1Api()
            self._kube_apps = client.AppsV1Api()
        except Exception as e:
            logger.error(f"Kubernetes設定でエラー: {str(e)}")

    def _ensure_backup_dir(self):
        """バックアップディレクトリの作成"""
        try:
            os.makedirs(self.config.backup_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"バックアップディレクトリ作成でエラー: {str(e)}")

    async def create_deployment_backup(self, version: str) -> Dict[str, Any]:
        """デプロイメントのバックアップ作成"""
        try:
            # 現在のデプロイメント状態の取得
            deployment = self._kube_apps.read_namespaced_deployment(
                name=self.config.app_name,
                namespace=self.config.namespace
            )

            # バックアップ情報の作成
            backup_info = {
                'timestamp': datetime.now().isoformat(),
                'version': version,
                'deployment_spec': deployment.spec.to_dict(),
                'image': deployment.spec.template.spec.containers[0].image
            }

            # バックアップの保存
            self._save_backup(backup_info)
            self._deployment_history.append(backup_info)

            # 履歴の制限
            self._limit_backup_history()

            return {
                'success': True,
                'message': 'バックアップ作成成功',
                'backup_info': backup_info
            }

        except Exception as e:
            logger.error(f"バックアップ作成でエラー: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def rollback(self, version: str = None) -> Dict[str, Any]:
        """ロールバックの実行"""
        try:
            # バックアップの取得
            backup = self._get_backup(version)
            if not backup:
                return {
                    'success': False,
                    'message': 'バックアップが見つかりません'
                }

            # ロールバックの実行
            result = await self._execute_rollback(backup)
            if not result['success']:
                return result

            # ヘルスチェック
            health_status = await self._check_deployment_health()
            if not health_status['success']:
                # 自動リカバリの試行
                recovery_result = await self._attempt_recovery()
                if not recovery_result['success']:
                    return recovery_result

            return {
                'success': True,
                'message': 'ロールバック成功',
                'version': backup['version']
            }

        except Exception as e:
            logger.error(f"ロールバック実行でエラー: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _execute_rollback(self, backup: Dict[str, Any]) -> Dict[str, Any]:
        """ロールバックの実行処理"""
        try:
            # デプロイメントの更新
            deployment_spec = backup['deployment_spec']
            self._kube_apps.patch_namespaced_deployment(
                name=self.config.app_name,
                namespace=self.config.namespace,
                body={'spec': deployment_spec}
            )

            # ロールバックの完了を待機
            await self._wait_for_rollback_completion()

            return {
                'success': True,
                'message': 'ロールバック実行成功'
            }

        except Exception as e:
            logger.error(f"ロールバック実行処理でエラー: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _check_deployment_health(self) -> Dict[str, Any]:
        """デプロイメントのヘルスチェック"""
        try:
            # Podの状態確認
            pods = self._kube_client.list_namespaced_pod(
                namespace=self.config.namespace,
                label_selector=f"app={self.config.app_name}"
            )

            # 全Podの準備状態を確認
            all_ready = all(
                pod.status.phase == 'Running' and
                all(cont.ready for cont in pod.status.container_statuses)
                for pod in pods.items
            )

            if not all_ready:
                return {
                    'success': False,
                    'message': 'Podが正常に起動していません'
                }

            # アプリケーションのヘルスチェック
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:8080{self.config.health_check_path}"
                ) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'message': 'ヘルスチェックに失敗しました'
                        }

            return {
                'success': True,
                'message': 'ヘルスチェック成功'
            }

        except Exception as e:
            logger.error(f"ヘルスチェックでエラー: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _attempt_recovery(self) -> Dict[str, Any]:
        """リカバリの試行"""
        try:
            for i in range(self.config.retry_limit):
                # デプロイメントの再起動
                self._kube_apps.delete_collection_namespaced_pod(
                    namespace=self.config.namespace,
                    label_selector=f"app={self.config.app_name}"
                )

                # 状態の確認
                await asyncio.sleep(10)
                health_status = await self._check_deployment_health()
                if health_status['success']:
                    return {
                        'success': True,
                        'message': 'リカバリ成功'
                    }

            return {
                'success': False,
                'message': 'リカバリ失敗'
            }

        except Exception as e:
            logger.error(f"リカバリ試行でエラー: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _save_backup(self, backup_info: Dict[str, Any]):
        """バックアップの保存"""
        try:
            backup_path = os.path.join(
                self.config.backup_dir,
                f"backup_{backup_info['version']}_{backup_info['timestamp']}.json"
            )
            with open(backup_path, 'w') as f:
                json.dump(backup_info, f, indent=2)
        except Exception as e:
            logger.error(f"バックアップ保存でエラー: {str(e)}")

    def _get_backup(self, version: str = None) -> Optional[Dict[str, Any]]:
        """バックアップの取得"""
        try:
            if version:
                # 指定バージョンのバックアップを検索
                for backup in reversed(self._deployment_history):
                    if backup['version'] == version:
                        return backup
            else:
                # 最新のバックアップを返す
                return self._deployment_history[-1] if self._deployment_history else None

            return None
        except Exception as e:
            logger.error(f"バックアップ取得でエラー: {str(e)}")
            return None

    def _limit_backup_history(self):
        """バックアップ履歴の制限"""
        try:
            while len(self._deployment_history) > self.config.backup_limit:
                oldest_backup = self._deployment_history.pop(0)
                # 関連ファイルの削除
                backup_files = os.listdir(self.config.backup_dir)
                for file in backup_files:
                    if oldest_backup['version'] in file:
                        os.remove(os.path.join(self.config.backup_dir, file))
        except Exception as e:
            logger.error(f"バックアップ履歴制限でエラー: {str(e)}")

    async def _wait_for_rollback_completion(self):
        """ロールバック完了の待機"""
        try:
            timeout = self.config.health_check_timeout
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < timeout:
                deployment = self._kube_apps.read_namespaced_deployment_status(
                    name=self.config.app_name,
                    namespace=self.config.namespace
                )

                if deployment.status.updated_replicas == deployment.spec.replicas:
                    return

                await asyncio.sleep(5)

            raise TimeoutError("ロールバック完了待機がタイムアウトしました")

        except Exception as e:
            logger.error(f"ロールバック完了待機でエラー: {str(e)}")
            raise 