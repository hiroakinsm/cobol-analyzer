# /home/administrator/cobol-analyzer/src/db/database_layer.py

from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
import motor.motor_asyncio
import logging
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# データベース設定
class DatabaseConfig:
    def __init__(
        self,
        host: str = "172.16.0.17",
        port: int = 27017,
        database: str = "cobol_ast_db",
        user: str = "administrator",
        password: str = "Kanami1001!",
        connection_timeout: int = 30000,
        server_selection_timeout: int = 30000,
        max_pool_size: int = 100,
        min_pool_size: int = 10
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection_timeout = connection_timeout
        self.server_selection_timeout = server_selection_timeout
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size

class DatabaseError(Exception):
    """データベースエラーの基底クラス"""
    def __init__(self, message: str = "Database operation error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class ConnectionError(DatabaseError):
    """接続エラー"""
    def __init__(self, message: str = "Database connection error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"Connection Error: {self.message}"


class TransactionError(DatabaseError):
    """トランザクションエラー"""
    def __init__(self, message: str = "Database transaction error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"Transaction Error: {self.message}"


class QueryError(DatabaseError):
    """クエリエラー"""
    def __init__(self, message: str = "Database query error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"Query Error: {self.message}"

T = TypeVar('T')

class MongoManager:
    """MongoDBデータベース管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)
        self.connection_stats = {
            'status': 'initialized',
            'active_operations': 0,
            'total_operations': 0,
            'error_count': 0
        }

    async def initialize(self):
        """データベース接続の初期化"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user,
                password=self.config.password,
                serverSelectionTimeoutMS=self.config.server_selection_timeout,
                connectTimeoutMS=self.config.connection_timeout,
                maxPoolSize=self.config.max_pool_size,
                minPoolSize=self.config.min_pool_size
            )
            self.db = self.client[self.config.database]
            
            # 接続テスト
            await self.client.admin.command('ping')
            self.connection_stats['status'] = 'active'
            self.logger.info("MongoDB connection initialized successfully")

        except Exception as e:
            self.connection_stats['status'] = 'failed'
            self.connection_stats['error_count'] += 1
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")

    async def close(self):
        """接続のクローズ"""
        if self.client:
            self.client.close()
            self.connection_stats['status'] = 'closed'
            self.logger.info("MongoDB connection closed")

    def get_collection(self, name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
        """コレクション取得"""
        if not self.db:
            raise ConnectionError("Database connection not initialized")
        return self.db[name]

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        if not self.client:
            raise ConnectionError("Database connection not initialized")

        async with await self.client.start_session() as session:
            self.connection_stats['active_operations'] += 1
            try:
                async with session.start_transaction():
                    yield session
            except Exception as e:
                self.connection_stats['error_count'] += 1
                self.logger.error(f"Transaction error: {str(e)}")
                raise TransactionError(f"Transaction failed: {str(e)}")
            finally:
                self.connection_stats['active_operations'] -= 1

    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """集約クエリの実行"""
        if not self.db:
            raise ConnectionError("Database connection not initialized")

        try:
            self.connection_stats['total_operations'] += 1
            return await self.db[collection].aggregate(pipeline).to_list(None)
        except Exception as e:
            self