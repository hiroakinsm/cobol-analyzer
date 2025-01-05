# /home/administrator/cobol-analyzer/src/db/connection_managers.py

from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncpg
import motor.motor_asyncio
import logging
from contextlib import asynccontextmanager
import yaml
from pathlib import Path

class ConnectionConfig:
    """データベース接続設定"""
    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        with open(config_path) as f:
            return yaml.safe_load(f)

    def get_postgres_config(self) -> Dict[str, Any]:
        """PostgreSQL設定の取得"""
        return self.config.get('postgres', {})

    def get_mongodb_config(self) -> Dict[str, Any]:
        """MongoDB設定の取得"""
        return self.config.get('mongodb', {})

    def get_pool_config(self) -> Dict[str, Any]:
        """プール設定の取得"""
        return self.config.get('pool_settings', {
            'min_connections': 10,
            'max_connections': 100,
            'max_queries': 50000,
            'setup_timeout': 60,
            'init_timeout': 30
        })

class PostgresConnectionManager:
    """PostgreSQL接続管理"""
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
        self.pool_stats = {
            'created_connections': 0,
            'active_connections': 0,
            'pool_status': 'initialized'
        }

    async def initialize(self):
        """コネクションプールの初期化"""
        try:
            postgres_config = self.config.get_postgres_config()
            pool_config = self.config.get_pool_config()

            self.pool = await asyncpg.create_pool(
                host=postgres_config["host"],
                port=postgres_config["port"],
                database=postgres_config["database"],
                user=postgres_config["user"],
                password=postgres_config["password"],
                min_size=pool_config["min_connections"],
                max_size=pool_config["max_connections"],
                max_queries=pool_config["max_queries"],
                setup=self._init_connection,
                setup_timeout=pool_config["setup_timeout"],
                init=self._init_pool,
                init_timeout=pool_config["init_timeout"]
            )
            self.pool_stats['pool_status'] = 'active'
            self.logger.info("PostgreSQL connection pool initialized")

        except Exception as e:
            self.pool_stats['pool_status'] = 'failed'
            self.logger.error(f"Failed to initialize PostgreSQL pool: {str(e)}")
            raise

    async def _init_connection(self, connection: asyncpg.Connection):
        """個別コネクションの初期化"""
        await connection.set_type_codec(
            'jsonb',
            encoder=lambda value: json.dumps(value),
            decoder=lambda value: json.loads(value),
            schema='pg_catalog'
        )
        self.pool_stats['created_connections'] += 1

    async def _init_pool(self, connection: asyncpg.Connection):
        """プール全体の初期化"""
        await connection.execute("""
            SET statement_timeout = '30s';
            SET idle_in_transaction_session_timeout = '60s';
        """)

    async def close(self):
        """接続のクローズ"""
        if self.pool:
            self.pool_stats['pool_status'] = 'closing'
            await self.pool.close()
            self.pool_stats['pool_status'] = 'closed'
            self.logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        async with self.pool.acquire() as connection:
            self.pool_stats['active_connections'] += 1
            try:
                async with connection.transaction():
                    yield connection
            finally:
                self.pool_stats['active_connections'] -= 1

    async def execute(self, query: str, *args) -> str:
        """クエリの実行"""
        async with self.pool.acquire() as connection:
            self.pool_stats['active_connections'] += 1
            try:
                return await connection.execute(query, *args)
            finally:
                self.pool_stats['active_connections'] -= 1

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """複数行の取得"""
        async with self.pool.acquire() as connection:
            self.pool_stats['active_connections'] += 1
            try:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
            finally:
                self.pool_stats['active_connections'] -= 1

    async def get_pool_stats(self) -> Dict[str, Any]:
        """プール統計の取得"""
        if self.pool:
            return {
                **self.pool_stats,
                'total_connections': len(self.pool._holders),
                'free_connections': len(self.pool._free),
                'pending_connections': len(self.pool._pending)
            }
        return self.pool_stats