# /home/administrator/cobol-analyzer/src/db/repositories.py

from typing import Dict, List, Optional, Any, TypeVar, Generic
from uuid import UUID
from datetime import datetime
import logging
from abc import ABC, abstractmethod

from .query_builders import QueryBuilder, InsertQueryBuilder, UpdateQueryBuilder
from .connection_managers import PostgresConnectionManager, MongoConnectionManager
from ..models.data_models import (
    AnalysisTask, AnalysisSource, AnalysisResult, AnalysisLog,
    BenchmarkMaster, ASTData
)

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """リポジトリの基底クラス"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """単一エンティティの取得"""
        pass

    @abstractmethod
    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        """複数エンティティの取得"""
        pass

    @abstractmethod
    async def add(self, entity: T) -> Any:
        """エンティティの追加"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> bool:
        """エンティティの更新"""
        pass

class PostgresRepository(BaseRepository[T]):
    """PostgreSQL用リポジトリ基底クラス"""
    def __init__(self, connection: PostgresConnectionManager, table_name: str):
        super().__init__()
        self.connection = connection
        self.table_name = table_name

    async def get(self, id: Any) -> Optional[T]:
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("id", "=", id)\
            .build()
        
        result = await self.connection.fetchrow(*query)
        return self._create_entity(result) if result else None

    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        builder = QueryBuilder().from_table(self.table_name)
        for field, value in filter_dict.items():
            builder.where(field, "=", value)
        
        query = builder.build()
        results = await self.connection.fetch(*query)
        return [self._create_entity(row) for row in results]

    @abstractmethod
    def _create_entity(self, row: Dict[str, Any]) -> T:
        """データベースの行からエンティティを生成"""
        pass

class MongoRepository(BaseRepository[T]):
    """MongoDB用リポジトリ基底クラス"""
    def __init__(self, connection: MongoConnectionManager, collection_name: str):
        super().__init__()
        self.connection = connection
        self.collection_name = collection_name

    async def get(self, id: Any) -> Optional[T]:
        doc = await self.connection.find_one(
            self.collection_name,
            {"_id": id}
        )
        return self._create_entity(doc) if doc else None

    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        docs = await self.connection.find_many(
            self.collection_name,
            filter_dict
        )
        return [self._create_entity(doc) for doc in docs]

    @abstractmethod
    def _create_entity(self, doc: Dict[str, Any]) -> T:
        """MongoDBのドキュメントからエンティティを生成"""
        pass

