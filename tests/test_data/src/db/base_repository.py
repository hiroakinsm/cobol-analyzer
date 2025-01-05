import time
from functools import wraps
from src.db.error_handler import DatabaseError
from src.db.connection_pool import DatabaseConnectionPool
from contextlib import contextmanager

def with_auto_reconnect(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(self, *args, **kwargs)
                except DatabaseError as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        self._handle_connection_error(e)
                        time.sleep(delay * (attempt + 1))
                        self._reconnect()
                    continue
            raise last_error
        return wrapper
    return decorator

class BaseRepository:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.pool = DatabaseConnectionPool(**connection_params)
        self.error_handler = None  # サブクラスで設定

    def _reconnect(self):
        """接続の再確立を試みる"""
        self.pool = DatabaseConnectionPool(**self.connection_params)

    def _handle_connection_error(self, error):
        """接続エラーの処理"""
        if self.error_handler:
            self.error_handler.handle_connection_error(error)

    @contextmanager
    def get_connection(self):
        """コネクションプールからの接続取得"""
        with self.pool.get_connection() as conn:
            yield conn 