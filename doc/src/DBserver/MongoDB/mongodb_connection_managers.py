# /home/administrator/cobol-analyzer/src/db/connection_managers.py

from typing import Dict, List, Any, Optional
from datetime import datetime
import motor.motor_asyncio
import logging
from contextlib import asynccontextmanager
import yaml
from pathlib import Path

class ConnectionConfig:
    """データベース接続設定"""
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def get_mongodb_config(self) -> Dict[str, Any]:
        """MongoDB設定の取得"""
        return self.config.get('mongodb', {
            'host': '172.16.0.17',
            'port': 27017,
            'database': 'cobol_ast_db',
            'user': 'administrator',
            'password': 'Kanami1001!',
            'connection_timeout': 30000,
            'server_selection_timeout': 30000
        })

class MongoConnectionManager:
    """MongoDB接続管理"""
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)
        self.connection_stats = {
            'status': 'initialized',
            'active_operations': 0,
            'last_error': None
        }

    async def initialize(self):
        """データベース接続の初期化"""
        try:
            mongodb_config = self.config.get_mongodb_config()

            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                host=mongodb_config["host"],
                port=mongodb_config["port"],
                username=mongodb_config["user"],
                password=mongodb_config["password"],
                serverSelectionTimeoutMS=mongodb_config["server_selection_timeout"],
                connectTimeoutMS=mongodb_config["connection_timeout"]
            )
            self.db = self.client[mongodb_config["database"]]
            
            # 接続テスト
            await self.client.admin.command('ping')
            self.connection_stats['status'] = 'active'
            self.logger.info("MongoDB connection initialized")

        except Exception as e:
            self.connection_stats['status'] = 'failed'
            self.connection_stats['last_error'] = str(e)
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    async def close(self):
        """接続のクローズ"""
        if self.client:
            self.client.close()
            self.connection_stats['status'] = 'closed'
            self.logger.info("MongoDB connection closed")

    def get_collection(self, name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
        """コレクション取得"""
        return self.db[name]

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with await self.client.start_session() as session:
            self.connection_stats['active_operations'] += 1
            try:
                async with session.start_transaction():
                    yield session
            finally:
                self.connection_stats['active_operations'] -= 1

    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """集約クエリの実行"""
        try:
            self.connection_stats['active_operations'] += 1
            return await self.db[collection].aggregate(pipeline).to_list(None)
        finally:
            self.connection_stats['active_operations'] -= 1

    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """1件のドキュメント検索"""
        try:
            self.connection_stats['active_operations'] += 1
            return await self.db[collection].find_one(filter_dict)
        finally:
            self.connection_stats['active_operations'] -= 1

    async def find_many(self, collection: str, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """複数ドキュメントの検索"""
        try:
            self.connection_stats['active_operations'] += 1
            cursor = self.db[collection].find(filter_dict)
            return await cursor.to_list(None)
        finally:
            self.connection_stats['active_operations'] -= 1

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """ドキュメントの挿入"""
        try:
            self.connection_stats['active_operations'] += 1
            result = await self.db[collection].insert_one(document)
            return str(result.inserted_id)
        finally:
            self.connection_stats['active_operations'] -= 1

    async def update_one(self, collection: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> int:
        """ドキュメントの更新"""
        try:
            self.connection_stats['active_operations'] += 1
            result = await self.db[collection].update_one(
                filter_dict,
                {"$set": update_dict}
            )
            return result.modified_count
        finally:
            self.connection_stats['active_operations'] -= 1

    async def get_connection_stats(self) -> Dict[str, Any]:
        """接続統計の取得"""
        return self.connection_stats