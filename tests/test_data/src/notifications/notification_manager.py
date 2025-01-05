from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict

class ErrorSeverity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class NotificationManager:
    def __init__(self, error_threshold=3, notification_interval=3600):
        self.error_threshold = error_threshold
        self.notification_interval = notification_interval
        self.error_counts = defaultdict(int)
        self.last_notification = defaultdict(datetime.min)
        self.logger = logging.getLogger(__name__)

    def should_notify(self, error_type, severity):
        current_time = datetime.now()
        error_key = f"{error_type}_{severity.value}"
        
        # エラーカウントの更新
        self.error_counts[error_key] += 1
        
        # 最後の通知からの経過時間をチェック
        time_since_last = current_time - self.last_notification[error_key]
        
        # 重要度に基づく通知閾値の調整
        threshold_multiplier = {
            ErrorSeverity.LOW: 1.0,
            ErrorSeverity.MEDIUM: 0.75,
            ErrorSeverity.HIGH: 0.5,
            ErrorSeverity.CRITICAL: 0.0  # 即時通知
        }
        
        adjusted_threshold = max(1, int(self.error_threshold * threshold_multiplier[severity]))
        
        if (self.error_counts[error_key] >= adjusted_threshold and 
            time_since_last.total_seconds() >= self.notification_interval):
            self.last_notification[error_key] = current_time
            self.error_counts[error_key] = 0
            return True
            
        return False

    def get_notification_template(self, severity):
        templates = {
            ErrorSeverity.LOW: {
                'subject_prefix': '[INFO]',
                'template': 'notification_templates/low_severity.txt'
            },
            ErrorSeverity.MEDIUM: {
                'subject_prefix': '[WARNING]',
                'template': 'notification_templates/medium_severity.txt'
            },
            ErrorSeverity.HIGH: {
                'subject_prefix': '[ERROR]',
                'template': 'notification_templates/high_severity.txt'
            },
            ErrorSeverity.CRITICAL: {
                'subject_prefix': '[CRITICAL]',
                'template': 'notification_templates/critical_severity.txt'
            }
        }
        return templates.get(severity) 