import pytest
from src.notifications.notification_handler import NotificationHandler
from src.db.error_handler import DatabaseErrorHandler
import psycopg2
from src.notifications.error_severity import ErrorSeverity

class TestNotifications:
    def setup_method(self):
        self.notifier = NotificationHandler()
        self.error_handler = DatabaseErrorHandler()

    def test_error_notification(self):
        # 基本的なエラー通知のテスト
        error_type = "Test Error"
        error_message = "This is a test error message"
        context = {"test_key": "test_value"}

        try:
            self.notifier.send_error_notification(error_type, error_message, context)
        except Exception as e:
            pytest.fail(f"Error notification failed: {str(e)}")

    def test_database_error_notification(self):
        # データベースエラーの通知テスト
        try:
            # 意図的にエラーを発生させる
            with pytest.raises(Exception):
                self.error_handler.handle_query_error(
                    error=psycopg2.Error("Test DB Error"),
                    query="SELECT * FROM nonexistent_table",
                    params={"id": 1}
                )
        except Exception as e:
            pytest.fail(f"Database error notification failed: {str(e)}")

    def test_notification_with_empty_context(self):
        # コンテキストなしのエラー通知テスト
        error_type = "Empty Context Error"
        error_message = "Error without context"

        try:
            self.notifier.send_error_notification(error_type, error_message)
        except Exception as e:
            pytest.fail(f"Error notification with empty context failed: {str(e)}")

    def test_notification_severity_levels(self):
        # 各重要度レベルでの通知テスト
        test_cases = [
            (ErrorSeverity.LOW, "Low Priority Issue"),
            (ErrorSeverity.MEDIUM, "Medium Priority Issue"),
            (ErrorSeverity.HIGH, "High Priority Issue"),
            (ErrorSeverity.CRITICAL, "Critical System Issue")
        ]

        for severity, message in test_cases:
            try:
                self.notifier.send_error_notification(
                    error_type=f"Test {severity.value} Error",
                    error_message=message,
                    context={"test": "context"},
                    severity=severity
                )
            except Exception as e:
                pytest.fail(f"Notification failed for {severity.value}: {str(e)}")

    def test_notification_threshold(self):
        # 通知閾値のテスト
        error_type = "Repeated Error"
        message = "This is a repeated error"

        # LOW severity - should notify after 3 occurrences
        for _ in range(2):
            self.notifier.send_error_notification(
                error_type=error_type,
                error_message=message,
                severity=ErrorSeverity.LOW
            )
            assert self.notifier.manager.error_counts[f"{error_type}_LOW"] > 0

        # CRITICAL severity - should notify immediately
        self.notifier.send_error_notification(
            error_type=error_type,
            error_message="Critical error",
            severity=ErrorSeverity.CRITICAL
        )
        assert self.notifier.manager.error_counts[f"{error_type}_CRITICAL"] == 0

    def test_notification_interval(self):
        # 通知間隔のテスト
        error_type = "Frequent Error"
        message = "This is a frequent error"

        # 最初の通知
        self.notifier.send_error_notification(
            error_type=error_type,
            error_message=message,
            severity=ErrorSeverity.HIGH
        )

        # 直後の通知は抑制されるはず
        result = self.notifier.manager.should_notify(error_type, ErrorSeverity.HIGH)
        assert not result 