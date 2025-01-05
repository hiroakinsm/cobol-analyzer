# /home/administrator/cobol-analyzer/src/repository/repository_implementation.py

from typing import Dict, List, Optional, Any, Generic, TypeVar
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from uuid import UUID
import logging
from dataclasses import dataclass
import asyncpg
import motor.motor_asyncio
from collections import defaultdict
import statistics
from enum import Enum
import json

@dataclass
class DatabaseConfig:
    """データベース設定"""
    host: str
    port: int
    database: str
    user: str
    password: str
    min_connections: int = 10
    max_connections: int = 100

class DatabaseConnection(ABC):
    """データベース接続の抽象基底クラス"""
    async def connect(self) -> None:
        """接続確立"""
        raise NotImplementedError

    async def disconnect(self) -> None:
        """接続切断"""
        raise NotImplementedError

    async def begin_transaction(self) -> None:
        """トランザクション開始"""
        raise NotImplementedError

    async def commit(self) -> None:
        """コミット"""
        raise NotImplementedError

    async def rollback(self) -> None:
        """ロールバック"""
        raise NotImplementedError

class PostgresManager(DatabaseConnection):
    """PostgreSQL接続管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        """接続確立"""
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
            self.logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """接続切断"""
        if self.pool:
            await self.pool.close()

    async def begin_transaction(self) -> None:
        """トランザクション開始"""
        if not self.pool:
            await self.connect()

    async def commit(self) -> None:
        """コミット"""
        pass  # PostgreSQLのトランザクションは個別のコネクションで管理

    async def rollback(self) -> None:
        """ロールバック"""
        pass  # PostgreSQLのトランザクションは個別のコネクションで管理

    async def execute(self, query: str, *args) -> str:
        """クエリ実行"""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[Dict[str, Any]]:
        """複数行取得"""
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """1行取得"""
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None

class MongoManager(DatabaseConnection):
    """MongoDB接続管理"""
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        """接続確立"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                host=self.config.host,
                port=self.config.port,
                username=self.config.user,
                password=self.config.password
            )
            self.db = self.client[self.config.database]
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    async def disconnect(self) -> None:
        """接続切断"""
        if self.client:
            self.client.close()

    async def begin_transaction(self) -> None:
        """トランザクション開始"""
        if not self.client:
            await self.connect()

    async def commit(self) -> None:
        """コミット"""
        pass  # MongoDBのトランザクションはセッションで管理

    async def rollback(self) -> None:
        """ロールバック"""
        pass  # MongoDBのトランザクションはセッションで管理

    def get_collection(self, name: str) -> motor.motor_asyncio.AsyncIOMotorCollection:
        """コレクション取得"""
        return self.db[name]

    async def aggregate(self, collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """集約クエリの実行"""
        return await self.db[collection].aggregate(pipeline).to_list(None)
        
# モデル定義
@dataclass
class BaseDBModel:
    """基本データモデル"""
    id: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

@dataclass
class AnalysisTask(BaseDBModel):
    """解析タスク"""
    task_id: UUID
    source_id: UUID
    task_type: str
    status: str
    target_sources: Dict[str, Any]
    task_parameters: Optional[Dict[str, Any]]
    error_detail: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

@dataclass
class AnalysisResult(BaseDBModel):
    """解析結果"""
    result_id: UUID
    task_id: UUID
    source_id: UUID
    analysis_type: str
    status: str
    results: Dict[str, Any]
    execution_time: float
    error_message: Optional[str]

@dataclass
class ASTData(BaseDBModel):
    """AST データ"""
    ast_id: UUID
    source_id: UUID
    version: str
    ast_data: Dict[str, Any]
    metadata: Dict[str, Any]

# リポジトリの実装
class PostgresRepository(Generic[T]):
    """PostgreSQL用リポジトリ基底クラス"""
    def __init__(self, db_manager: PostgresManager, model_class: type[T]):
        self.db = db_manager
        self.model_class = model_class
        self.table_name = model_class.__name__.lower()
        self.logger = logging.getLogger(__name__)

    async def get(self, id: Any) -> Optional[T]:
        """IDによるエンティティ取得"""
        query = f"SELECT * FROM {self.table_name} WHERE id = $1"
        try:
            row = await self.db.fetchrow(query, id)
            return self.model_class(**row) if row else None
        except Exception as e:
            self.logger.error(f"Failed to get {self.table_name} by id {id}: {str(e)}")
            raise

    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        """フィルタ条件によるエンティティ取得"""
        conditions = " AND ".join(f"{k} = ${i+1}" for i, k in enumerate(filter_dict.keys()))
        query = f"SELECT * FROM {self.table_name} WHERE {conditions}"
        try:
            rows = await self.db.fetch(query, *filter_dict.values())
            return [self.model_class(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get many {self.table_name}: {str(e)}")
            raise

    async def add(self, entity: T) -> Any:
        """エンティティの追加"""
        fields = entity.__dict__.keys()
        placeholders = [f"${i+1}" for i in range(len(fields))]
        query = f"""
            INSERT INTO {self.table_name} ({','.join(fields)})
            VALUES ({','.join(placeholders)})
            RETURNING id
        """
        try:
            return await self.db.fetchrow(query, *entity.__dict__.values())
        except Exception as e:
            self.logger.error(f"Failed to add {self.table_name}: {str(e)}")
            raise

    async def update(self, entity: T) -> bool:
        """エンティティの更新"""
        fields = [f for f in entity.__dict__.keys() if f != 'id']
        sets = [f"{f} = ${i+2}" for i, f in enumerate(fields)]
        query = f"""
            UPDATE {self.table_name}
            SET {','.join(sets)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        try:
            result = await self.db.execute(query, entity.id, *[getattr(entity, f) for f in fields])
            return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to update {self.table_name}: {str(e)}")
            raise

    async def delete(self, id: Any) -> bool:
        """エンティティの削除"""
        query = f"DELETE FROM {self.table_name} WHERE id = $1"
        try:
            result = await self.db.execute(query, id)
            return result == "DELETE 1"
        except Exception as e:
            self.logger.error(f"Failed to delete {self.table_name}: {str(e)}")
            raise

class MongoRepository(Generic[T]):
    """MongoDB用リポジトリ基底クラス"""
    def __init__(self, db_manager: MongoManager, model_class: type[T]):
        self.db = db_manager
        self.model_class = model_class
        self.collection_name = model_class.__name__.lower()
        self.logger = logging.getLogger(__name__)

    async def get(self, id: Any) -> Optional[T]:
        """IDによるエンティティ取得"""
        try:
            doc = await self.db.get_collection(self.collection_name).find_one({"_id": id})
            return self.model_class(**doc) if doc else None
        except Exception as e:
            self.logger.error(f"Failed to get {self.collection_name} by id {id}: {str(e)}")
            raise

    async def get_many(self, filter_dict: Dict[str, Any]) -> List[T]:
        """フィルタ条件によるエンティティ取得"""
        try:
            cursor = self.db.get_collection(self.collection_name).find(filter_dict)
            docs = await cursor.to_list(None)
            return [self.model_class(**doc) for doc in docs]
        except Exception as e:
            self.logger.error(f"Failed to get many {self.collection_name}: {str(e)}")
            raise

    async def add(self, entity: T) -> Any:
        """エンティティの追加"""
        try:
            result = await self.db.get_collection(self.collection_name).insert_one(entity.__dict__)
            return result.inserted_id
        except Exception as e:
            self.logger.error(f"Failed to add {self.collection_name}: {str(e)}")
            raise

    async def update(self, entity: T) -> bool:
        """エンティティの更新"""
        try:
            result = await self.db.get_collection(self.collection_name).update_one(
                {"_id": entity.id},
                {"$set": {**entity.__dict__, "updated_at": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Failed to update {self.collection_name}: {str(e)}")
            raise

    async def delete(self, id: Any) -> bool:
        """エンティティの削除"""
        try:
            result = await self.db.get_collection(self.collection_name).delete_one({"_id": id})
            return result.deleted_count > 0
        except Exception as e:
            self.logger.error(f"Failed to delete {self.collection_name}: {str(e)}")
            raise
            
# 具体的なリポジトリの実装
class AnalysisTaskRepository(PostgresRepository[AnalysisTask]):
    """解析タスクリポジトリ"""
    async def get_pending_tasks(self) -> List[AnalysisTask]:
        """保留中タスクの取得"""
        query = """
            SELECT * FROM analysis_tasks 
            WHERE status = 'pending'
            ORDER BY priority DESC, created_at ASC
        """
        try:
            rows = await self.db.fetch(query)
            return [AnalysisTask(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get pending tasks: {str(e)}")
            raise

    async def update_status(self, task_id: UUID, status: str) -> bool:
        """タスクステータスの更新"""
        query = """
            UPDATE analysis_tasks
            SET 
                status = $1,
                updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE 
                    WHEN $1 IN ('completed', 'failed') THEN CURRENT_TIMESTAMP
                    ELSE completed_at
                END
            WHERE task_id = $2
        """
        try:
            result = await self.db.execute(query, status, task_id)
            return result == "UPDATE 1"
        except Exception as e:
            self.logger.error(f"Failed to update task status: {str(e)}")
            raise

class AnalysisResultRepository(PostgresRepository[AnalysisResult]):
    """解析結果リポジトリ"""
    async def get_results_by_source(self, source_id: UUID) -> List[AnalysisResult]:
        """ソースIDによる結果取得"""
        query = """
            SELECT * FROM analysis_results
            WHERE source_id = $1
            ORDER BY created_at DESC
        """
        try:
            rows = await self.db.fetch(query, source_id)
            return [AnalysisResult(**row) for row in rows]
        except Exception as e:
            self.logger.error(f"Failed to get results by source: {str(e)}")
            raise

    async def store_stage_result(self, 
                               task_id: UUID, 
                               stage: str, 
                               result: Dict[str, Any]) -> UUID:
        """ステージ結果の保存"""
        query = """
            INSERT INTO analysis_results (
                result_id, task_id, source_id, analysis_type,
                status, results, execution_time, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP)
            RETURNING result_id
        """
        try:
            result_id = UUID()
            await self.db.execute(
                query,
                result_id,
                task_id,
                result["source_id"],
                stage,
                "completed",
                json.dumps(result),
                result.get("execution_time", 0)
            )
            return result_id
        except Exception as e:
            self.logger.error(f"Failed to store stage result: {str(e)}")
            raise

class ASTRepository(MongoRepository[ASTData]):
    """ASTリポジトリ"""
    async def get_ast_by_source(self, source_id: UUID) -> Optional[ASTData]:
        """ソースIDによるAST取得"""
        try:
            doc = await self.db.get_collection("ast_collection").find_one(
                {"source_id": str(source_id)}
            )
            return ASTData(**doc) if doc else None
        except Exception as e:
            self.logger.error(f"Failed to get AST by source: {str(e)}")
            raise

    async def update_ast(self, source_id: UUID, ast_data: Dict[str, Any]) -> bool:
        """AST更新"""
        try:
            result = await self.db.get_collection("ast_collection").update_one(
                {"source_id": str(source_id)},
                {
                    "$set": {
                        "ast_data": ast_data,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            self.logger.error(f"Failed to update AST: {str(e)}")
            raise

class IntegratedResultRepository:
    """統合結果リポジトリ"""
    def __init__(self, 
                 analysis_result_repo: AnalysisResultRepository,
                 ast_repo: ASTRepository):
        self.analysis_result_repo = analysis_result_repo
        self.ast_repo = ast_repo
        self.logger = logging.getLogger(__name__)

    async def get_integrated_result(self, source_id: UUID) -> Dict[str, Any]:
        """統合結果の取得"""
        try:
            # 解析結果の取得
            results = await self.analysis_result_repo.get_results_by_source(source_id)
            
            # AST情報の取得
            ast = await self.ast_repo.get_ast_by_source(source_id)

            # 結果の統合
            integrated = {
                "source_id": source_id,
                "analysis_results": [result.__dict__ for result in results],
                "ast_info": ast.__dict__ if ast else None,
                "summary": {
                    "total_analyses": len(results),
                    "latest_analysis": results[0].__dict__ if results else None,
                    "has_ast": ast is not None
                },
                "integrated_at": datetime.utcnow()
            }

            return integrated
        except Exception as e:
            self.logger.error(f"Failed to get integrated result: {str(e)}")
            raise