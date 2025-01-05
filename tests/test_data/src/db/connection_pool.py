import psycopg2
from psycopg2.pool import SimpleConnectionPool
import threading
from contextlib import contextmanager

class DatabaseConnectionPool:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, min_conn=1, max_conn=10, **kwargs):
        if not hasattr(self, 'pool'):
            self.connection_params = kwargs
            self.pool = SimpleConnectionPool(min_conn, max_conn, **kwargs)
            self.active_connections = 0

    @contextmanager
    def get_connection(self):
        connection = self.pool.getconn()
        self.active_connections += 1
        try:
            yield connection
        finally:
            self.pool.putconn(connection)
            self.active_connections -= 1

    def close_all(self):
        if hasattr(self, 'pool'):
            self.pool.closeall()

    def get_status(self):
        return {
            'active_connections': self.active_connections,
            'pool_size': self.pool.maxconn,
            'available': self.pool.maxconn - self.active_connections
        } 