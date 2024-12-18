from typing import List, Dict, Optional, Any, Union
from uuid import UUID
import asyncio
import logging
from datetime import datetime, timedelta

class DatabaseFunctions:
    """データベースアクセス関数群"""
    def __init__(self, pg_pool, mongodb_client):
        self.pg_pool = pg_pool
        self.mongodb_client = mongodb_client
        self.logger = logging.getLogger(__name__)

    async def get_task_results(self, source_id: UUID) -> Dict[str, Any]:
        """解析タスクの結果を取得"""
        try:
            async with self.pg_pool.acquire() as conn:
                # 解析結果の取得
                results = await conn.fetch("""
                    SELECT r.*, t.task_type, t.analysis_config
                    FROM analysis_results_partitioned r
                    JOIN analysis_tasks_partitioned t ON r.task_id = t.task_id
                    WHERE r.source_id = $1
                    ORDER BY r.created_at DESC
                """, source_id)

                # MongoDBからASTデータを取得
                ast_data = await self.mongodb_client.ast_collection.find_one(
                    {"source_id": str(source_id)}
                )

                return {
                    "results": [dict(r) for r in results],
                    "ast_data": ast_data
                }
        except Exception as e:
            self.logger.error(f"Error getting task results: {str(e)}")
            raise

    async def store_analysis_results(self,
                                   source_id: UUID,
                                   task_id: UUID,
                                   results: Dict[str, Any],
                                   ast_data: Dict[str, Any]) -> None:
        """解析結果の保存"""
        try:
            async with self.pg_pool.acquire() as conn:
                async with conn.transaction():
                    # PostgreSQLに結果を保存
                    await conn.execute("""
                        INSERT INTO analysis_results_partitioned (
                            result_id, task_id, source_id, analysis_type,
                            status, mongodb_collection, mongodb_document_id,
                            summary_data, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
                    """, UUID(...), task_id, source_id, results['type'],
                        'completed', 'ast_collection', str(source_id),
                        results['summary'], datetime.utcnow())

            # MongoDBにASTデータを保存
            await self.mongodb_client.ast_collection.update_one(
                {"source_id": str(source_id)},
                {"$set": ast_data},
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Error storing analysis results: {str(e)}")
            raise

    async def get_summary_data(self,
                             source_ids: List[UUID],
                             analysis_type: str) -> List[Dict[str, Any]]:
        """複数ソースのサマリデータ取得"""
        try:
            async with self.pg_pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT r.source_id, r.summary_data, r.created_at
                    FROM analysis_results_partitioned r
                    WHERE r.source_id = ANY($1)
                    AND r.analysis_type = $2
                    AND r.status = 'completed'
                    ORDER BY r.created_at DESC
                """, source_ids, analysis_type)

                return [dict(r) for r in results]
        except Exception as e:
            self.logger.error(f"Error getting summary data: {str(e)}")
            raise

    async def cleanup_old_data(self, retention_days: int = 90) -> None:
        """古いデータのクリーンアップ"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            async with self.pg_pool.acquire() as conn:
                async with conn.transaction():
                    # PostgreSQLの古いデータを削除
                    await conn.execute("""
                        DELETE FROM analysis_results_partitioned
                        WHERE created_at < $1
                    """, cutoff_date)

                    await conn.execute("""
                        DELETE FROM analysis_tasks_partitioned
                        WHERE created_at < $1
                    """, cutoff_date)

            # MongoDBの古いデータを削除
            await self.mongodb_client.ast_collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            raise

    async def get_task_status(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """タスクのステータス取得"""
        try:
            async with self.pg_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT status, priority, started_at, completed_at, error_message
                    FROM analysis_tasks_partitioned
                    WHERE task_id = $1
                """, task_id)

                return dict(result) if result else None
        except Exception as e:
            self.logger.error(f"Error getting task status: {str(e)}")
            raise