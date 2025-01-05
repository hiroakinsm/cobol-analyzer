from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta
import asyncio
import json
import aioredis
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """キャッシュの設定"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    ttl: int = 3600  # デフォルトの有効期限（秒）
    prefix: str = "cobol_analyzer:"

class CacheManager:
    """解析結果のキャッシュを管理するクラス"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        self._cache_keys = {
            'dashboard': 'dashboard_data',
            'metrics': 'metrics_summary',
            'trends': 'trend_data',
            'quality': 'quality_indicators',
            'risks': 'risk_analysis'
        }

    async def initialize(self):
        """Redisクライアントの初期化"""
        try:
            self.redis = await aioredis.create_redis_pool(
                f'redis://{self.config.host}:{self.config.port}',
                db=self.config.db,
                encoding='utf-8'
            )
            logger.info("Redisクライアントを初期化しました")
        except Exception as e:
            logger.error(f"Redisクライアント初期化でエラー: {str(e)}")
            raise

    async def close(self):
        """Redisクライアントのクローズ"""
        if self.redis:
            self.redis.close()
            await self.redis.wait_closed()
            logger.info("Redisクライアントをクローズしました")

    async def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュからデータを取得"""
        try:
            full_key = f"{self.config.prefix}{self._cache_keys.get(cache_key, cache_key)}"
            data = await self.redis.get(full_key)
            
            if data:
                cached_data = json.loads(data)
                # キャッシュの有効期限をチェック
                if self._is_cache_valid(cached_data):
                    return cached_data.get('data')
                else:
                    await self.invalidate_cache(cache_key)
            
            return None
        except Exception as e:
            logger.error(f"キャッシュ取得でエラー: {str(e)}")
            return None

    async def set_cached_data(self, cache_key: str, data: Dict[str, Any], ttl: int = None):
        """データをキャッシュに保存"""
        try:
            full_key = f"{self.config.prefix}{self._cache_keys.get(cache_key, cache_key)}"
            cache_data = {
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'ttl': ttl or self.config.ttl
            }
            
            await self.redis.set(
                full_key,
                json.dumps(cache_data),
                expire=ttl or self.config.ttl
            )
        except Exception as e:
            logger.error(f"キャッシュ保存でエラー: {str(e)}")

    async def invalidate_cache(self, cache_key: str = None):
        """キャッシュの無効化"""
        try:
            if cache_key:
                full_key = f"{self.config.prefix}{self._cache_keys.get(cache_key, cache_key)}"
                await self.redis.delete(full_key)
            else:
                # 全てのキャッシュを削除
                pattern = f"{self.config.prefix}*"
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"キャッシュ無効化でエラー: {str(e)}")

    async def refresh_cache(self, dashboard_generator):
        """キャッシュの更新"""
        try:
            # ダッシュボードデータの生成
            dashboard_data = await dashboard_generator.generate_dashboard_data()
            
            # 各コンポーネントのキャッシュを更新
            await self.set_cached_data('dashboard', dashboard_data)
            await self.set_cached_data('metrics', dashboard_data['metrics'])
            await self.set_cached_data('trends', dashboard_data['trends'])
            await self.set_cached_data('quality', dashboard_data['quality'])
            await self.set_cached_data('risks', dashboard_data['risks'])
            
            logger.info("キャッシュを更新しました")
        except Exception as e:
            logger.error(f"キャッシュ更新でエラー: {str(e)}")

    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """キャッシュの有効性をチェック"""
        try:
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            ttl = cached_data.get('ttl', self.config.ttl)
            return datetime.now() - cache_time < timedelta(seconds=ttl)
        except Exception as e:
            logger.error(f"キャッシュ有効性チェックでエラー: {str(e)}")
            return False

    async def start_cache_refresh_task(self, dashboard_generator, interval: int = 3600):
        """定期的なキャッシュ更新タスクの開始"""
        while True:
            try:
                await self.refresh_cache(dashboard_generator)
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"定期キャッシュ更新でエラー: {str(e)}")
                await asyncio.sleep(60)  # エラー時は1分待機 