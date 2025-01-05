from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import aiohttp
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class NotificationLevel(Enum):
    """通知レベル"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class NotificationConfig:
    """通知設定"""
    slack_webhook_url: str = ""
    email_config: Dict[str, Any] = None
    notification_levels: List[str] = None
    batch_interval: int = 300  # 通知のバッチ処理間隔（秒）
    
    def __post_init__(self):
        if self.notification_levels is None:
            self.notification_levels = ["error", "critical"]
        if self.email_config is None:
            self.email_config = {}

class NotificationManager:
    """エラー通知を管理するクラス"""
    
    def __init__(self, config: NotificationConfig):
        self.config = config
        self._pending_notifications: List[Dict[str, Any]] = []
        self._notification_count: Dict[str, int] = {}

    async def notify(self, 
                    message: str, 
                    level: NotificationLevel = NotificationLevel.INFO,
                    details: Dict[str, Any] = None):
        """通知の送信"""
        try:
            if level.value not in self.config.notification_levels:
                return

            notification = {
                'message': message,
                'level': level.value,
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }

            # 重複通知の制御
            if self._is_duplicate(notification):
                self._update_notification_count(message)
                return

            # 通知の送信
            await self._send_notification(notification)
            
            # 通知カウントの更新
            self._notification_count[message] = 1

        except Exception as e:
            logger.error(f"通知送信でエラー: {str(e)}")

    async def _send_notification(self, notification: Dict[str, Any]):
        """通知の実際の送信処理"""
        try:
            if self.config.slack_webhook_url:
                await self._send_to_slack(notification)
            
            if self.config.email_config:
                await self._send_to_email(notification)

        except Exception as e:
            logger.error(f"通知送信処理でエラー: {str(e)}")

    async def _send_to_slack(self, notification: Dict[str, Any]):
        """Slackへの通知送信"""
        try:
            color_map = {
                'info': '#36a64f',
                'warning': '#ffd700',
                'error': '#ff0000',
                'critical': '#800000'
            }

            attachment = {
                'color': color_map.get(notification['level'], '#36a64f'),
                'title': f"COBOL Analyzer {notification['level'].upper()}",
                'text': notification['message'],
                'fields': [
                    {
                        'title': key,
                        'value': str(value),
                        'short': True
                    }
                    for key, value in notification['details'].items()
                ],
                'ts': int(datetime.now().timestamp())
            }

            payload = {
                'attachments': [attachment]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook_url,
                    json=payload
                ) as response:
                    if response.status != 200:
                        logger.error(f"Slack通知でエラー: {response.status}")

        except Exception as e:
            logger.error(f"Slack通知送信でエラー: {str(e)}")

    async def _send_to_email(self, notification: Dict[str, Any]):
        """メール通知の送信"""
        try:
            # メール送信の実装
            # 実際の実装ではSMTPクライアントなどを使用
            pass
        except Exception as e:
            logger.error(f"メール通知送信でエラー: {str(e)}")

    def _is_duplicate(self, notification: Dict[str, Any]) -> bool:
        """重複通知のチェック"""
        message = notification['message']
        if message in self._notification_count:
            count = self._notification_count[message]
            # 一定回数以上の同じ通知は抑制
            if count > 5:
                return True
        return False

    def _update_notification_count(self, message: str):
        """通知カウントの更新"""
        if message in self._notification_count:
            self._notification_count[message] += 1
        else:
            self._notification_count[message] = 1

    async def clear_notification_counts(self):
        """通知カウントのクリア"""
        self._notification_count.clear()

    def get_notification_summary(self) -> Dict[str, Any]:
        """通知サマリの取得"""
        return {
            'total_notifications': sum(self._notification_count.values()),
            'by_message': dict(self._notification_count),
            'timestamp': datetime.now().isoformat()
        }

    async def batch_process_notifications(self):
        """通知のバッチ処理"""
        if not self._pending_notifications:
            return

        try:
            # 通知のグループ化
            grouped = {}
            for notification in self._pending_notifications:
                level = notification['level']
                if level not in grouped:
                    grouped[level] = []
                grouped[level].append(notification)

            # レベルごとにまとめて送信
            for level, notifications in grouped.items():
                if len(notifications) == 1:
                    await self._send_notification(notifications[0])
                else:
                    # 複数の通知をまとめる
                    summary = self._create_notification_summary(level, notifications)
                    await self._send_notification(summary)

            self._pending_notifications.clear()

        except Exception as e:
            logger.error(f"通知バッチ処理でエラー: {str(e)}")

    def _create_notification_summary(self, 
                                  level: str, 
                                  notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """通知サマリの作成"""
        return {
            'message': f"{len(notifications)} {level} notifications received",
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'details': {
                'count': len(notifications),
                'messages': [n['message'] for n in notifications]
            }
        } 