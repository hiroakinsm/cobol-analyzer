# Implementation Server: 172.16.0.27 (Application Server)
# Path: /home/administrator/cobol-analyzer/src/database/db_base.py

# Database Access Layer.py から実装開始
from typing import Dict, List, Optional, Any, TypeVar, Generic
from datetime import datetime
from uuid import UUID
import asyncpg
import motor.motor_asyncio
from abc import ABC, abstractmethod
import logging

class DatabaseConfig:
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        min_connections: int = 10,
        max_connections: int = 100
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_connections = min_connections
        self.max_connections = max_connections

class PostgresManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize PostgreSQL pool: {str(e)}")
            raise

    async def close(self):
        if self.pool:
            await self.pool.close()

class MongoManager:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user,
                password=self.config.password
            )
            self.db = self.client[self.config.database]
        except Exception as e:
            self.logger.error(f"Failed to initialize MongoDB connection: {str(e)}")
            raise

    async def close(self):
        if self.client:
            self.client.close()
