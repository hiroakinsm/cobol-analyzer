# /home/administrator/cobol-analyzer/src/db/database_access.py

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from uuid import UUID
import logging
from typing import Dict, List, Optional, Any
import asyncpg
from contextlib import asynccontextmanager
from cachetools import TTLCache

class PostgresDatabaseAccess:
    """PostgreSQLデータベースアクセス"""
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        self.logger = logging.getLogger(__name__)
        self.cache = TTLCache(maxsize=1000, ttl=3600)  # 1時間のキャッシュ

    async def get_analysis_results(self, source_id: UUID) -> Dict[str, Any]:
        """解析結果の取得"""
        try:
            cache_key = f"analysis_results_{source_id}"
            if cache_key in self.cache:
                return self.cache[cache_key]

            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT r.*, t.task_type, t.analysis_config
                    FROM analysis_results_partitioned r
                    JOIN analysis_tasks_partitioned t ON r.task_id = t.task_id
                    WHERE r.source_id = $1
                    ORDER BY r.created_at DESC
                """, source_id)

                formatted_results = [dict(r) for r in results]
                self.cache[cache_key] = formatted_results
                return formatted_results

        except Exception as e:
            self.logger.error(f"Error retrieving analysis results: {str(e)}")
            raise

    async def store_analysis_result(self, result: Dict[str, Any]) -> UUID:
        """解析結果の保存"""
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    result_id = UUID()
                    await conn.execute("""
                        INSERT INTO analysis_results_partitioned (
                            result_id, task_id, source_id, analysis_type,
                            status, mongodb_collection, mongodb_document_id,
                            summary_data, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
                    """, result_id, result['task_id'], result['source_id'],
                        result['type'], 'completed', result['collection'],
                        str(result['document_id']), result['summary'],
                        datetime.utcnow())

                    # キャッシュの無効化
                    cache_key = f"analysis_results_{result['source_id']}"
                    if cache_key in self.cache:
                        del self.cache[cache_key]

                    return result_id

        except Exception as e:
            self.logger.error(f"Error storing analysis result: {str(e)}")
            raise

    async def get_analysis_tasks(self, source_id: Optional[UUID] = None, 
                               status: Optional[str] = None) -> List[Dict[str, Any]]:
        """解析タスクの取得"""
        try:
            query = """
                SELECT * FROM analysis_tasks_partitioned
                WHERE 1=1
            """
            params = []
            
            if source_id:
                query += " AND source_id = $1"
                params.append(source_id)
            
            if status:
                query += f" AND status = ${len(params) + 1}"
                params.append(status)
                
            query += " ORDER BY created_at DESC"

            async with self.pool.acquire() as conn:
                results = await conn.fetch(query, *params)
                return [dict(r) for r in results]

        except Exception as e:
            self.logger.error(f"Error retrieving analysis tasks: {str(e)}")
            raise

    async def update_task_status(self, task_id: UUID, status: str, 
                               error_message: Optional[str] = None) -> bool:
        """タスクステータスの更新"""
        try:
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE analysis_tasks_partitioned
                    SET status = $1,
                        error_message = $2,
                        updated_at = $3,
                        completed_at = CASE 
                            WHEN $1 IN ('completed', 'failed') THEN $3
                            ELSE completed_at
                        END
                    WHERE task_id = $4
                """, status, error_message, datetime.utcnow(), task_id)
                
                return result == "UPDATE 1"

        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}")
            raise

    async def get_summary_data(self, source_ids: List[UUID], 
                             summary_type: str) -> List[Dict[str, Any]]:
        """サマリデータの取得"""
        try:
            async with self.pool.acquire() as conn:
                results = await conn.fetch("""
                    WITH latest_results AS (
                        SELECT DISTINCT ON (source_id) *
                        FROM analysis_results_partitioned
                        WHERE source_id = ANY($1)
                        AND analysis_type = $2
                        ORDER BY source_id, created_at DESC
                    )
                    SELECT r.*, s.file_path, s.file_type
                    FROM latest_results r
                    JOIN analysis_sources s ON r.source_id = s.source_id
                    ORDER BY r.created_at DESC
                """, source_ids, summary_type)

                return [dict(r) for r in results]

        except Exception as e:
            self.logger.error(f"Error retrieving summary data: {str(e)}")
            raise

    async def cleanup_old_data(self, retention_days: int = 90) -> None:
        """古いデータの削除"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # 古い解析結果の削除
                    await conn.execute("""
                        DELETE FROM analysis_results_partitioned
                        WHERE created_at < $1
                    """, cutoff_date)

                    # 古い解析タスクの削除
                    await conn.execute("""
                        DELETE FROM analysis_tasks_partitioned
                        WHERE created_at < $1
                        AND status IN ('completed', 'failed')
                    """, cutoff_date)

                    # キャッシュのクリア
                    self.cache.clear()

        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            raise

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                yield connection