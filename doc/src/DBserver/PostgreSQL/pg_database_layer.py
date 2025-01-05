# /home/administrator/cobol-analyzer/src/db/database_layer.py

from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
import asyncpg
import logging
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# データベース設定
class DatabaseConfig:
    def __init__(
        self,
        host: str = "172.16.0.13",
        port: int = 5432,
        database: str = "cobol_analysis_db",
        user: str = "cobana_admin",
        password: str = "Kanami1001!",
        min_connections: int = 10,
        max_connections: int = 100,
        command_timeout: int = 30,
        connection_timeout: int = 60,
        pool_recycle: int = 3600
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        self.connection_timeout = connection_timeout
        self.pool_recycle = pool_recycle

class DatabaseError(Exception):
    """データベースエラーの基底クラス"""
    def __init__(self, message: str = "Database operation error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return self.message

class ConnectionError(DatabaseError):
    """接続エラー"""
    def __init__(self, message: str = "Database connection error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"Connection Error: {self.message}"

class TransactionError(DatabaseError):
    """トランザクションエラー"""
    def __init__(self, message: str = "Database transaction error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"Transaction Error: {self.message}"

class QueryError(DatabaseError):
    """クエリエラー"""
    def __init__(self, message: str = "Database query error occurred"):
        self.message = message
        super().__init__(self.message)
    
    def __str__(self):
        return f"Query Error: {self.message}"

T = TypeVar('T')

class PostgresManager:
    """PostgreSQLデータベース管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
        self.connection_stats = {
            'status': 'initialized',
            'active_connections': 0,
            'total_queries': 0,
            'error_count': 0
        }

    async def initialize(self):
        """コネクションプールの初期化"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=self.config.command_timeout,
                server_settings={
                    'application_name': 'cobol_analyzer',
                    'statement_timeout': f'{self.config.command_timeout * 1000}',
                    'idle_in_transaction_session_timeout': '3600000'
                }
            )
            self.connection_stats['status'] = 'active'
            self.logger.info("PostgreSQL connection pool initialized successfully")
        except Exception as e:
            self.connection_stats['status'] = 'failed'
            self.connection_stats['error_count'] += 1
            self.logger.error(f"Failed to initialize PostgreSQL pool: {str(e)}")
            raise ConnectionError(f"Database connection failed: {str(e)}")

    async def close(self):
        """コネクションプールのクローズ"""
        if self.pool:
            self.connection_stats['status'] = 'closing'
            await self.pool.close()
            self.connection_stats['status'] = 'closed'
            self.logger.info("PostgreSQL connection pool closed")

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理"""
        if not self.pool:
            raise ConnectionError("Database connection not initialized")

        async with self.pool.acquire() as connection:
            self.connection_stats['active_connections'] += 1
            try:
                async with connection.transaction():
                    yield connection
            except Exception as e:
                self.connection_stats['error_count'] += 1
                self.logger.error(f"Transaction error: {str(e)}")
                raise TransactionError(f"Transaction failed: {str(e)}")
            finally:
                self.connection_stats['active_connections'] -= 1

    async def execute(self, query: str, *args) -> str:
        """クエリの実行"""
        if not self.pool:
            raise ConnectionError("Database connection not initialized")

        try:
            self.connection_stats['total_queries'] += 1
            async with self.pool.acquire() as connection:
                return await connection.execute(query, *args)
        except Exception as e:
            self.connection_stats['error_count'] += 1
            self.logger.error(f"Query execution error: {str(e)}")
            raise QueryError(f"Query execution failed: {str(e)}")

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """データの取得"""
        if not self.pool:
            raise ConnectionError("Database connection not initialized")

        try:
            self.connection_stats['total_queries'] += 1
            async with self.pool.acquire() as connection:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            self.connection_stats['error_count'] += 1
            self.logger.error(f"Query fetch error: {str(e)}")
            raise QueryError(f"Query fetch failed: {str(e)}")

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """1行データの取得"""
        if not self.pool:
            raise ConnectionError("Database connection not initialized")

        try:
            self.connection_stats['total_queries'] += 1
            async with self.pool.acquire() as connection:
                row = await connection.fetchrow(query, *args)
                return dict(row) if row else None
        except Exception as e:
            self.connection_stats['error_count'] += 1
            self.logger.error(f"Query fetchrow error: {str(e)}")
            raise QueryError(f"Query fetchrow failed: {str(e)}")

    async def get_connection_stats(self) -> Dict[str, Any]:
        """接続統計の取得"""
        stats = self.connection_stats.copy()
        if self.pool:
            stats.update({
                'pool_size': len(self.pool._holders),
                'free_connections': len(self.pool._free),
                'active_transactions': len(self.pool._holders) - len(self.pool._free)
            })
        return stats

    async def check_connection_health(self) -> bool:
        """接続の健全性チェック"""
        try:
            async with self.pool.acquire() as connection:
                await connection.execute('SELECT 1')
                return True
        except Exception as e:
            self.logger.error(f"Connection health check failed: {str(e)}")
            return False

class PostgresHealthCheck:
    """PostgreSQL健全性チェック"""
    def __init__(self, db_manager: PostgresManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)

    async def check_health(self) -> Dict[str, Any]:
        """健全性チェックの実行"""
        health_status = {
            'status': 'healthy',
            'details': {},
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            # 接続チェック
            connection_healthy = await self.db_manager.check_connection_health()
            health_status['details']['connection'] = {
                'healthy': connection_healthy,
                'message': 'Connection is working' if connection_healthy else 'Connection failed'
            }

            # 接続統計の取得
            stats = await self.db_manager.get_connection_stats()
            health_status['details']['stats'] = stats

            # エラー率の計算
            if stats['total_queries'] > 0:
                error_rate = stats['error_count'] / stats['total_queries']
                health_status['details']['error_rate'] = error_rate
                if error_rate > 0.05:  # 5%以上のエラー率は警告
                    health_status['status'] = 'warning'

            return health_status

        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'details': {'error': str(e)},
                'timestamp': datetime.utcnow().isoformat()
            }

# メインエントリーポイント
async def main():
    # データベース設定の作成
    config = DatabaseConfig()
    
    # データベースマネージャーの初期化
    db_manager = PostgresManager(config)
    await db_manager.initialize()
    
    try:
        # 健全性チェッカーの作成
        health_checker = PostgresHealthCheck(db_manager)
        
        # 健全性チェックの実行
        health_status = await health_checker.check_health()
        print(f"Database health status: {health_status}")
        
    finally:
        # データベース接続のクローズ
        await db_manager.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())