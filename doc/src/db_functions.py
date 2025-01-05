# Implementation Server: 172.16.0.27 (Application Server)
# Path: /home/administrator/cobol-analyzer/src/database/db_functions.py

# Database Functions.py を実装
class DatabaseFunctions:
    def __init__(self, pg_pool, mongodb_client):
        self.pg_pool = pg_pool
        self.mongodb_client = mongodb_client
        self.logger = logging.getLogger(__name__)

    async def get_task_results(self, source_id: UUID) -> Dict[str, Any]:
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
                        'completed', 'ast_collection_2', str(source_id),
                        results['summary'], datetime.utcnow())

            # MongoDBにASTデータを保存
            await self.mongodb_client.ast_collection_2.update_one(
                {"source_id": str(source_id)},
                {"$set": ast_data},
                upsert=True
            )
        except Exception as e:
            self.logger.error(f"Error storing analysis results: {str(e)}")
            raise