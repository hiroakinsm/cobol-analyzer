from typing import Dict, Any, Optional
import asyncpg
import motor.motor_asyncio
from config.database import DatabaseConfig

class PostgreSQLConnectionManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        """PostgreSQL接続プールの初期化"""
        self.pool = await asyncpg.create_pool(
            host=self.config.pg_host,
            port=self.config.pg_port,
            user=self.config.pg_user,
            password=self.config.pg_password,
            database=self.config.pg_database,
            min_size=5,
            max_size=20
        )

    async def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        """メタデータの取得"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            query = """
                SELECT m.* 
                FROM metadata m 
                WHERE m.source_id = $1
            """
            result = await conn.fetchrow(query, source_id)
            return dict(result) if result else None

    async def close(self):
        """接続プールのクローズ"""
        if self.pool:
            await self.pool.close()

class MongoDBConnectionManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb://{config.mongo_user}:{config.mongo_password}@{config.mongo_host}:{config.mongo_port}"
        )
        self.db = self.client[config.mongo_database]

    async def fetch_ast(self, source_id: str) -> Dict[str, Any]:
        """ASTデータの取得"""
        collection = self.db.ast_collection
        result = await collection.find_one({"source_id": source_id})
        return result

    async def close(self):
        """MongoDB接続のクローズ"""
        self.client.close()

class DatabaseConnectionManager:
    def __init__(self, config: DatabaseConfig):
        self.pg_manager = PostgreSQLConnectionManager(config)
        self.mongo_manager = MongoDBConnectionManager(config)

    async def initialize(self):
        """両方のデータベース接続を初期化"""
        await self.pg_manager.initialize()

    async def get_metadata(self, source_id: str) -> Dict[str, Any]:
        """メタデータの取得"""
        return await self.pg_manager.fetch_metadata(source_id)

    async def get_ast(self, source_id: str) -> Dict[str, Any]:
        """ASTデータの取得"""
        return await self.mongo_manager.fetch_ast(source_id)

    async def close(self):
        """全ての接続をクローズ"""
        await self.pg_manager.close()
        await self.mongo_manager.close() 