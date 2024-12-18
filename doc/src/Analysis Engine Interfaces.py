```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from uuid import UUID

# 解析結果の状態
class AnalysisStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"

# 解析の種類
class AnalysisType(Enum):
    STRUCTURE = "structure"
    DATA = "data"
    QUALITY = "quality"
    METRICS = "metrics"
    SECURITY = "security"
    BENCHMARK = "benchmark"

# エラーレベル
class ErrorLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class AnalysisError:
    level: ErrorLevel
    message: str
    details: Optional[Dict[str, Any]] = None
    location: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.utcnow()

@dataclass
class AnalysisResult:
    analysis_id: UUID
    source_id: UUID
    analysis_type: AnalysisType
    status: AnalysisStatus
    results: Dict[str, Any]
    errors: List[AnalysisError]
    execution_time: float
    created_at: datetime = datetime.utcnow()

# 解析エンジンの基本インターフェース
class IAnalysisEngine(ABC):
    @abstractmethod
    def analyze(self, ast: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """解析を実行"""
        pass

    @abstractmethod
    def validate_input(self, ast: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """入力の検証"""
        pass

    @abstractmethod
    def supports_analysis_type(self, analysis_type: AnalysisType) -> bool:
        """解析タイプのサポート確認"""
        pass

# 解析結果ハンドラーのインターフェース
class IResultHandler(ABC):
    @abstractmethod
    def handle_result(self, result: AnalysisResult) -> bool:
        """解析結果の処理"""
        pass

    @abstractmethod
    def handle_error(self, error: AnalysisError) -> None:
        """エラーの処理"""
        pass

# 解析コンテキストマネージャー
class AnalysisContextManager:
    def __init__(self):
        self.contexts: Dict[UUID, Dict[str, Any]] = {}

    def create_context(self, analysis_id: UUID, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析コンテキストの作成"""
        context = {
            "analysis_id": analysis_id,
            "start_time": datetime.utcnow(),
            "status": AnalysisStatus.SUCCESS,
            "errors": [],
            **initial_data
        }
        self.contexts[analysis_id] = context
        return context

    def update_context(self, analysis_id: UUID, updates: Dict[str, Any]) -> None:
        """コンテキストの更新"""
        if analysis_id not in self.contexts:
            raise KeyError(f"Context not found for analysis_id: {analysis_id}")
        self.contexts[analysis_id].update(updates)

    def get_context(self, analysis_id: UUID) -> Dict[str, Any]:
        """コンテキストの取得"""
        return self.contexts.get(analysis_id, {})

# 解析エンジンマネージャー
class AnalysisEngineManager:
    def __init__(self):
        self.engines: Dict[AnalysisType, IAnalysisEngine] = {}
        self.context_manager = AnalysisContextManager()
        self.result_handlers: List[IResultHandler] = []

    def register_engine(self, analysis_type: AnalysisType, engine: IAnalysisEngine) -> None:
        """解析エンジンの登録"""
        self.engines[analysis_type] = engine

    def register_result_handler(self, handler: IResultHandler) -> None:
        """結果ハンドラーの登録"""
        self.result_handlers.append(handler)

    async def execute_analysis(self, analysis_id: UUID, ast: Dict[str, Any], 
                             analysis_type: AnalysisType, context_data: Dict[str, Any]) -> AnalysisResult:
        """解析の実行"""
        if analysis_type not in self.engines:
            raise ValueError(f"No engine registered for analysis type: {analysis_type}")

        engine = self.engines[analysis_type]
        context = self.context_manager.create_context(analysis_id, context_data)

        try:
            if not engine.validate_input(ast, context):
                raise ValueError("Input validation failed")

            result = await self._execute_engine(engine, ast, context)
            self._handle_result(result)
            return result

        except Exception as e:
            error = AnalysisError(
                level=ErrorLevel.ERROR,
                message=str(e),
                details={"exception_type": type(e).__name__}
            )
            self._handle_error(error)
            raise

    async def _execute_engine(self, engine: IAnalysisEngine, ast: Dict[str, Any], 
                            context: Dict[str, Any]) -> AnalysisResult:
        """エンジンの実行"""
        return await engine.analyze(ast, context)

    def _handle_result(self, result: AnalysisResult) -> None:
        """結果の処理"""
        for handler in self.result_handlers:
            handler.handle_result(result)

    def _handle_error(self, error: AnalysisError) -> None:
        """エラーの処理"""
        for handler in self.result_handlers:
            handler.handle_error(error)

# 結果保存ハンドラー
class DatabaseResultHandler(IResultHandler):
    def __init__(self, mongo_client, postgres_client):
        self.mongo_client = mongo_client
        self.postgres_client = postgres_client

    def handle_result(self, result: AnalysisResult) -> bool:
        """結果のデータベース保存"""
        try:
            # MongoDBに詳細結果を保存
            self._save_to_mongodb(result)
            # PostgreSQLにメタデータを保存
            self._save_to_postgresql(result)
            return True
        except Exception as e:
            logging.error(f"Failed to save analysis result: {e}")
            return False

    def handle_error(self, error: AnalysisError) -> None:
        """エラーのログ保存"""
        try:
            self._log_error_to_postgresql(error)
        except Exception as e:
            logging.error(f"Failed to save error: {e}")

    def _save_to_mongodb(self, result: AnalysisResult) -> None:
        """MongoDBへの保存"""
        collection = self.mongo_client.get_collection(str(result.analysis_type))
        document = {
            "analysis_id": str(result.analysis_id),
            "source_id": str(result.source_id),
            "results": result.results,
            "created_at": result.created_at
        }
        collection.insert_one(document)

    def _save_to_postgresql(self, result: AnalysisResult) -> None:
        """PostgreSQLへの保存"""
        query = """
        INSERT INTO analysis_results 
        (analysis_id, source_id, analysis_type, status, execution_time, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.postgres_client.execute(
            query,
            (str(result.analysis_id), str(result.source_id), 
             result.analysis_type.value, result.status.value,
             result.execution_time, result.created_at)
        )
```