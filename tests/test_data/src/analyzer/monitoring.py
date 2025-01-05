from typing import Dict, Any, List, Optional
import logging
import psutil
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class MonitoringConfig:
    """監視設定"""
    metrics_interval: int = 60  # メトリクス収集間隔（秒）
    history_size: int = 1440    # 履歴保持サイズ（24時間分）
    alert_thresholds: Dict[str, float] = None
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'cpu_usage': 80.0,      # CPU使用率閾値（%）
                'memory_usage': 85.0,    # メモリ使用率閾値（%）
                'disk_usage': 90.0,      # ディスク使用率閾値（%）
                'analysis_time': 300.0   # 解析時間閾値（秒）
            }

class SystemMonitor:
    """システム監視を管理するクラス"""
    
    def __init__(self, config: MonitoringConfig, notification_manager):
        self.config = config
        self.notification_manager = notification_manager
        self._metrics_history: Dict[str, deque] = {
            'cpu_usage': deque(maxlen=config.history_size),
            'memory_usage': deque(maxlen=config.history_size),
            'disk_usage': deque(maxlen=config.history_size),
            'analysis_times': deque(maxlen=config.history_size),
            'error_counts': deque(maxlen=config.history_size)
        }
        self._current_metrics: Dict[str, Any] = {}
        self._is_monitoring = False

    async def start_monitoring(self):
        """監視の開始"""
        self._is_monitoring = True
        try:
            while self._is_monitoring:
                await self._collect_system_metrics()
                await self._check_thresholds()
                await asyncio.sleep(self.config.metrics_interval)
        except Exception as e:
            logger.error(f"システム監視でエラー: {str(e)}")
            self._is_monitoring = False

    async def stop_monitoring(self):
        """監視の停止"""
        self._is_monitoring = False

    async def _collect_system_metrics(self):
        """システムメトリクスの収集"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self._metrics_history['cpu_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': cpu_percent
            })

            # メモリ使用率
            memory = psutil.virtual_memory()
            self._metrics_history['memory_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': memory.percent
            })

            # ディスク使用率
            disk = psutil.disk_usage('/')
            self._metrics_history['disk_usage'].append({
                'timestamp': datetime.now().isoformat(),
                'value': disk.percent
            })

            self._current_metrics = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'disk_usage': disk.percent,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"メトリクス収集でエラー: {str(e)}")

    async def _check_thresholds(self):
        """閾値チェック"""
        try:
            for metric, value in self._current_metrics.items():
                if metric in self.config.alert_thresholds:
                    threshold = self.config.alert_thresholds[metric]
                    if value > threshold:
                        await self._send_alert(metric, value, threshold)
        except Exception as e:
            logger.error(f"閾値チェックでエラー: {str(e)}")

    async def _send_alert(self, metric: str, value: float, threshold: float):
        """アラートの送信"""
        try:
            message = f"システムメトリクス警告: {metric}"
            details = {
                'metric': metric,
                'current_value': value,
                'threshold': threshold,
                'timestamp': datetime.now().isoformat()
            }
            
            await self.notification_manager.notify(
                message=message,
                level="warning",
                details=details
            )
        except Exception as e:
            logger.error(f"アラート送信でエラー: {str(e)}")

    def record_analysis_time(self, source_id: str, duration: float):
        """解析時間の記録"""
        try:
            self._metrics_history['analysis_times'].append({
                'timestamp': datetime.now().isoformat(),
                'source_id': source_id,
                'duration': duration
            })

            # 解析時間の閾値チェック
            if duration > self.config.alert_thresholds['analysis_time']:
                asyncio.create_task(self._send_alert(
                    'analysis_time',
                    duration,
                    self.config.alert_thresholds['analysis_time']
                ))
        except Exception as e:
            logger.error(f"解析時間記録でエラー: {str(e)}")

    def record_error(self, error_type: str, details: Dict[str, Any]):
        """エラーの記録"""
        try:
            self._metrics_history['error_counts'].append({
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'details': details
            })
        except Exception as e:
            logger.error(f"エラー記録でエラー: {str(e)}")

    def get_metrics_summary(self) -> Dict[str, Any]:
        """メトリクスサマリの取得"""
        try:
            current_metrics = dict(self._current_metrics)
            
            # 平均値の計算
            averages = {}
            for metric, history in self._metrics_history.items():
                if history and metric != 'error_counts':
                    if metric == 'analysis_times':
                        values = [item['duration'] for item in history]
                    else:
                        values = [item['value'] for item in history]
                    averages[f'{metric}_avg'] = sum(values) / len(values)

            # エラー統計
            error_stats = {}
            error_history = self._metrics_history['error_counts']
            if error_history:
                error_types = {}
                for error in error_history:
                    error_type = error['error_type']
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                error_stats['error_counts'] = error_types

            return {
                'current': current_metrics,
                'averages': averages,
                'errors': error_stats,
                'generated_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"メトリクスサマリ生成でエラー: {str(e)}")
            return {}

    def get_historical_metrics(self, 
                             metric_name: str, 
                             time_range: str = '1h') -> List[Dict[str, Any]]:
        """履歴メトリクスの取得"""
        try:
            if metric_name not in self._metrics_history:
                return []

            history = list(self._metrics_history[metric_name])
            if not history:
                return []

            # 時間範囲でフィルタリング
            end_time = datetime.now()
            start_time = self._calculate_start_time(end_time, time_range)

            filtered_metrics = [
                metric for metric in history
                if datetime.fromisoformat(metric['timestamp']) >= start_time
            ]

            return filtered_metrics
        except Exception as e:
            logger.error(f"履歴メトリクス取得でエラー: {str(e)}")
            return []

    def _calculate_start_time(self, end_time: datetime, time_range: str) -> datetime:
        """開始時刻の計算"""
        range_map = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '12h': timedelta(hours=12),
            '24h': timedelta(days=1),
            '7d': timedelta(days=7)
        }
        return end_time - range_map.get(time_range, range_map['1h']) 