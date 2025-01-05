from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from collections import deque
import statistics
from .db_alert_manager import AlertManager, AlertLevel, Alert

logger = logging.getLogger(__name__)

@dataclass
class ConnectionMetrics:
    """接続メトリクスを保持するデータクラス"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    waiting_connections: int = 0
    response_times: deque = deque(maxlen=100)  # 直近100件の応答時間
    errors: int = 0
    last_error_time: datetime = None

    def add_response_time(self, time_ms: float):
        self.response_times.append(time_ms)

    @property
    def average_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def max_response_time(self) -> float:
        return max(self.response_times) if self.response_times else 0

class DatabaseMonitor:
    """データベース接続の監視を行うクラス"""
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.pg_metrics = ConnectionMetrics()
        self.mongo_metrics = ConnectionMetrics()
        self.is_monitoring = False
        self._monitor_task = None
        self.alert_manager = AlertManager()

    async def start_monitoring(self):
        """監視を開始"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            await self.alert_manager.start()
            logger.info("データベース監視を開始しました")

    async def stop_monitoring(self):
        """監視を停止"""
        if self.is_monitoring:
            self.is_monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            await self.alert_manager.stop()
            logger.info("データベース監視を停止しました")

    async def _monitoring_loop(self):
        """定期的な監視を実行"""
        while self.is_monitoring:
            try:
                await self._check_connections()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"監視中にエラーが発生しました: {str(e)}")

    async def _check_connections(self):
        """接続状態をチェック"""
        metrics = self.get_metrics()
        await self.alert_manager.save_metrics(metrics)

        # 接続数のチェック
        for db_type, db_metrics in metrics.items():
            if db_metrics['active_connections'] > db_metrics['total_connections'] * 0.8:
                self.alert_manager.create_alert(
                    level=AlertLevel.WARNING,
                    message=f"接続プールの使用率が高い: {db_type}",
                    source=db_type,
                    details=db_metrics
                )

    def record_operation(self, db_type: str, operation: str, duration_ms: float, error: Exception = None):
        """操作の記録"""
        metrics = self.pg_metrics if db_type == 'postgres' else self.mongo_metrics
        metrics.add_response_time(duration_ms)
        
        # レスポンスタイムのアラートチェック
        if duration_ms > 1000:  # 1秒以上
            self.alert_manager.create_alert(
                level=AlertLevel.WARNING,
                message=f"遅いレスポンスタイム: {duration_ms}ms",
                source=f"{db_type}.{operation}",
                details={'duration_ms': duration_ms}
            )

        # エラーのアラート
        if error:
            self.alert_manager.create_alert(
                level=AlertLevel.ERROR,
                message=str(error),
                source=f"{db_type}.{operation}",
                details={'error_type': type(error).__name__}
            )

    def get_metrics(self) -> Dict[str, Any]:
        """現在のメトリクスを取得"""
        return {
            'postgres': {
                'total_connections': self.pg_metrics.total_connections,
                'active_connections': self.pg_metrics.active_connections,
                'idle_connections': self.pg_metrics.idle_connections,
                'waiting_connections': self.pg_metrics.waiting_connections,
                'average_response_time': self.pg_metrics.average_response_time,
                'max_response_time': self.pg_metrics.max_response_time,
                'errors': self.pg_metrics.errors,
                'last_error_time': self.pg_metrics.last_error_time,
            },
            'mongodb': {
                'total_connections': self.mongo_metrics.total_connections,
                'active_connections': self.mongo_metrics.active_connections,
                'idle_connections': self.mongo_metrics.idle_connections,
                'waiting_connections': self.mongo_metrics.waiting_connections,
                'average_response_time': self.mongo_metrics.average_response_time,
                'max_response_time': self.mongo_metrics.max_response_time,
                'errors': self.mongo_metrics.errors,
                'last_error_time': self.mongo_metrics.last_error_time,
            }
        }

    def check_health(self) -> Dict[str, bool]:
        """ヘルスチェックの実行"""
        return {
            'postgres': self._check_postgres_health(),
            'mongodb': self._check_mongodb_health()
        }

    def _check_postgres_health(self) -> bool:
        """PostgreSQLの健全性チェック"""
        if self.pg_metrics.last_error_time:
            # 最後のエラーから5分以内は異常とみなす
            if datetime.now() - self.pg_metrics.last_error_time < timedelta(minutes=5):
                return False
        return True

    def _check_mongodb_health(self) -> bool:
        """MongoDBの健全性チェック"""
        if self.mongo_metrics.last_error_time:
            # 最後のエラーから5分以内は異常とみなす
            if datetime.now() - self.mongo_metrics.last_error_time < timedelta(minutes=5):
                return False
        return True 