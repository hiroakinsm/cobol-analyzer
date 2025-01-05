# /home/administrator/cobol-analyzer/src/repository/repositories.py

from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
import logging
from abc import ABC, abstractmethod

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """リポジトリの基底クラス"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """単一エンティティの取得"""
        raise NotImplementedError()

    @abstractmethod
    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        """複数エンティティの取得"""
        raise NotImplementedError()

    @abstractmethod
    async def add(self, entity: T) -> Any:
        """エンティティの追加"""
        raise NotImplementedError()

    @abstractmethod
    async def update(self, entity: T) -> bool:
        """エンティティの更新"""
        raise NotImplementedError()

    @abstractmethod
    async def delete(self, id: Any) -> bool:
        """エンティティの削除"""
        raise NotImplementedError()

class PostgresRepository(BaseRepository[T]):
    """PostgreSQL用リポジトリ基底クラス"""
    def __init__(self, connection, table_name: str):
        super().__init__()
        self.connection = connection
        self.table_name = table_name

    async def get(self, id: Any) -> Optional[T]:
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        
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
        raise NotImplementedError()

class MasterRepository(PostgresRepository[T]):
    """マスターデータ用の基底リポジトリクラス"""
    def __init__(self, connection, table_name: str):
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

class EnvironmentMasterRepository(MasterRepository[EnvironmentMaster]):
    """環境マスター用リポジトリ"""
    def __init__(self, connection):
        super().__init__(connection, "environment_master")
        self.id_column = "environment_id"
        self.model_class = EnvironmentMaster

    async def get_by_sub_category(self, category: str, sub_category: str) -> List[EnvironmentMaster]:
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

    def _create_entity(self, row: Dict[str, Any]) -> EnvironmentMaster:
        return EnvironmentMaster(**row)

class BenchmarkMasterRepository(MasterRepository[BenchmarkMaster]):
    """ベンチマークマスター用リポジトリ"""
    def __init__(self, connection):
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

    def _create_entity(self, row: Dict[str, Any]) -> BenchmarkMaster:
        return BenchmarkMaster(**row)

class SingleAnalysisMasterRepository(MasterRepository[SingleAnalysisMaster]):
    """単一解析マスター用リポジトリ"""
    def __init__(self, connection):
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

    def _create_entity(self, row: Dict[str, Any]) -> SingleAnalysisMaster:
        return SingleAnalysisMaster(**row)

class SummaryAnalysisMasterRepository(MasterRepository[SummaryAnalysisMaster]):
    """サマリ解析マスター用リポジトリ"""
    def __init__(self, connection):
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

    def _create_entity(self, row: Dict[str, Any]) -> SummaryAnalysisMaster:
        return SummaryAnalysisMaster(**row)