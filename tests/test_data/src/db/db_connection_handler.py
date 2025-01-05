from typing import Dict, Any, Optional
import asyncpg
import motor.motor_asyncio
from config.database import DatabaseConfig
from contextlib import asynccontextmanager
from datetime import datetime
import logging
import asyncio
from functools import wraps
from .db_connection_monitor import DatabaseMonitor
import time

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_operation(max_attempts: int = 3, delay: float = 1.0):
    """データベース操作のリトライデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except DatabaseError as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (2 ** attempt)  # 指数バックオフ
                        logger.warning(f"操作失敗 (試行 {attempt + 1}/{max_attempts}): {str(e)}")
                        logger.info(f"{wait_time}秒後にリトライします")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"最大リトライ回数に到達: {str(e)}")
                        raise last_error
            return None
        return wrapper
    return decorator

class DatabaseError(Exception):
    """データベース操作に関するカスタム例外"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        self.timestamp = datetime.now()
        logger.error(f"データベースエラー: {message}", exc_info=original_error)

class PostgresHandler:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        logger.info("PostgresHandlerを初期化しました")

    @retry_operation()
    async def initialize(self):
        """PostgreSQL接続プールの初期化"""
        try:
            logger.info("PostgreSQL接続プールを初期化中...")
            self.pool = await asyncpg.create_pool(
                host=self.config.pg_host,
                port=self.config.pg_port,
                user=self.config.pg_user,
                password=self.config.pg_password,
                database=self.config.pg_database,
                min_size=5,
                max_size=20,
                command_timeout=60.0,
                timeout=10.0
            )
            logger.info("PostgreSQL接続プールの初期化が完了しました")
        except Exception as e:
            raise DatabaseError("PostgreSQL接続プールの初期化に失敗しました", e)

    @asynccontextmanager
    async def transaction(self):
        """トランザクション管理用のコンテキストマネージャー"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                logger.debug("新しいトランザクションを開始しました")
                try:
                    yield conn
                    logger.debug("トランザクションをコミットしました")
                except Exception as e:
                    logger.error("トランザクションをロールバックしました", exc_info=e)
                    raise

    @retry_operation()
    async def fetch_metadata(self, source_id: str) -> Dict[str, Any]:
        """メタデータの取得"""
        try:
            logger.info(f"メタデータを取得中: {source_id}")
            async with self.transaction() as conn:
                query = """
                    SELECT m.* 
                    FROM metadata m 
                    WHERE m.source_id = $1
                """
                result = await conn.fetchrow(query, source_id)
                if result:
                    logger.info(f"メタデータの取得が完了しました: {source_id}")
                else:
                    logger.warning(f"メタデータが見つかりません: {source_id}")
                return dict(result) if result else None
        except asyncpg.PostgresError as e:
            raise DatabaseError(f"メタデータの取得に失敗しました: {source_id}", e)

    async def close(self):
        """接続プールのクローズ"""
        if self.pool:
            try:
                logger.info("PostgreSQL接続プールをクローズ中...")
                await self.pool.close()
                logger.info("PostgreSQL接続プールをクローズしました")
            except Exception as e:
                raise DatabaseError("PostgreSQL接続のクローズに失敗しました", e)

class MongoHandler:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        try:
            logger.info("MongoHandlerを初期化中...")
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                f"mongodb://{config.mongo_user}:{config.mongo_password}@{config.mongo_host}:{config.mongo_port}",
                serverSelectionTimeoutMS=5000
            )
            self.db = self.client[config.mongo_database]
            logger.info("MongoHandlerの初期化が完了しました")
        except Exception as e:
            raise DatabaseError("MongoDB接続の初期化に失敗しました", e)

    @retry_operation()
    async def fetch_ast(self, source_id: str) -> Dict[str, Any]:
        """ASTデータの取得"""
        try:
            logger.info(f"ASTデータを取得中: {source_id}")
            collection = self.db.ast_collection
            result = await collection.find_one({"source_id": source_id})
            if not result:
                logger.warning(f"ASTデータが見つかりません: {source_id}")
                raise DatabaseError(f"ASTデータが見つかりません: {source_id}")
            logger.info(f"ASTデータの取得が完了しました: {source_id}")
            return result
        except Exception as e:
            raise DatabaseError(f"ASTデータの取得に失敗しました: {source_id}", e)

    async def close(self):
        """MongoDB接続のクローズ"""
        try:
            logger.info("MongoDB接続をクローズ中...")
            self.client.close()
            logger.info("MongoDB接続をクローズしました")
        except Exception as e:
            raise DatabaseError("MongoDB接続のクローズに失敗しました", e)

class DBConnectionHandler:
    def __init__(self, config: DatabaseConfig):
        logger.info("DBConnectionHandlerを初期化中...")
        self.pg_handler = PostgresHandler(config)
        self.mongo_handler = MongoHandler(config)
        self._initialized = False
        self.monitor = DatabaseMonitor()
        logger.info("DBConnectionHandlerの初期化が完了しました")

    async def start_monitoring(self):
        """監視を開始"""
        await self.monitor.start_monitoring()

    async def stop_monitoring(self):
        """監視を停止"""
        await self.monitor.stop_monitoring()

    async def get_metrics(self) -> Dict[str, Any]:
        """メトリクスを取得"""
        return self.monitor.get_metrics()

    async def check_health(self) -> Dict[str, bool]:
        """ヘルスチェックを実行"""
        return self.monitor.check_health()

    @retry_operation()
    async def initialize(self):
        """両方のデータベース接続を初期化"""
        try:
            logger.info("データベース接続を初期化中...")
            await self.pg_handler.initialize()
            self._initialized = True
            logger.info("データベース接続の初期化が完了しました")
        except DatabaseError as e:
            logger.error("データベース接続の初期化に失敗しました")
            await self.close()
            raise DatabaseError("データベース接続の初期化に失敗しました", e)

    async def get_metadata(self, source_id: str) -> Dict[str, Any]:
        """メタデータの取得（監視付き）"""
        start_time = time.time()
        try:
            result = await super().get_metadata(source_id)
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.record_operation('postgres', 'get_metadata', duration_ms)
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.record_operation('postgres', 'get_metadata', duration_ms, e)
            raise

    async def get_ast(self, source_id: str) -> Dict[str, Any]:
        """ASTデータの取得"""
        if not self._initialized:
            await self.initialize()
        return await self.mongo_handler.fetch_ast(source_id)

    @asynccontextmanager
    async def transaction(self):
        """PostgreSQLトランザクションのコンテキストマネージャー"""
        if not self._initialized:
            await self.initialize()
        async with self.pg_handler.transaction() as conn:
            yield conn

    async def close(self):
        """全ての接続をクローズ"""
        try:
            logger.info("全てのデータベース接続をクローズ中...")
            await self.pg_handler.close()
            await self.mongo_handler.close()
            logger.info("全てのデータベース接続をクローズしました")
        except DatabaseError as e:
            raise DatabaseError("データベース接続のクローズに失敗しました", e) 