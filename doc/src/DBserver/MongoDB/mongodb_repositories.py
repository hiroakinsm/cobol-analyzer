# /home/administrator/cobol-analyzer/src/repository/repositories.py

from typing import Dict, List, Optional, Any, TypeVar, Generic
from uuid import UUID
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from abc import ABC, abstractmethod

from ..models.data_models import (
    ASTData, AnalysisResult, MetricsData, DocumentData,
    CrossReference, EmbeddedAnalysisData, IntegratedAnalysisResult
)

T = TypeVar('T')

class MongoRepository(Generic[T]):
    """MongoDB用リポジトリ基底クラス"""
    def __init__(self, client: AsyncIOMotorClient, database: str, collection: str):
        self.client = client
        self.db: AsyncIOMotorDatabase = client[database]
        self.collection: AsyncIOMotorCollection = self.db[collection]
        self.logger = logging.getLogger(self.__class__.__name__)

    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """単一ドキュメントの取得"""
        try:
            return await self.collection.find_one(filter_dict)
        except Exception as e:
            self.logger.error(f"Failed to find document: {str(e)}")
            raise

    async def find_many(self, filter_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """複数ドキュメントの取得"""
        try:
            cursor = self.collection.find(filter_dict)
            return await cursor.to_list(None)
        except Exception as e:
            self.logger.error(f"Failed to find documents: {str(e)}")
            raise

    async def insert_one(self, document: Dict[str, Any]) -> str:
        """ドキュメントの挿入"""
        try:
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to insert document: {str(e)}")
            raise

    async def update_one(self, filter_dict: Dict[str, Any], 
                        update_dict: Dict[str, Any]) -> bool:
        """ドキュメントの更新"""
        try:
            result = await self.collection.update_one(
                filter_dict,
                {"$set": update_dict}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Failed to update document: {str(e)}")
            raise

    async def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """ドキュメントの削除"""
        try:
            result = await self.collection.delete_one(filter_dict)
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Failed to delete document: {str(e)}")
            raise

class ASTRepository(MongoRepository[ASTData]):
    """ASTリポジトリ"""
    def __init__(self, client: AsyncIOMotorClient):
        super().__init__(client, "cobol_ast_db", "ast_collection")

    async def store_ast(self, source_id: UUID, ast_data: Dict[str, Any]) -> str:
        """ASTデータの保存"""
        document = {
            "source_id": str(source_id),
            "ast_data": ast_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {
                "version": "1.0",
                "parser_type": "cobol"
            }
        }
        return await self.insert_one(document)

    async def get_ast(self, source_id: UUID) -> Optional[Dict[str, Any]]:
        """ASTデータの取得"""
        return await self.find_one({"source_id": str(source_id)})

    async def get_multiple_asts(self, source_ids: List[UUID]) -> List[Dict[str, Any]]:
        """複数ASTの取得"""
        str_ids = [str(sid) for sid in source_ids]
        return await self.find_many({"source_id": {"$in": str_ids}})

    async def update_ast(self, source_id: UUID, ast_data: Dict[str, Any]) -> bool:
        """ASTの更新"""
        update_data = {
            "ast_data": ast_data,
            "updated_at": datetime.utcnow()
        }
        return await self.update_one(
            {"source_id": str(source_id)},
            update_data
        )

class AnalysisResultRepository(MongoRepository[AnalysisResult]):
    """解析結果リポジトリ"""
    def __init__(self, client: AsyncIOMotorClient):
        super().__init__(client, "cobol_ast_db", "analysis_results")

    async def store_result(self, source_id: UUID, result: Dict[str, Any]) -> str:
        """解析結果の保存"""
        document = {
            "source_id": str(source_id),
            "result_data": result,
            "created_at": datetime.utcnow(),
            "result_type": result.get("type", "unknown")
        }
        return await self.insert_one(document)

    async def get_results(self, source_id: UUID) -> List[Dict[str, Any]]:
        """解析結果の取得"""
        return await self.find_many({"source_id": str(source_id)})

    async def get_latest_result(self, source_id: UUID, 
                              result_type: str) -> Optional[Dict[str, Any]]:
        """最新の解析結果取得"""
        cursor = self.collection.find({
            "source_id": str(source_id),
            "result_type": result_type
        }).sort("created_at", -1).limit(1)
        
        results = await cursor.to_list(None)
        return results[0] if results else None

class MetricsRepository(MongoRepository[MetricsData]):
    """メトリクスリポジトリ"""
    def __init__(self, client: AsyncIOMotorClient):
        super().__init__(client, "cobol_ast_db", "metrics_data")

    async def store_metrics(self, source_id: UUID, 
                          metrics_data: Dict[str, Any]) -> str:
        """メトリクスの保存"""
        document = {
            "source_id": str(source_id),
            "metrics": metrics_data,
            "created_at": datetime.utcnow(),
            "aggregated": False
        }
        return await self.insert_one(document)

    async def get_metrics_history(self, source_id: UUID, 
                                metric_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """メトリクス履歴の取得"""
        filter_dict = {"source_id": str(source_id)}
        if metric_type:
            filter_dict["metrics.type"] = metric_type
            
        return await self.find_many(filter_dict)

    async def aggregate_metrics(self, source_ids: List[UUID]) -> Dict[str, Any]:
        """メトリクスの集約"""
        str_ids = [str(sid) for sid in source_ids]
        pipeline = [
            {"$match": {"source_id": {"$in": str_ids}}},
            {"$group": {
                "_id": "$metrics.type",
                "average": {"$avg": "$metrics.value"},
                "max": {"$max": "$metrics.value"},
                "min": {"$min": "$metrics.value"},
                "count": {"$sum": 1}
            }}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(None)
        return {doc["_id"]: doc for doc in result}

class EmbeddedAnalysisRepository(MongoRepository[EmbeddedAnalysisData]):
    """埋め込み解析リポジトリ"""
    def __init__(self, client: AsyncIOMotorClient):
        super().__init__(client, "cobol_ast_db", "embedded_analysis")

    async def store_embedded_analysis(self, source_id: UUID, 
                                    analysis_data: Dict[str, Any]) -> str:
        """埋め込み解析結果の保存"""
        document = {
            "source_id": str(source_id),
            "analysis_data": analysis_data,
            "created_at": datetime.utcnow(),
            "analysis_type": analysis_data.get("type", "unknown")
        }
        return await self.insert_one(document)

    async def get_embedded_analysis(self, source_id: UUID, 
                                  analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """埋め込み解析結果の取得"""
        filter_dict = {"source_id": str(source_id)}
        if analysis_type:
            filter_dict["analysis_type"] = analysis_type
        return await self.find_many(filter_dict)

class CrossReferenceRepository(MongoRepository[CrossReference]):
    """クロスリファレンスリポジトリ"""
    def __init__(self, client: AsyncIOMotorClient):
        super().__init__(client, "cobol_ast_db", "cross_references")

    async def store_references(self, source_id: UUID, 
                             references: Dict[str, Any]) -> str:
        """クロスリファレンスの保存"""
        document = {
            "source_id": str(source_id),
            "references": references,
            "created_at": datetime.utcnow(),
            "reference_type": references.get("type", "unknown")
        }
        return await self.insert_one(document)

    async def get_references(self, source_id: UUID) -> List[Dict[str, Any]]:
        """クロスリファレンスの取得"""
        return await self.find_many({"source_id": str(source_id)})

    async def get_dependent_sources(self, source_id: UUID) -> List[str]:
        """依存ソースの取得"""
        pipeline = [
            {"$match": {"references.dependencies": str(source_id)}},
            {"$project": {"source_id": 1}}
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(None)
        return [doc["source_id"] for doc in result]

class IntegratedResultRepository(MongoRepository[IntegratedAnalysisResult]):
    """統合解析結果リポジトリ"""
    def __init__(self, client: AsyncIOMotorClient):
        super().__init__(client, "cobol_ast_db", "integrated_results")

    async def store_integrated_result(self, source_ids: List[UUID], 
                                    result: Dict[str, Any]) -> str:
        """統合結果の保存"""
        document = {
            "source_ids": [str(sid) for sid in source_ids],
            "result_data": result,
            "created_at": datetime.utcnow(),
            "integration_type": result.get("type", "unknown")
        }
        return await self.insert_one(document)

    async def get_integrated_results(self, source_ids: List[UUID]) -> List[Dict[str, Any]]:
        """統合結果の取得"""
        str_ids = [str(sid) for sid in source_ids]
        return await self.find_many({
            "source_ids": {"$all": str_ids}
        })