# /home/administrator/cobol-analyzer/src/repository/repository_implementation.py

from typing import Dict, List, Optional, Any, Generic, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import UUID
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from dataclasses import dataclass
from collections import defaultdict

T = TypeVar('T')

class MongoRepository(Generic[T]):
    """MongoDB用リポジトリ基底クラス"""
    def __init__(self, db_client: AsyncIOMotorClient, model_class: type[T]):
        self.client = db_client
        self.model_class = model_class
        self.collection_name = model_class.__name__.lower()
        self.logger = logging.getLogger(__name__)
        self.db = self.client.cobol_ast_db

    def get_collection(self, name: str = None) -> AsyncIOMotorCollection:
        """コレクションの取得"""
        return self.db[name or self.collection_name]

    async def get(self, id: Any) -> Optional[T]:
        """IDによるエンティティ取得"""
        try:
            doc = await self.get_collection().find_one({"_id": id})
            return self.model_class(**doc) if doc else None
        except Exception as e:
            self.logger.error(f"Failed to get {self.collection_name} by id {id}: {str(e)}")
            raise

    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        """フィルタ条件によるエンティティ取得"""
        try:
            cursor = self.get_collection().find(filter_dict)
            docs = await cursor.to_list(None)
            return [self.model_class(**doc) for doc in docs]
        except Exception as e:
            self.logger.error(f"Failed to get many {self.collection_name}: {str(e)}")
            raise

    async def add(self, entity: T) -> Any:
        """エンティティの追加"""
        try:
            result = await self.get_collection().insert_one(entity.__dict__)
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Failed to add {self.collection_name}: {str(e)}")
            raise

    async def update(self, entity: T) -> bool:
        """エンティティの更新"""
        try:
            result = await self.get_collection().update_one(
                {"_id": entity.id},
                {"$set": {**entity.__dict__, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Failed to update {self.collection_name}: {str(e)}")
            raise

    async def delete(self, id: Any) -> bool:
        """エンティティの削除"""
        try:
            result = await self.get_collection().delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Failed to delete {self.collection_name}: {str(e)}")
            raise

class ASTRepository(MongoRepository['ASTData']):
    """ASTリポジトリ"""
    async def get_ast_by_source(self, source_id: UUID) -> Optional['ASTData']:
        """ソースIDによるAST取得"""
        try:
            doc = await self.get_collection("ast_collection").find_one(
                {"source_id": str(source_id)}
            )
            return self.model_class(**doc) if doc else None
        except Exception as e:
            self.logger.error(f"Failed to get AST by source: {str(e)}")
            raise

    async def update_ast(self, source_id: UUID, ast_data: Dict[str, Any]) -> bool:
        """AST更新"""
        try:
            result = await self.get_collection("ast_collection").update_one(
                {"source_id": str(source_id)},
                {
                    "$set": {
                        "ast_data": ast_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Failed to update AST: {str(e)}")
            raise

class AnalysisDetailsRepository(MongoRepository['AnalysisDetails']):
    """解析詳細リポジトリ"""
    async def store_analysis_details(self, result_id: UUID, details: Dict[str, Any]) -> str:
        """解析詳細の保存"""
        try:
            document = {
                "result_id": str(result_id),
                "details": details,
                "created_at": datetime.utcnow()
            }
            result = await self.get_collection("analysis_details").insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to store analysis details: {str(e)}")
            raise

    async def get_analysis_details(self, result_id: UUID) -> Optional[Dict[str, Any]]:
        """解析詳細の取得"""
        try:
            return await self.get_collection("analysis_details").find_one(
                {"result_id": str(result_id)}
            )
        except Exception as e:
            self.logger.error(f"Failed to get analysis details: {str(e)}")
            raise

class MetricsRepository(MongoRepository['MetricsData']):
    """メトリクスリポジトリ"""
    async def store_metrics(self, source_id: UUID, metrics_data: Dict[str, Any]) -> str:
        """メトリクスの保存"""
        try:
            document = {
                "source_id": str(source_id),
                "metrics_data": metrics_data,
                "created_at": datetime.utcnow()
            }
            result = await self.get_collection("metrics_data").insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to store metrics: {str(e)}")
            raise

    async def get_historical_metrics(self, source_id: UUID,
                                   metric_type: str) -> List[Dict[str, Any]]:
        """履歴メトリクスの取得"""
        try:
            cursor = self.get_collection("metrics_data").find({
                "source_id": str(source_id),
                "metrics_data.type": metric_type
            }).sort("created_at", -1)
            return await cursor.to_list(None)
        except Exception as e:
            self.logger.error(f"Failed to get historical metrics: {str(e)}")
            raise

    async def get_aggregated_metrics(self, 
                                   source_ids: List[UUID],
                                   metric_type: str) -> Dict[str, Any]:
        """集約メトリクスの取得"""
        try:
            pipeline = [
                {
                    "$match": {
                        "source_id": {"$in": [str(sid) for sid in source_ids]},
                        "metrics_data.type": metric_type
                    }
                },
                {
                    "$group": {
                        "_id": "$metrics_data.type",
                        "average": {"$avg": "$metrics_data.value"},
                        "max": {"$max": "$metrics_data.value"},
                        "min": {"$min": "$metrics_data.value"},
                        "total_count": {"$sum": 1}
                    }
                }
            ]
            result = await self.get_collection("metrics_data").aggregate(pipeline).to_list(None)
            return result[0] if result else {}
        except Exception as e:
            self.logger.error(f"Failed to get aggregated metrics: {str(e)}")
            raise

class BenchmarkDataRepository(MongoRepository['BenchmarkData']):
    """ベンチマークデータリポジトリ"""
    async def store_benchmark_data(self, benchmark_data: Dict[str, Any]) -> str:
        """ベンチマークデータの保存"""
        try:
            document = {
                **benchmark_data,
                "created_at": datetime.utcnow()
            }
            result = await self.get_collection("benchmark_data").insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to store benchmark data: {str(e)}")
            raise

    async def get_benchmark_results(self, category: str) -> List[Dict[str, Any]]:
        """ベンチマーク結果の取得"""
        try:
            cursor = self.get_collection("benchmark_data").find({
                "category": category
            }).sort("created_at", -1)
            return await cursor.to_list(None)
        except Exception as e:
            self.logger.error(f"Failed to get benchmark results: {str(e)}")
            raise

class CrossReferenceRepository(MongoRepository['CrossReference']):
    """クロスリファレンスリポジトリ"""
    async def store_cross_references(self, source_id: UUID,
                                   references: Dict[str, Any]) -> str:
        """クロスリファレンスの保存"""
        try:
            document = {
                "source_id": str(source_id),
                "references": references,
                "created_at": datetime.utcnow()
            }
            result = await self.get_collection("cross_references").insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to store cross references: {str(e)}")
            raise

    async def get_references_by_source(self, source_id: UUID) -> Optional[Dict[str, Any]]:
        """ソースごとのリファレンス取得"""
        try:
            return await self.get_collection("cross_references").find_one({
                "source_id": str(source_id)
            })
        except Exception as e:
            self.logger.error(f"Failed to get cross references: {str(e)}")
            raise

class IntegratedResultRepository:
    """統合結果リポジトリ"""
    def __init__(self, 
                analysis_result_repo: AnalysisDetailsRepository,
                ast_repo: ASTRepository):
        self.analysis_result_repo = analysis_result_repo
        self.ast_repo = ast_repo
        self.logger = logging.getLogger(__name__)

    async def get_integrated_result(self, source_id: UUID) -> Dict[str, Any]:
        """統合結果の取得"""
        try:
            # 解析結果の取得
            analysis_results = await self.analysis_result_repo.get_many({
                "source_id": str(source_id)
            })
            
            # AST情報の取得
            ast = await self.ast_repo.get_ast_by_source(source_id)

            # 結果の統合
            integrated = {
                "source_id": source_id,
                "analysis_results": [result.__dict__ for result in analysis_results],
                "ast_info": ast.__dict__ if ast else None,
                "summary": {
                    "total_analyses": len(analysis_results),
                    "latest_analysis": analysis_results[0].__dict__ if analysis_results else None,
                    "has_ast": ast is not None
                },
                "integrated_at": datetime.utcnow()
            }

            return integrated
        except Exception as e:
            self.logger.error(f"Failed to get integrated result: {str(e)}")
            raise