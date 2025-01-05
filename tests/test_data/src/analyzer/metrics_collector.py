from typing import Dict, Any, List, Optional
import logging
import psutil
import os
import platform
from datetime import datetime
from dataclasses import dataclass
import asyncio
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class CollectorConfig:
    """メトリクス収集の設定"""
    collect_interval: int = 30    # 収集間隔（秒）
    process_name: str = "cobol_analyzer"
    detailed_cpu: bool = True     # 詳細なCPU情報を収集
    detailed_memory: bool = True  # 詳細なメモリ情報を収集
    io_monitoring: bool = True    # IO監視を有効化
    network_monitoring: bool = True  # ネットワーク監視を有効化

class MetricsCollector:
    """詳細なシステムメトリクスを収集するクラス"""
    
    def __init__(self, config: CollectorConfig):
        self.config = config
        self._process = self._find_process()
        self._metrics: Dict[str, Any] = defaultdict(list)
        self._is_collecting = False

    def _find_process(self) -> Optional[psutil.Process]:
        """対象プロセスの特定"""
        try:
            for proc in psutil.process_iter(['name', 'cmdline']):
                if self.config.process_name in proc.info['name']:
                    return proc
            return None
        except Exception as e:
            logger.error(f"プロセス特定でエラー: {str(e)}")
            return None

    async def start_collection(self):
        """メトリクス収集の開始"""
        self._is_collecting = True
        try:
            while self._is_collecting:
                await self._collect_all_metrics()
                await asyncio.sleep(self.config.collect_interval)
        except Exception as e:
            logger.error(f"メトリクス収集でエラー: {str(e)}")
            self._is_collecting = False

    async def stop_collection(self):
        """メトリクス収集の停止"""
        self._is_collecting = False

    async def _collect_all_metrics(self):
        """全メトリクスの収集"""
        try:
            timestamp = datetime.now().isoformat()
            
            # システム全体のメトリクス
            system_metrics = await self._collect_system_metrics()
            
            # プロセス固有のメトリクス
            process_metrics = await self._collect_process_metrics()
            
            # 詳細メトリクス
            detailed_metrics = {}
            if self.config.detailed_cpu:
                detailed_metrics['cpu'] = await self._collect_detailed_cpu()
            if self.config.detailed_memory:
                detailed_metrics['memory'] = await self._collect_detailed_memory()
            if self.config.io_monitoring:
                detailed_metrics['io'] = await self._collect_io_metrics()
            if self.config.network_monitoring:
                detailed_metrics['network'] = await self._collect_network_metrics()

            # メトリクスの保存
            metrics = {
                'timestamp': timestamp,
                'system': system_metrics,
                'process': process_metrics,
                'detailed': detailed_metrics
            }
            
            self._store_metrics(metrics)
            
        except Exception as e:
            logger.error(f"メトリクス収集でエラー: {str(e)}")

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """システム全体のメトリクス収集"""
        try:
            return {
                'cpu': {
                    'percent': psutil.cpu_percent(interval=1),
                    'count': psutil.cpu_count(),
                    'frequency': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
                },
                'memory': psutil.virtual_memory()._asdict(),
                'swap': psutil.swap_memory()._asdict(),
                'disk': {
                    'usage': psutil.disk_usage('/')._asdict(),
                    'io_counters': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
                },
                'network': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {}
            }
        except Exception as e:
            logger.error(f"システムメトリクス収集でエラー: {str(e)}")
            return {}

    async def _collect_process_metrics(self) -> Dict[str, Any]:
        """プロセス固有のメトリクス収集"""
        try:
            if not self._process:
                return {}

            return {
                'cpu_percent': self._process.cpu_percent(),
                'memory_percent': self._process.memory_percent(),
                'memory_info': self._process.memory_info()._asdict(),
                'num_threads': self._process.num_threads(),
                'io_counters': self._process.io_counters()._asdict() if hasattr(self._process, 'io_counters') else {},
                'status': self._process.status()
            }
        except Exception as e:
            logger.error(f"プロセスメトリクス収集でエラー: {str(e)}")
            return {}

    async def _collect_detailed_cpu(self) -> Dict[str, Any]:
        """詳細なCPU情報の収集"""
        try:
            return {
                'times': psutil.cpu_times()._asdict(),
                'times_percent': psutil.cpu_times_percent()._asdict(),
                'stats': psutil.cpu_stats()._asdict(),
                'load_avg': psutil.getloadavg()
            }
        except Exception as e:
            logger.error(f"CPU詳細情報収集でエラー: {str(e)}")
            return {}

    async def _collect_detailed_memory(self) -> Dict[str, Any]:
        """詳細なメモリ情報の収集"""
        try:
            return {
                'virtual': psutil.virtual_memory()._asdict(),
                'swap': psutil.swap_memory()._asdict(),
                'process_memory': self._process.memory_full_info()._asdict() if self._process else {}
            }
        except Exception as e:
            logger.error(f"メモリ詳細情報収集でエラー: {str(e)}")
            return {}

    async def _collect_io_metrics(self) -> Dict[str, Any]:
        """IO情報の収集"""
        try:
            return {
                'disk': {
                    'partitions': [p._asdict() for p in psutil.disk_partitions()],
                    'io_counters': psutil.disk_io_counters(perdisk=True)
                },
                'process_io': self._process.io_counters()._asdict() if self._process and hasattr(self._process, 'io_counters') else {}
            }
        except Exception as e:
            logger.error(f"IOメトリクス収集でエラー: {str(e)}")
            return {}

    async def _collect_network_metrics(self) -> Dict[str, Any]:
        """ネットワーク情報の収集"""
        try:
            return {
                'io_counters': psutil.net_io_counters(pernic=True),
                'connections': [conn._asdict() for conn in psutil.net_connections()],
                'interfaces': psutil.net_if_stats()
            }
        except Exception as e:
            logger.error(f"ネットワークメトリクス収集でエラー: {str(e)}")
            return {}

    def _store_metrics(self, metrics: Dict[str, Any]):
        """メトリクスの保存"""
        try:
            for category, data in metrics.items():
                if category != 'timestamp':
                    self._metrics[category].append({
                        'timestamp': metrics['timestamp'],
                        'data': data
                    })
                    
                    # 履歴サイズの制限
                    if len(self._metrics[category]) > 1000:  # 最大1000件保持
                        self._metrics[category].pop(0)
        except Exception as e:
            logger.error(f"メトリクス保存でエラー: {str(e)}")

    def get_latest_metrics(self) -> Dict[str, Any]:
        """最新のメトリクスを取得"""
        try:
            latest = {}
            for category, data in self._metrics.items():
                if data:
                    latest[category] = data[-1]
            return latest
        except Exception as e:
            logger.error(f"最新メトリクス取得でエラー: {str(e)}")
            return {}

    def get_historical_metrics(self, 
                             category: str, 
                             start_time: datetime = None) -> List[Dict[str, Any]]:
        """履歴メトリクスの取得"""
        try:
            if category not in self._metrics:
                return []

            if not start_time:
                return self._metrics[category]

            return [
                metric for metric in self._metrics[category]
                if datetime.fromisoformat(metric['timestamp']) >= start_time
            ]
        except Exception as e:
            logger.error(f"履歴メトリクス取得でエラー: {str(e)}")
            return [] 