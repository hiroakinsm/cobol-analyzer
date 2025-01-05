# /home/administrator/cobol-analyzer/src/db/database_access.py

from typing import List, Dict, Optional, Any, Union
from uuid import UUID
import asyncio
import logging
from datetime import datetime, timedelta
from cachetools import TTLCache, LRUCache
import aiocache
from functools import wraps
from dataclasses import dataclass

@dataclass
class CacheConfig:
    """キャッシュ設定"""
    default_ttl: int = 3600  # 1時間
    max_size: int = 1000
    cleanup_interval: int = 300  # 5分
    result_ttl: int = 7200  # 2時間
    task_ttl: int = 1800  # 30分

class DatabaseFunctions:
    """データベースアクセス関数群"""
    def __init__(self, pg_pool, mongodb_client, cache_config: CacheConfig = None):
        self.pg_pool = pg_pool
        self.mongodb_client = mongodb_client
        self.cache_config = cache_config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        
        # キャッシュの初期化
        self.result_cache = TTLCache(
            maxsize=self.cache_config.max_size,
            ttl=self.cache_config.result_ttl
        )
        self.task_cache = TTLCache(
            maxsize=self.cache_config.max_size,
            ttl=self.cache_config.task_ttl
        )
        self.query_cache = LRUCache(maxsize=self.cache_config.max_size)
        
        # 分散キャッシュの初期化
        self.distributed_cache = aiocache.Cache.from_url("redis://localhost")
        
        # キャッシュクリーンアップタスクの開始
        asyncio.create_task(self._cache_cleanup_loop())

    def cache_result(ttl: int = None):
        """結果キャッシュデコレータ"""
        def decorator(func):
            @wraps(func)
            async def wrapper(self, *args, **kwargs):
                cache_key = f"{func.__name__}:{args}:{kwargs}"
                
                # ローカルキャッシュチェック
                if cache_key in self.result_cache:
                    return self.result_cache[cache_key]
                
                # 分散キャッシュチェック
                cached = await self.distributed_cache.get(cache_key)
                if cached:
                    self.result_cache[cache_key] = cached
                    return cached
                
                # 結果の取得と保存
                result = await func(self, *args, **kwargs)
                
                if result:
                    cache_ttl = ttl or self.cache_config.default_ttl
                    self.result_cache[cache_key] = result
                    await self.distributed_cache.set(
                        cache_key,
                        result,
                        ttl=cache_ttl
                    )
                
                return result
            return wrapper
        return decorator

    async def _cache_cleanup_loop(self):
        """キャッシュクリーンアップループ"""
        while True:
            try:
                await asyncio.sleep(self.cache_config.cleanup_interval)
                self._cleanup_expired_cache()
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {str(e)}")

    def _cleanup_expired_cache(self):
        """期限切れキャッシュのクリーンアップ"""
        current_time = datetime.utcnow()
        
        # TTLキャッシュは自動的にクリーンアップされるが、
        # 明示的なクリーンアップも実行
        self.result_cache.expire()
        self.task_cache.expire()

    @cache_result(ttl=3600)
    async def get_task_results(self, source_id: UUID) -> Dict[str, Any]:
        """解析タスクの結果を取得"""
        try:
            async with self.pg_pool.acquire() as conn:
                results = await conn.fetch("""
                    SELECT r.*, t.task_type, t.analysis_config
                    FROM analysis_results_partitioned r
                    JOIN analysis_tasks_partitioned t ON r.task_id = t.task_id
                    WHERE r.source_id = $1
                    ORDER BY r.created_at DESC
                """, source_id)

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
                    await conn.execute("""
                        INSERT INTO analysis_results_partitioned (
                            result_id, task_id, source_id, analysis_type,
                            status, mongodb_collection, mongodb_document_id,
                            summary_data, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
                    """, UUID(...), task_id, source_id, results['type'],
                        'completed', 'ast_collection', str(source_id),
                        results['summary'], datetime.utcnow())

            await self.mongodb_client.ast_collection.update_one(
                {"source_id": str(source_id)},
                {"$set": ast_data},
                upsert=True
            )

            # キャッシュの無効化
            cache_key = f"get_task_results:{source_id}"
            self.result_cache.pop(cache_key, None)
            await self.distributed_cache.delete(cache_key)
            
        except Exception as e:
            self.logger.error(f"Error storing analysis results: {str(e)}")
            raise

    @cache_result(ttl=1800)
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
                    await conn.execute("""
                        DELETE FROM analysis_results_partitioned
                        WHERE created_at < $1
                    """, cutoff_date)

                    await conn.execute("""
                        DELETE FROM analysis_tasks_partitioned
                        WHERE created_at < $1
                    """, cutoff_date)

            await self.mongodb_client.ast_collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })

            # 関連キャッシュの一括クリア
            self.result_cache.clear()
            self.task_cache.clear()
            await self.distributed_cache.clear()
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
            raise

    @cache_result(ttl=300)
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

    async def cleanup(self):
        """リソースのクリーンアップ"""
        await self.distributed_cache.close()