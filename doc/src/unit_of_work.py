# /home/administrator/cobol-analyzer/src/db/unit_of_work.py

from typing import Dict, Optional
from contextlib import asynccontextmanager
import logging

from .connection_managers import PostgresConnectionManager, MongoConnectionManager
from .repositories import (
    AnalysisTaskRepository,
    ASTRepository,
    AnalysisResultRepository
)

class UnitOfWork:
    """Unit of Workパターンの実装"""
    def __init__(self, 
                 pg_connection: PostgresConnectionManager,
                 mongo_connection: MongoConnectionManager):
        self.pg_connection = pg_connection
        self.mongo_connection = mongo_connection
        self.logger = logging.getLogger(__name__)

        # リポジトリの初期化
        self.analysis_tasks = AnalysisTaskRepository(pg_connection)
        self.asts = ASTRepository(mongo_connection)
        self.analysis_results = AnalysisResultRepository(mongo_connection)

    async def begin_transaction(self):
        """トランザクションの開始"""
        try:
            self._pg_transaction = await self.pg_connection.transaction()
            self._mongo_transaction = await self.mongo_connection.transaction()
        except Exception as e:
            self.logger.error(f"Failed to begin transaction: {str(e)}")
            raise

    async def commit(self):
        """トランザクションのコミット"""
        try:
            await self._pg_transaction.commit()
            await self._mongo_transaction.commit()
        except Exception as e:
            self.logger.error(f"Failed to commit transaction: {str(e)}")
            await self.rollback()
            raise

    async def rollback(self):
        """トランザクションのロールバック"""
        try:
            if hasattr(self, '_pg_transaction'):
                await self._pg_transaction.rollback()
            if hasattr(self, '_mongo_transaction'):
                await self._mongo_transaction.abort()
        except Exception as e:
            self.logger.error(f"Failed to rollback transaction: {str(e)}")
            raise

    @asynccontextmanager
    async def transaction(self):
        """トランザクションのコンテキスト管理"""
        try:
            await self.begin_transaction()
            yield self
            await self.commit()
        except Exception as e:
            await self.rollback()
            raise