class AnalysisTaskRepository(PostgresRepository[AnalysisTask]):
    """解析タスクリポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "analysis_tasks_partitioned")

    async def get_pending_tasks(self) -> List[AnalysisTask]:
        """保留中のタスクを取得"""
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("status", "=", "pending")\
            .order_by("priority DESC", "created_at ASC")\
            .build()
        
        results = await self.connection.fetch(*query)
        return [self._create_entity(row) for row in results]

    async def update_status(self, task_id: UUID, 
                          status: str, 
                          error_message: Optional[str] = None) -> bool:
        """タスクのステータス更新"""
        builder = UpdateQueryBuilder(self.table_name)\
            .set_field("status", status)\
            .set_field("updated_at", datetime.utcnow())
        
        if error_message:
            builder.set_field("error_message", error_message)
        
        builder.where("task_id", "=", task_id)
        query = builder.build()
        
        result = await self.connection.execute(*query)
        return result == "UPDATE 1"

    def _create_entity(self, row: Dict[str, Any]) -> AnalysisTask:
        return AnalysisTask(**row)

class ASTRepository(MongoRepository[ASTData]):
    """ASTリポジトリ"""
    def __init__(self, connection: MongoConnectionManager):
        super().__init__(connection, "ast_collection")

    async def get_ast_by_source(self, source_id: UUID) -> Optional[ASTData]:
        """ソースIDによるAST取得"""
        doc = await self.connection.find_one(
            self.collection_name,
            {"source_id": str(source_id)}
        )
        return self._create_entity(doc) if doc else None

    async def get_asts_by_sources(self, source_ids: List[UUID]) -> List[ASTData]:
        """複数ソースのAST取得"""
        str_ids = [str(id) for id in source_ids]
        docs = await self.connection.find_many(
            self.collection_name,
            {"source_id": {"$in": str_ids}}
        )
        return [self._create_entity(doc) for doc in docs]

    async def add_ast(self, ast_data: ASTData) -> str:
        """ASTの追加"""
        doc = {
            "source_id": str(ast_data.source_id),
            "task_id": str(ast_data.task_id),
            "ast_type": ast_data.ast_type,
            "ast_data": ast_data.ast_data,
            "metadata": ast_data.metadata,
            "created_at": datetime.utcnow()
        }
        return await self.connection.insert_one(self.collection_name, doc)

    def _create_entity(self, doc: Dict[str, Any]) -> ASTData:
        return ASTData(**doc)

class AnalysisResultRepository(MongoRepository[AnalysisResult]):
    """解析結果リポジトリ"""
    def __init__(self, connection: MongoConnectionManager):
        super().__init__(connection, "analysis_results_collection")

    async def get_results_by_source(self, source_id: UUID) -> List[AnalysisResult]:
        """ソースIDによる結果取得"""
        docs = await self.connection.find_many(
            self.collection_name,
            {"source_id": str(source_id)}
        )
        return [self._create_entity(doc) for doc in docs]

    async def store_result(self, result: AnalysisResult) -> str:
        """結果の保存"""
        doc = {
            "result_id": str(result.result_id),
            "source_id": str(result.source_id),
            "analysis_type": result.analysis_type,
            "details": result.details,
            "metrics": result.metrics,
            "issues": result.issues,
            "created_at": datetime.utcnow()
        }
        return await self.connection.insert_one(self.collection_name, doc)

    def _create_entity(self, doc: Dict[str, Any]) -> AnalysisResult:
        return AnalysisResult(**doc)

# /home/administrator/cobol-analyzer/src/db/repositories.py に追加

class MasterRepository(PostgresRepository[T]):
    """マスターデータ用の基底リポジトリクラス"""
    def __init__(self, connection: PostgresConnectionManager, table_name: str):
        super().__init__(connection, table_name)

    async def get_active(self) -> List[T]:
        """有効なマスターデータの取得"""
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("is_active", "=", True)\
            .order_by("created_at", "DESC")\
            .build()
        
        try:
            rows = await self.connection.fetch(query)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get active master data: {str(e)}")
            raise

    async def get_by_category(self, category: str) -> List[T]:
        """カテゴリによるマスターデータの取得"""
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("category", "=", category)\
            .where("is_active", "=", True)\
            .order_by("created_at", "DESC")\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get master data by category: {str(e)}")
            raise

    async def logical_delete(self, id: int) -> bool:
        """論理削除"""
        query = UpdateQueryBuilder()\
            .table(self.table_name)\
            .set_values({
                "is_active": False,
                "updated_at": datetime.utcnow()
            })\
            .where(f"{self.id_column}", "=", id)\
            .build()

        try:
            await self.connection.execute(query)
            return True
        except Exception as e:
            self.logger.error(f"Failed to logical delete master data: {str(e)}")
            raise

class EnvironmentMasterRepository(MasterRepository[BenchmarkMaster]):
    """環境マスター用リポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "environment_master")
        self.id_column = "environment_id"
        self.model_class = BenchmarkMaster

    async def get_by_sub_category(self, category: str, sub_category: str) -> List[BenchmarkMaster]:
        """サブカテゴリによる取得"""
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("category", "=", category)\
            .where("sub_category", "=", sub_category)\
            .where("is_active", "=", True)\
            .order_by("created_at", "DESC")\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get master data by sub category: {str(e)}")
            raise

class BenchmarkMasterRepository(MasterRepository[BenchmarkMaster]):
    """ベンチマークマスター用リポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "benchmark_master")
        self.id_column = "benchmark_id"
        self.model_class = BenchmarkMaster

    async def get_thresholds(self, category: str, metric_name: str) -> Optional[Dict[str, float]]:
        """閾値の取得"""
        query = QueryBuilder()\
            .select(["warning_threshold", "error_threshold"])\
            .from_table(self.table_name)\
            .where("category", "=", category)\
            .where("metric_name", "=", metric_name)\
            .where("is_active", "=", True)\
            .build()

        try:
            row = await self.connection.fetchrow(query)
            if not row:
                return None
            return {
                "warning": row["warning_threshold"],
                "error": row["error_threshold"]
            }
        except Exception as e:
            self.logger.error(f"Failed to get thresholds: {str(e)}")
            raise
            
# 各マスター固有の機能を追加

class SingleAnalysisMasterRepository(MasterRepository[SingleAnalysisMaster]):
    """単一解析マスター用リポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "single_analysis_master")
        self.id_column = "analysis_id"
        self.model_class = SingleAnalysisMaster

    async def get_by_analysis_type(self, analysis_type: str) -> List[SingleAnalysisMaster]:
        """解析タイプによる取得"""
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("analysis_type", "=", analysis_type)\
            .where("is_active", "=", True)\
            .order_by("process_type", "ASC")\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get analysis master by type: {str(e)}")
            raise

    async def get_parameters(self, analysis_type: str, process_type: str) -> List[Dict[str, Any]]:
        """パラメータ設定の取得"""
        query = QueryBuilder()\
            .select(["parameter_name", "parameter_value", "data_type", "is_required"])\
            .from_table(self.table_name)\
            .where("analysis_type", "=", analysis_type)\
            .where("process_type", "=", process_type)\
            .where("is_active", "=", True)\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get analysis parameters: {str(e)}")
            raise

