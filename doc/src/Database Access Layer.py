```python
from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
import asyncpg
import motor.motor_asyncio
from abc import ABC, abstractmethod
import logging
from contextlib import asynccontextmanager

# データベース設定
class DatabaseConfig:
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_connections: int = 10,
        max_connections: int = 100
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_connections = min_connections
        self.max_connections = max_connections

class PostgresManager:
    """PostgreSQLデータベース管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)

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
                max_size=self.config.max_connections
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL pool: {str(e)}")
            raise

    async def close(self):
        """コネクションプールのクローズ"""
        if self.pool:
            await self.pool.close()

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection

    async def execute(self, query: str, *args) -> str:
        """クエリの実行"""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """データの取得"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """1行データの取得"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None

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
                password=self.config.password
            )
            self.db = self.client[self.config.database]
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    async def close(self):
        """接続のクローズ"""
        if self.client:
            self.client.close()

    def get_collection(self, name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
        """コレクションの取得"""
        return self.db[name]

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """ドキュメントの挿入"""
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)

    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ドキュメントの検索"""
        result = await self.db[collection].find_one(filter_dict)
        return result

    async def find_many(self, collection: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """複数ドキュメントの検索"""
        cursor = self.db[collection].find(filter_dict)
        return await cursor.to_list(length=None)

    async def update_one(self, collection: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """ドキュメントの更新"""
        result = await self.db[collection].update_one(filter_dict, {"$set": update_dict})
        return result.modified_count

class DatabaseError(Exception):
    """データベースエラーの基底クラス"""
    pass

class ConnectionError(DatabaseError):
    """接続エラー"""
    pass

class TransactionError(DatabaseError):
    """トランザクションエラー"""
    pass

class QueryError(DatabaseError):
    """クエリエラー"""
    pass

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

# 使用例
async def example_usage():
    # PostgreSQL設定
    postgres_config = DatabaseConfig(
        host="172.16.0.13",
        port=5432,
        database="cobol_analysis_db",
        user="cobana_admin",
        password="Kanami1001!"
    )

    # MongoDB設定
    mongo_config = DatabaseConfig(
        host="172.16.0.17",
        port=27017,
        database="cobol_ast_db",
        user="administrator",
        password="Kanami1001!"
    )

    try:
        # マネージャーの作成
        postgres = await DatabaseManagerFactory.create_postgres_manager(postgres_config)
        mongo = await DatabaseManagerFactory.create_mongo_manager(mongo_config)

        # PostgreSQLトランザクション例
        async with postgres.transaction() as connection:
            # 解析タスクの作成
            task_id = UUID('12345678-1234-5678-1234-567812345678')
            await connection.execute("""
                INSERT INTO analysis_tasks (task_id, status, created_at)
                VALUES ($1, 'pending', $2)
            """, task_id, datetime.utcnow())

        # MongoDB操作例
        ast_document = {
            "source_id": str(UUID('12345678-1234-5678-1234-567812345678')),
            "ast_data": {"type": "program", "children": []},
            "created_at": datetime.utcnow()
        }
        await mongo.insert_one("ast_collection", ast_document)

    except Exception as e:
        logging.error(f"Database operation failed: {str(e)}")
        raise
    finally:
        # リソースのクリーンアップ
        await postgres.close()
        await mongo.close()
```