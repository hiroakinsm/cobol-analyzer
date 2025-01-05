from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from dataclasses import dataclass
import subprocess
import os
import yaml
import json
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CIConfig:
    """CI/CD設定"""
    repo_url: str = ""
    branch: str = "main"
    build_dir: str = "build"
    test_dir: str = "tests"
    deploy_dir: str = "deploy"
    docker_file: str = "Dockerfile"
    requirements_file: str = "requirements.txt"
    env_file: str = ".env"

class CICDManager:
    """CI/CD処理を管理するクラス"""
    
    def __init__(self, config: CIConfig):
        self.config = config
        self._build_status: Dict[str, Any] = {}
        self._test_results: Dict[str, Any] = {}
        self._deployment_status: Dict[str, Any] = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """必要なディレクトリの作成"""
        try:
            for dir_path in [self.config.build_dir, 
                           self.config.test_dir, 
                           self.config.deploy_dir]:
                os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            logger.error(f"ディレクトリ作成でエラー: {str(e)}")

    async def run_pipeline(self) -> Dict[str, Any]:
        """CIパイプラインの実行"""
        try:
            # ソース取得
            await self._fetch_source()
            
            # ビルド
            build_result = await self._build()
            if not build_result.get('success'):
                return self._create_pipeline_result('build_failed')
            
            # テスト
            test_result = await self._run_tests()
            if not test_result.get('success'):
                return self._create_pipeline_result('test_failed')
            
            # デプロイ
            deploy_result = await self._deploy()
            if not deploy_result.get('success'):
                return self._create_pipeline_result('deploy_failed')
            
            return self._create_pipeline_result('success')
            
        except Exception as e:
            logger.error(f"パイプライン実行でエラー: {str(e)}")
            return self._create_pipeline_result('error')

    async def _fetch_source(self) -> Dict[str, Any]:
        """ソースコードの取得"""
        try:
            if not self.config.repo_url:
                return {'success': True, 'message': 'ローカルソースを使用'}

            # Gitコマンドの実行
            process = await asyncio.create_subprocess_exec(
                'git', 'clone', '-b', self.config.branch, self.config.repo_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'message': 'ソース取得成功',
                    'output': stdout.decode()
                }
            else:
                return {
                    'success': False,
                    'message': 'ソース取得失敗',
                    'error': stderr.decode()
                }
                
        except Exception as e:
            logger.error(f"ソース取得でエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _build(self) -> Dict[str, Any]:
        """ビルドプロセスの実行"""
        try:
            # 依存関係のインストール
            if os.path.exists(self.config.requirements_file):
                process = await asyncio.create_subprocess_exec(
                    'pip', 'install', '-r', self.config.requirements_file,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        'success': False,
                        'message': '依存関係インストール失敗',
                        'error': stderr.decode()
                    }

            # Dockerビルド
            if os.path.exists(self.config.docker_file):
                process = await asyncio.create_subprocess_exec(
                    'docker', 'build', '-t', 'cobol-analyzer:latest', '.',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    return {
                        'success': False,
                        'message': 'Dockerビルド失敗',
                        'error': stderr.decode()
                    }

            return {
                'success': True,
                'message': 'ビルド成功'
            }
            
        except Exception as e:
            logger.error(f"ビルドでエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _run_tests(self) -> Dict[str, Any]:
        """テストの実行"""
        try:
            # pytestの実行
            process = await asyncio.create_subprocess_exec(
                'pytest', self.config.test_dir, '--junitxml=test-results.xml',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self._test_results = self._parse_test_results('test-results.xml')
                return {
                    'success': True,
                    'message': 'テスト成功',
                    'results': self._test_results
                }
            else:
                return {
                    'success': False,
                    'message': 'テスト失敗',
                    'error': stderr.decode(),
                    'output': stdout.decode()
                }
                
        except Exception as e:
            logger.error(f"テスト実行でエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _deploy(self) -> Dict[str, Any]:
        """デプロイの実行"""
        try:
            # 環境変数の読み込み
            if os.path.exists(self.config.env_file):
                with open(self.config.env_file, 'r') as f:
                    env_vars = yaml.safe_load(f)
                os.environ.update(env_vars)

            # Dockerコンテナの起動
            process = await asyncio.create_subprocess_exec(
                'docker', 'run', '-d',
                '--name', 'cobol-analyzer',
                '-p', '8080:8080',
                'cobol-analyzer:latest',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    'success': True,
                    'message': 'デプロイ成功',
                    'container_id': stdout.decode().strip()
                }
            else:
                return {
                    'success': False,
                    'message': 'デプロイ失敗',
                    'error': stderr.decode()
                }
                
        except Exception as e:
            logger.error(f"デプロイでエラー: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _parse_test_results(self, result_file: str) -> Dict[str, Any]:
        """テスト結果の解析"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(result_file)
            root = tree.getroot()
            
            return {
                'total': int(root.attrib['tests']),
                'failures': int(root.attrib['failures']),
                'errors': int(root.attrib['errors']),
                'skipped': int(root.attrib['skipped']),
                'time': float(root.attrib['time']),
                'timestamp': root.attrib['timestamp']
            }
        except Exception as e:
            logger.error(f"テスト結果解析でエラー: {str(e)}")
            return {}

    def _create_pipeline_result(self, status: str) -> Dict[str, Any]:
        """パイプライン結果の生成"""
        return {
            'status': status,
            'build_status': self._build_status,
            'test_results': self._test_results,
            'deployment_status': self._deployment_status,
            'timestamp': datetime.now().isoformat()
        } 