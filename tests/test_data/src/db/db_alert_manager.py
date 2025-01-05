from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json
import asyncio
import aiofiles
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class Alert:
    """アラート情報を保持するデータクラス"""
    level: AlertLevel
    message: str
    source: str
    timestamp: datetime
    details: Dict[str, Any]

class AlertManager:
    """アラートの管理とメトリクスの永続化を行うクラス"""
    def __init__(self, metrics_file: str = "db_metrics.json", alert_file: str = "db_alerts.json"):
        self.metrics_file = metrics_file
        self.alert_file = alert_file
        self.alerts: List[Alert] = []
        self.alert_handlers: List[callable] = []
        self._save_task = None

    def add_alert_handler(self, handler: callable):
        """アラートハンドラを追加"""
        self.alert_handlers.append(handler)

    async def start(self):
        """メトリクス保存タスクを開始"""
        self._save_task = asyncio.create_task(self._periodic_save())

    async def stop(self):
        """メトリクス保存タスクを停止"""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass

    async def save_metrics(self, metrics: Dict[str, Any]):
        """メトリクスを保存"""
        try:
            metrics_with_timestamp = {
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics
            }
            async with aiofiles.open(self.metrics_file, 'a') as f:
                await f.write(json.dumps(metrics_with_timestamp) + '\n')
        except Exception as e:
            logger.error(f"メトリクスの保存に失敗: {str(e)}")

    async def save_alert(self, alert: Alert):
        """アラートを保存"""
        try:
            alert_dict = {
                'level': alert.level.value,
                'message': alert.message,
                'source': alert.source,
                'timestamp': alert.timestamp.isoformat(),
                'details': alert.details
            }
            async with aiofiles.open(self.alert_file, 'a') as f:
                await f.write(json.dumps(alert_dict) + '\n')
        except Exception as e:
            logger.error(f"アラートの保存に失敗: {str(e)}")

    def create_alert(self, level: AlertLevel, message: str, source: str, details: Dict[str, Any]) -> Alert:
        """新しいアラートを作成"""
        alert = Alert(
            level=level,
            message=message,
            source=source,
            timestamp=datetime.now(),
            details=details
        )
        self.alerts.append(alert)
        asyncio.create_task(self._handle_alert(alert))
        return alert

    async def _handle_alert(self, alert: Alert):
        """アラートの処理"""
        try:
            await self.save_alert(alert)
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"アラートハンドラでエラー: {str(e)}")
        except Exception as e:
            logger.error(f"アラート処理でエラー: {str(e)}")

    async def _periodic_save(self):
        """定期的なメトリクス保存"""
        while True:
            try:
                await asyncio.sleep(300)  # 5分ごと
                # メトリクスの保存は DatabaseMonitor から呼び出される
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期保存でエラー: {str(e)}")

    def get_recent_alerts(self, limit: int = 100) -> List[Alert]:
        """最近のアラートを取得"""
        return sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:limit]

    async def load_historical_data(self) -> Dict[str, Any]:
        """過去のメトリクスデータを読み込み"""
        try:
            metrics_data = []
            async with aiofiles.open(self.metrics_file, 'r') as f:
                async for line in f:
                    metrics_data.append(json.loads(line))
            return metrics_data
        except Exception as e:
            logger.error(f"履歴データの読み込みに失敗: {str(e)}")
            return [] 