from typing import Dict, Any, List, Optional
import logging
import asyncio
import pytest
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import websockets
import psutil
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class TestConfig:
    """テスト設定"""
    test_host: str = "localhost"
    test_port: int = 8766
    timeout: float = 5.0
    test_data_size: int = 100
    parallel_clients: int = 10
    metrics_interval: float = 0.1

class AnalyzerTestSuite:
    """テストスイートを管理するクラス"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self._test_data: Dict[str, Any] = {}
        self._test_results: List[Dict[str, Any]] = []

    async def run_all_tests(self) -> Dict[str, Any]:
        """全テストの実行"""
        try:
            results = {
                'unit_tests': await self._run_unit_tests(),
                'integration_tests': await self._run_integration_tests(),
                'performance_tests': await self._run_performance_tests(),
                'stress_tests': await self._run_stress_tests()
            }
            
            # テスト結果の集計
            summary = self._generate_test_summary(results)
            
            return {
                'results': results,
                'summary': summary,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"テスト実行でエラー: {str(e)}")
            return {}

    async def _run_unit_tests(self) -> Dict[str, Any]:
        """ユニットテストの実行"""
        try:
            test_cases = [
                self._test_metrics_collection,
                self._test_data_processing,
                self._test_cache_management,
                self._test_error_handling
            ]
            
            results = []
            for test_case in test_cases:
                result = await test_case()
                results.append(result)
            
            return {
                'passed': sum(1 for r in results if r['status'] == 'passed'),
                'failed': sum(1 for r in results if r['status'] == 'failed'),
                'details': results
            }
        except Exception as e:
            logger.error(f"ユニットテストでエラー: {str(e)}")
            return {}

    async def _run_integration_tests(self) -> Dict[str, Any]:
        """インテグレーションテストの実行"""
        try:
            test_cases = [
                self._test_websocket_connection,
                self._test_data_flow,
                self._test_system_integration,
                self._test_client_communication
            ]
            
            results = []
            for test_case in test_cases:
                result = await test_case()
                results.append(result)
            
            return {
                'passed': sum(1 for r in results if r['status'] == 'passed'),
                'failed': sum(1 for r in results if r['status'] == 'failed'),
                'details': results
            }
        except Exception as e:
            logger.error(f"インテグレーションテストでエラー: {str(e)}")
            return {}

    async def _run_performance_tests(self) -> Dict[str, Any]:
        """パフォーマンステストの実行"""
        try:
            metrics = {
                'response_times': [],
                'throughput': [],
                'memory_usage': [],
                'cpu_usage': []
            }
            
            # 負荷テスト
            async with websockets.connect(
                f'ws://{self.config.test_host}:{self.config.test_port}'
            ) as websocket:
                start_time = datetime.now()
                
                # テストデータの送信
                for _ in range(self.config.test_data_size):
                    message = self._generate_test_message()
                    send_time = datetime.now()
                    
                    await websocket.send(json.dumps(message))
                    response = await websocket.recv()
                    
                    # レスポンス時間の記録
                    response_time = (datetime.now() - send_time).total_seconds()
                    metrics['response_times'].append(response_time)
                    
                    # システムメトリクスの収集
                    metrics['memory_usage'].append(psutil.Process().memory_percent())
                    metrics['cpu_usage'].append(psutil.cpu_percent())
                    
                    await asyncio.sleep(self.config.metrics_interval)
                
                # スループットの計算
                total_time = (datetime.now() - start_time).total_seconds()
                throughput = self.config.test_data_size / total_time
                metrics['throughput'] = throughput
            
            return {
                'metrics': metrics,
                'statistics': self._calculate_performance_stats(metrics)
            }
        except Exception as e:
            logger.error(f"パフォーマンステストでエラー: {str(e)}")
            return {}

    async def _run_stress_tests(self) -> Dict[str, Any]:
        """ストレステストの実行"""
        try:
            # 並行クライアントの作成
            clients = [
                self._simulate_client(i)
                for i in range(self.config.parallel_clients)
            ]
            
            # 全クライアントの実行
            results = await asyncio.gather(*clients, return_exceptions=True)
            
            # 結果の分析
            success_count = sum(1 for r in results if isinstance(r, dict))
            error_count = sum(1 for r in results if isinstance(r, Exception))
            
            return {
                'total_clients': self.config.parallel_clients,
                'successful': success_count,
                'failed': error_count,
                'error_rate': error_count / self.config.parallel_clients
            }
        except Exception as e:
            logger.error(f"ストレステストでエラー: {str(e)}")
            return {}

    async def _simulate_client(self, client_id: int) -> Dict[str, Any]:
        """クライアントのシミュレーション"""
        try:
            async with websockets.connect(
                f'ws://{self.config.test_host}:{self.config.test_port}'
            ) as websocket:
                metrics = {
                    'messages_sent': 0,
                    'messages_received': 0,
                    'errors': 0
                }
                
                for _ in range(self.config.test_data_size):
                    try:
                        message = self._generate_test_message()
                        await websocket.send(json.dumps(message))
                        metrics['messages_sent'] += 1
                        
                        response = await websocket.recv()
                        metrics['messages_received'] += 1
                        
                    except Exception as e:
                        metrics['errors'] += 1
                        logger.error(f"クライアント {client_id} でエラー: {str(e)}")
                
                return {
                    'client_id': client_id,
                    'metrics': metrics
                }
        except Exception as e:
            logger.error(f"クライアントシミュレーションでエラー: {str(e)}")
            raise

    def _generate_test_message(self) -> Dict[str, Any]:
        """テストメッセージの生成"""
        return {
            'type': 'test',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'value': np.random.random(),
                'metric': 'test_metric'
            }
        }

    def _calculate_performance_stats(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンス統計の計算"""
        try:
            stats = {}
            
            for metric, values in metrics.items():
                if isinstance(values, list) and values:
                    stats[metric] = {
                        'min': min(values),
                        'max': max(values),
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'p95': np.percentile(values, 95),
                        'p99': np.percentile(values, 99)
                    }
                elif isinstance(values, (int, float)):
                    stats[metric] = values
            
            return stats
        except Exception as e:
            logger.error(f"統計計算でエラー: {str(e)}")
            return {}

    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """テスト結果サマリの生成"""
        try:
            total_tests = 0
            total_passed = 0
            total_failed = 0
            
            for test_type, result in results.items():
                if isinstance(result, dict):
                    passed = result.get('passed', 0)
                    failed = result.get('failed', 0)
                    total_tests += passed + failed
                    total_passed += passed
                    total_failed += failed
            
            return {
                'total_tests': total_tests,
                'total_passed': total_passed,
                'total_failed': total_failed,
                'success_rate': total_passed / total_tests if total_tests > 0 else 0
            }
        except Exception as e:
            logger.error(f"サマリ生成でエラー: {str(e)}")
            return {} 