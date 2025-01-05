import logging
import time
from functools import wraps
import psycopg2
from psycopg2 import OperationalError, InterfaceError
from src.notifications.notification_handler import NotificationHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DatabaseError(Exception):
    """データベース操作に関するカスタムエラー"""
    pass

class RetryableError(DatabaseError):
    """リトライ可能なエラー"""
    pass

def with_retry(max_attempts=3, delay=1):
    """リトライ処理を行うデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, InterfaceError) as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                        time.sleep(delay * (attempt + 1))  # 指数バックオフ
                    continue
            raise RetryableError(f"Failed after {max_attempts} attempts: {str(last_error)}")
        return wrapper
    return decorator

class DatabaseErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.notifier = NotificationHandler()

    def handle_connection_error(self, error, context=None):
        """接続エラーの処理"""
        self.logger.error(f"Database connection error: {str(error)}")
        if context:
            self.logger.error(f"Context: {context}")
        
        # エラー通知の送信
        self.notifier.send_error_notification(
            "Database Connection Error",
            str(error),
            context
        )
        
        raise DatabaseError(f"Connection failed: {str(error)}")

    def handle_query_error(self, error, query=None, params=None):
        """クエリエラーの処理"""
        self.logger.error(f"Query execution error: {str(error)}")
        context = {
            "query": query,
            "parameters": params
        }
        
        # エラー通知の送信
        self.notifier.send_error_notification(
            "Query Execution Error",
            str(error),
            context
        )
        
        raise DatabaseError(f"Query failed: {str(error)}")

    def handle_transaction_error(self, error, operation=None):
        """トランザクションエラーの処理"""
        self.logger.error(f"Transaction error: {str(error)}")
        if operation:
            self.logger.error(f"Operation: {operation}")
        raise DatabaseError(f"Transaction failed: {str(error)}")

    def handle_validation_error(self, error, field_name=None, value=None):
        """バリデーションエラーの処理"""
        self.logger.error(f"Validation error: {str(error)}")
        if field_name:
            self.logger.error(f"Field: {field_name}")
        if value:
            self.logger.error(f"Value: {value}")
        raise DatabaseError(f"Validation failed: {str(error)}") 