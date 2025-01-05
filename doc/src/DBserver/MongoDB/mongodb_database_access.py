# /home/administrator/cobol-analyzer/src/db/database_access.py

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from uuid import UUID
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from contextlib import asynccontextmanager
from cachetools import TTLCache

class MongoDatabaseAccess:
    """MongoDBデータベースアクセス"""
    def __init__(self, client: AsyncIOMotorClient):
        self.client = client
        self.db = client.cobol_ast_db
        self.logger = logging.getLogger(__name__)
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # 1時間のキャッシュ

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """コレクションの取得"""
        return self.db[name]

    async def store_ast_data(self, source_id: UUID, ast_data: Dict[str, Any]) -> str:
        """ASTデータの保存"""
        try:
            collection = self.get_collection('ast_collection')
            document = {
                "source_id": str(source_id),
                "ast_data": ast_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            result = await collection.update_one(
                {"source_id": str(source_id)},
                {"$set": document},
                upsert=True
            )

            # キャッシュの無効化
            cache_key = f"ast_{source_id}"
            if cache_key in self.cache:
                del self.cache[cache_key]

            return str(source_id)

        except Exception as e:
            self.logger.error(f"Error storing AST data: {str(e)}")
            raise

    async def get_ast_data(self, source_id: UUID) -> Optional[Dict[str, Any]]:
        """ASTデータの取得"""
        try:
            cache_key = f"ast_{source_id}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            collection = self.get_collection('ast_collection')
            result = await collection.find_one({"source_id": str(source_id)})
            
            if result:
                self.cache[cache_key] = result
            return result

        except Exception as e:
            self.logger.error(f"Error retrieving AST data: {str(e)}")
            raise

    async def store_analysis_details(self, result_id: UUID, 
                                   details: Dict[str, Any]) -> str:
        """詳細な解析結果の保存"""
        try:
            collection = self.get_collection('analysis_details')
            document = {
                "result_id": str(result_id),
                "details": details,
                "created_at": datetime.utcnow()
            }

            result = await collection.insert_one(document)
            return str(result.inserted_id)

        except Exception as e:
            self.logger.error(f"Error storing analysis details: {str(e)}")
            raise

    async def get_analysis_details(self, result_id: UUID) -> Optional[Dict[str, Any]]:
        """詳細な解析結果の取得"""
        try:
            collection = self.get_collection('analysis_details')
            return await collection.find_one({"result_id": str(result_id)})

        except Exception as e:
            self.logger.error(f"Error retrieving analysis details: {str(e)}")
            raise

    async def store_metrics_data(self, source_id: UUID, 
                               metrics_data: Dict[str, Any]) -> str:
        """メトリクスデータの保存"""
        try:
            collection = self.get_collection('metrics_data')
            document = {
                "source_id": str(source_id),
                "metrics_data": metrics_data,
                "created_at": datetime.utcnow()
            }

            result = await collection.insert_one(document)
            return str(result.inserted_id)

        except Exception as e:
            self.logger.error(f"Error storing metrics data: {str(e)}")
            raise

    async def get_historical_metrics(self, source_id: UUID, 
                                   metric_type: str) -> List[Dict[str, Any]]:
        """履歴メトリクスの取得"""
        try:
            collection = self.get_collection('metrics_data')
            cursor = collection.find({
                "source_id": str(source_id),
                "metrics_data.type": metric_type
            }).sort("created_at", -1)

            return await cursor.to_list(length=None)

        except Exception as e:
            self.logger.error(f"Error retrieving historical metrics: {str(e)}")
            raise

    async def store_summary_data(self, source_ids: List[UUID], 
                               summary_data: Dict[str, Any]) -> str:
        """サマリデータの保存"""
        try:
            collection = self.get_collection('summary_data')
            document = {
                "source_ids": [str(sid) for sid in source_ids],
                "summary_data": summary_data,
                "created_at": datetime.utcnow()
            }

            result = await collection.insert_one(document)
            return str(result.inserted_id)

        except Exception as e:
            self.logger.error(f"Error storing summary data: {str(e)}")
            raise

    async def cleanup_old_data(self, retention_days: int = 90) -> None:
        """古いデータの削除"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # 各コレクションの古いデータを削除
            collections = ['ast_collection', 'analysis_details', 
                         'metrics_data', 'summary_data']
            
            for collection_name in collections:
                collection = self.get_collection(collection_name)
                await collection.delete_many({
                    "created_at": {"$lt": cutoff_date}
                })

            # キャッシュのクリア
            self.cache.clear()

        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            raise

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session