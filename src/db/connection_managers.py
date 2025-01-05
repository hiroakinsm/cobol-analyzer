# /home/administrator/cobol-analyzer/src/db/connection_managers.py

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncpg
import motor.motor_asyncio
import logging
from contextlib import asynccontextmanager

class PostgresConnectionManager:
    """PostgreSQL接続管理"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """コネクションプールの初期化"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                min_size=self.config.get("min_connections", 10),
                max_size=self.config.get("max_connections", 100)
            )
            self.logger.info("PostgreSQL connection pool initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL pool: {str(e)}")
            raise

    async def close(self):
        """接続のクローズ"""
        if self.pool:
            await self.pool.close()
            self.logger.info("PostgreSQL connection pool closed")

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
        """複数行の取得"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """1行の取得"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None

class MongoConnectionManager:
    """MongoDB接続管理"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """データベース接続の初期化"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                host=self.config["host"],
                port=self.config["port"],
                username=self.config["user"],
                password=self.config["password"]
            )
            self.db = self.client[self.config["database"]]
            self.logger.info("MongoDB connection initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    async def close(self):
        """接続のクローズ"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")

    def get_collection(self, name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
        """コレクションの取得"""
        return self.db[name]

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session

    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """1件のドキュメント検索"""
        return await self.db[collection].find_one(filter_dict)

    async def find_many(self, collection: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """複数ドキュメントの検索"""
        cursor = self.db[collection].find(filter_dict)
        return await cursor.to_list(length=None)

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """ドキュメントの挿入"""
        result = await self.db[collection].insert_one(document)
        return str(result.inserted_id)

    async def update_one(self, collection: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """ドキュメントの更新"""
        result = await self.db[collection].update_one(
            filter_dict,
            {"$set": update_dict}
        )
        return result.modified_count