class SummaryAnalysisMasterRepository(MasterRepository[SummaryAnalysisMaster]):
    """サマリ解析マスター用リポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "summary_analysis_master")
        self.id_column = "summary_id"
        self.model_class = SummaryAnalysisMaster

    async def get_by_process_type(self, process_type: str) -> List[SummaryAnalysisMaster]:
        """処理タイプによる取得"""
        query = QueryBuilder()\
            .from_table(self.table_name)\
            .where("process_type", "=", process_type)\
            .where("is_active", "=", True)\
            .order_by("parameter_name", "ASC")\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get summary master by process: {str(e)}")
            raise

class DashboardMasterRepository(MasterRepository[DashboardMaster]):
    """ダッシュボードマスター用リポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "dashboard_master")
        self.id_column = "dashboard_id"
        self.model_class = DashboardMaster

    async def get_layout_config(self, dashboard_type: str) -> List[Dict[str, Any]]:
        """レイアウト設定の取得"""
        query = QueryBuilder()\
            .select(["component_type", "layout_config", "style_config", "display_order"])\
            .from_table(self.table_name)\
            .where("dashboard_type", "=", dashboard_type)\
            .where("is_active", "=", True)\
            .order_by("display_order", "ASC")\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get dashboard layout: {str(e)}")
            raise

    async def get_component_config(self, dashboard_type: str, component_type: str) -> Optional[Dict[str, Any]]:
        """コンポーネント設定の取得"""
        query = QueryBuilder()\
            .select(["parameter_name", "parameter_value", "layout_config", "style_config"])\
            .from_table(self.table_name)\
            .where("dashboard_type", "=", dashboard_type)\
            .where("component_type", "=", component_type)\
            .where("is_active", "=", True)\
            .build()

        try:
            row = await self.connection.fetchrow(query)
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get component config: {str(e)}")
            raise

class DocumentMasterRepository(MasterRepository[DocumentMaster]):
    """ドキュメントマスター用リポジトリ"""
    def __init__(self, connection: PostgresConnectionManager):
        super().__init__(connection, "document_master")
        self.id_column = "document_id" 
        self.model_class = DocumentMaster

    async def get_section_config(self, document_type: str) -> List[Dict[str, Any]]:
        """セクション設定の取得"""
        query = QueryBuilder()\
            .select(["section_type", "parameter_name", "parameter_value", "format_config"])\
            .from_table(self.table_name)\
            .where("document_type", "=", document_type)\
            .where("is_active", "=", True)\
            .order_by("display_order", "ASC")\
            .build()

        try:
            rows = await self.connection.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get section config: {str(e)}")
            raise

    async def get_template_path(self, document_type: str, section_type: str) -> Optional[str]:
        """テンプレートパスの取得"""
        query = QueryBuilder()\
            .select(["template_path"])\
            .from_table(self.table_name)\
            .where("document_type", "=", document_type)\
            .where("section_type", "=", section_type)\
            .where("is_active", "=", True)\
            .build()

        try:
            row = await self.connection.fetchrow(query)
            return row["template_path"] if row else None
        except Exception as e:
            self.logger.error(f"Failed to get template path: {str(e)}")
            raise
            
# これらのリポジトリは:
# マスター共通の機能を継承しながら、各マスター固有の検索・取得機能を実装
# エラーハンドリングとロギングを統一的に実装
# 各マスター特有の設定や構成情報を取得する機能を提供
# しています。さらに実装を続ける場合は、必要に応じて:
# パラメータバリデーション機能の追加
# キャッシュ機能の実装
# バッチ操作の最適化
# トランザクション管理の強化
# などを検討できます。