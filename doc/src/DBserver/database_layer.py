# /home/administrator/cobol-analyzer/src/db/database_layer.py

from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
import asyncpg
import motor.motor_asyncio
from abc import ABC, abstractmethod
import logging
from contextlib import asynccontextmanager
from enum import Enum
import json
from dataclasses import dataclass

# トランザクション関連の型定義
class TransactionIsolationLevel(Enum):
    """トランザクション分離レベル"""
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"

class TransactionStatus(Enum):
    """トランザクションステータス"""
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"

@dataclass
class TransactionConfig:
    """トランザクション設定"""
    isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED
    read_only: bool = False
    deferrable: bool = False
    timeout: int = 30  # seconds

@dataclass
class DatabaseConfig:
    """データベース設定"""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 10
    max_connections: int = 100
    connection_timeout: int = 60
    command_timeout: int = 30
    pool_recycle: int = 3600

class TransactionManager:
    """トランザクション管理"""
    def __init__(self, connection):
        self.connection = connection
        self.status = TransactionStatus.ACTIVE
        self.start_time = datetime.utcnow()
        self.logger = logging.getLogger(__name__)
        self.savepoints: List[str] = []

    async def commit(self):
        """トランザクションのコミット"""
        try:
            await self.connection.commit()
            self.status = TransactionStatus.COMMITTED
        except Exception as e:
            self.status = TransactionStatus.FAILED
            self.logger.error(f"Transaction commit failed: {str(e)}")
            raise

    async def rollback(self, savepoint: str = None):
        """トランザクションのロールバック"""
        try:
            if savepoint and savepoint in self.savepoints:
                await self.connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                self.savepoints = self.savepoints[:self.savepoints.index(savepoint)]
            else:
                await self.connection.rollback()
                self.savepoints = []
            self.status = TransactionStatus.ROLLED_BACK
        except Exception as e:
            self.status = TransactionStatus.FAILED
            self.logger.error(f"Transaction rollback failed: {str(e)}")
            raise

    async def create_savepoint(self, name: str):
        """セーブポイントの作成"""
        try:
            await self.connection.execute(f"SAVEPOINT {name}")
            self.savepoints.append(name)
        except Exception as e:
            self.logger.error(f"Savepoint creation failed: {str(e)}")
            raise

class PostgresManager:
    """PostgreSQLデータベース管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
        self.active_transactions: Dict[str, TransactionManager] = {}

    async def initialize(self):
        """コネクションプールの初期化"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings={
                    'application_name': 'cobol_analyzer',
                    'statement_timeout': f'{self.config.command_timeout * 1000}'
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL pool: {str(e)}")
            raise

    async def close(self):
        """接続のクローズ"""
        if self.pool:
            active_txn_count = len(self.active_transactions)
            if active_txn_count > 0:
                self.logger.warning(f"Closing pool with {active_txn_count} active transactions")
                for txn in self.active_transactions.values():
                    await txn.rollback()
            await self.pool.close()

    @asynccontextmanager
    async def transaction(self, config: TransactionConfig = None):
        """トランザクション管理"""
        config = config or TransactionConfig()
        connection = await self.pool.acquire()
        transaction_id = str(UUID())
        
        try:
            # トランザクション設定の適用
            await connection.execute(
                f"SET TRANSACTION ISOLATION LEVEL {config.isolation_level.value}"
            )
            if config.read_only:
                await connection.execute("SET TRANSACTION READ ONLY")
            if config.deferrable:
                await connection.execute("SET TRANSACTION DEFERRABLE")

            # トランザクションの開始
            transaction = await connection.transaction()
            await transaction.start()
            
            # トランザクションマネージャーの作成
            txn_manager = TransactionManager(transaction)
            self.active_transactions[transaction_id] = txn_manager

            try:
                yield connection
                await txn_manager.commit()
            except Exception:
                await txn_manager.rollback()
                raise

        finally:
            self.active_transactions.pop(transaction_id, None)
            await self.pool.release(connection)

    async def execute_in_transaction(self, query: str, *args, config: TransactionConfig = None):
        """トランザクション内でのクエリ実行"""
        async with self.transaction(config) as connection:
            return await connection.execute(query, *args)

    async def fetch_in_transaction(self, query: str, *args, config: TransactionConfig = None):
        """トランザクション内でのデータ取得"""
        async with self.transaction(config) as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]

class MongoManager:
    """MongoDBデータベース管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """データベース接続の初期化"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user,
                password=self.config.password,
                serverSelectionTimeoutMS=self.config.connection_timeout * 1000
            )
            self.db = self.client[self.config.database]
            
            # 接続テスト
            await self.client.admin.command('ping')
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    async def close(self):
        """接続のクローズ"""
        if self.client:
            self.client.close()

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                except Exception:
                    await session.abort_transaction()
                    raise

    async def execute_in_transaction(self, collection: str, operation: str, *args, **kwargs):
        """トランザクション内での操作実行"""
        async with self.transaction() as session:
            collection = self.db[collection]
            method = getattr(collection, operation)
            return await method(*args, session=session, **kwargs)

# データベースマネージャーのファクトリ
class DatabaseManagerFactory:
    @staticmethod
    async def create_postgres_manager(config: DatabaseConfig) -> PostgresManager:
        manager = PostgresManager(config)
        await manager.initialize()
        return manager

    @staticmethod
    async def create_mongo_manager(config: DatabaseConfig) -> MongoManager:
        manager = MongoManager(config)
        await manager.initialize()
        return manager