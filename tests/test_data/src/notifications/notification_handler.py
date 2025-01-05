import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from datetime import datetime
import configparser
import os
from src.notifications.notification_manager import NotificationManager, ErrorSeverity

class NotificationHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_config()
        self.manager = NotificationManager(
            error_threshold=self.config['Notification'].getint('error_threshold'),
            notification_interval=self.config['Notification'].getint('notification_interval')
        )

    def _load_config(self):
        config = configparser.ConfigParser()
        config_path = os.path.join('config', 'notification_config.ini')
        config.read(config_path)

        self.smtp_host = config['Email']['smtp_host']
        self.smtp_port = config['Email'].getint('smtp_port')
        self.sender = config['Email']['sender']
        self.recipient = config['Email']['recipient']
        self.username = config['Email']['username']
        self.password = config['Email']['password']

    def send_error_notification(self, error_type, error_message, context=None, severity=ErrorSeverity.MEDIUM):
        if not self.manager.should_notify(error_type, severity):
            self.logger.info(f"Skipping notification for {error_type} (severity: {severity.value})")
            return

        template = self.manager.get_notification_template(severity)
        subject = f"{template['subject_prefix']} {error_type}"
        
        # テンプレートからメール本文を生成
        body = self._generate_message_body(template['template'], {
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'severity': severity.value,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        self._send_email(subject, body)

    def _generate_message_body(self, template_path, params):
        try:
            with open(template_path, 'r') as f:
                template = f.read()
            return template.format(**params)
        except Exception as e:
            self.logger.error(f"Failed to load template: {str(e)}")
            # フォールバックテンプレート
            return """
Error Report:
Type: {error_type}
Severity: {severity}
Time: {timestamp}
Message: {error_message}
Context: {context}
"""

    def _send_email(self, subject, body):
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = self.recipient
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.login(self.username, self.password)
            server.send_message(msg) 