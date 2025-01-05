# /home/administrator/cobol-analyzer/src/repository/repository_implementation.py

from typing import Dict, List, Optional, Any, Generic, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import UUID
import logging
from dataclasses import dataclass
import asyncpg
from collections import defaultdict
import json

T = TypeVar('T')

class PostgresRepository(Generic[T]):
    """PostgreSQL用リポジトリ基底クラス"""
    def __init__(self, db_manager: asyncpg.Pool, model_class: type[T]):
        self.db = db_manager
        self.model_class = model_class
        self.table_name = model_class.__name__.lower()
        self.logger = logging.getLogger(__name__)

    async def get(self, id: Any) -> Optional[T]:
        """IDによるエンティティ取得"""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        try:
            row = await self.db.fetchrow(query, id)
            return self.model_class(**row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get {self.table_name} by id {id}: {str(e)}")
            raise

    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        """フィルタ条件によるエンティティ取得"""
        conditions = " AND ".join(f"{k} = ${i+1}" for i, k in enumerate(filter_dict.keys()))
        query = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        try:
            rows = await self.db.fetch(query, *filter_dict.values())
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get many {self.table_name}: {str(e)}")
            raise

    async def add(self, entity: T) -> Any:
        """エンティティの追加"""
        fields = entity.__dict__.keys()
        placeholders = [f"${i+1}" for i in range(len(fields))]
        query = f"""
            INSERT INTO {self.table_name} ({','.join(fields)})
            VALUES ({','.join(placeholders)})
            RETURNING id
        """
        try:
            return await self.db.fetchrow(query, *entity.__dict__.values())
        except Exception as e:
            self.logger.error(f"Failed to add {self.table_name}: {str(e)}")
            raise

    async def update(self, entity: T) -> bool:
        """エンティティの更新"""
        fields = [f for f in entity.__dict__.keys() if f != 'id']
        sets = [f"{f} = ${i+2}" for i, f in enumerate(fields)]
        query = f"""
            UPDATE {self.table_name}
            SET {','.join(sets)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        try:
            result = await self.db.execute(query, entity.id, *[getattr(entity, f) for f in fields])
            return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to update {self.table_name}: {str(e)}")
            raise

    async def delete(self, id: Any) -> bool:
        """エンティティの削除"""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        try:
            result = await self.db.execute(query, id)
            return result == "DELETE 1"
        except Exception as e:
            self.logger.error(f"Failed to delete {self.table_name}: {str(e)}")
            raise

class AnalysisTaskRepository(PostgresRepository['AnalysisTask']):
    """解析タスクリポジトリ"""
    async def get_pending_tasks(self) -> List['AnalysisTask']:
        """保留中タスクの取得"""
        query = """
            SELECT * FROM analysis_tasks_partitioned 
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
        """
        try:
            rows = await self.db.fetch(query)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get pending tasks: {str(e)}")
            raise

    async def update_status(self, task_id: UUID, status: str) -> bool:
        """タスクステータスの更新"""
        query = """
            UPDATE analysis_tasks_partitioned
            SET 
                status = $1,
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE 
                    WHEN $1 IN ('completed', 'failed') THEN CURRENT_TIMESTAMP
                    ELSE completed_at
                END
            WHERE task_id = $2
        """
        try:
            result = await self.db.execute(query, status, task_id)
            return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to update task status: {str(e)}")
            raise

class AnalysisResultRepository(PostgresRepository['AnalysisResult']):
    """解析結果リポジトリ"""
    async def get_results_by_source(self, source_id: UUID) -> List['AnalysisResult']:
        """ソースIDによる結果取得"""
        query = """
            SELECT * FROM analysis_results_partitioned
            WHERE source_id = $1
            ORDER BY created_at DESC
        """
        try:
            rows = await self.db.fetch(query, source_id)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get results by source: {str(e)}")
            raise

    async def store_stage_result(self, 
                               task_id: UUID, 
                               stage: str, 
                               result: Dict[str, Any]) -> UUID:
        """ステージ結果の保存"""
        query = """
            INSERT INTO analysis_results_partitioned (
                result_id, task_id, source_id, analysis_type,
                status, results, execution_time, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
            RETURNING result_id
        """
        try:
            result_id = UUID()
            await self.db.execute(
                query,
                result_id,
                task_id,
                result["source_id"],
                stage,
                "completed",
                json.dumps(result),
                result.get("execution_time", 0)
            )
            return result_id
        except Exception as e:
            self.logger.error(f"Failed to store stage result: {str(e)}")
            raise

class BenchmarkResultRepository(PostgresRepository['BenchmarkResult']):
    """ベンチマーク結果リポジトリ"""
    async def get_benchmarks_by_category(self, category: str) -> List['BenchmarkResult']:
        """カテゴリによるベンチマーク結果取得"""
        query = """
            SELECT * FROM benchmark_results_partitioned
            WHERE category = $1
            ORDER BY created_at DESC
        """
        try:
            rows = await self.db.fetch(query, category)
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get benchmarks by category: {str(e)}")
            raise

class AnalysisLogRepository(PostgresRepository['AnalysisLog']):
    """解析ログリポジトリ"""
    async def add_log(self, log_entry: 'AnalysisLog') -> None:
        """ログエントリの追加"""
        query = """
            INSERT INTO analysis_logs (
                task_id, source_id, log_level, component,
                message, details, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
        """
        try:
            await self.db.execute(
                query,
                log_entry.task_id,
                log_entry.source_id,
                log_entry.level,
                log_entry.component,
                log_entry.message,
                json.dumps(log_entry.details) if log_entry.details else None
            )
        except Exception as e:
            self.logger.error(f"Failed to add log entry: {str(e)}")
            raise