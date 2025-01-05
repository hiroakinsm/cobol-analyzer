# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/base/components.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import json
import logging
import chardet
import hashlib

# 基本的な型定義
class SourceType(Enum):
    COBOL = "COBOL"
    JCL = "JCL"
    ASM = "ASM"

class AnalysisStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class SourceFile:
    file_path: Path
    source_type: SourceType
    encoding: str
    size: int
    hash: str
    metadata: Dict[str, Any]

@dataclass
class AnalysisContext:
    task_id: UUID
    source_id: UUID
    source_file: SourceFile
    config: Dict[str, Any]
    status: AnalysisStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

# 基本的なソースファイル読み込み
class SourceReader(ABC):
    """ソースファイル読み込みの基底クラス"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def read_file(self, file_path: Path, encoding: Optional[str] = None) -> str:
        """ソースファイルを読み込む"""
        try:
            encoding = encoding or self.detect_encoding(file_path)
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger.error(f"Failed to read file {file_path}: {str(e)}")
            raise

    @abstractmethod
    def detect_encoding(self, file_path: Path) -> str:
        """ファイルのエンコーディングを検出"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'
        except Exception as e:
            self.logger.error(f"Failed to detect encoding for {file_path}: {str(e)}")
            return 'utf-8'

    @abstractmethod
    def calculate_hash(self, content: str) -> str:
        """ファイルのハッシュ値を計算"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

class BaseParser(ABC):
    """基本的なパーサーインターフェース"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def parse(self, content: str) -> Dict[str, Any]:
        """ソースコードをパースしてAST生成"""
        try:
            ast = self._tokenize(content)
            ast = self._build_ast(ast)
            self.validate(ast)
            return ast
        except Exception as e:
            self.logger.error(f"Parse error: {str(e)}")
            raise

    @abstractmethod
    def validate(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ASTの妥当性を検証"""
        validation_errors = []
        try:
            validation_errors.extend(self._validate_structure(ast))
            validation_errors.extend(self._validate_references(ast))
            validation_errors.extend(self._validate_semantics(ast))
            return validation_errors
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            raise

class MetricsCollector(ABC):
    """メトリクス収集の基底クラス"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def collect_metrics(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """ASTからメトリクスを収集"""
        metrics = {}
        try:
            metrics.update(self._collect_complexity_metrics(ast))
            metrics.update(self._collect_volume_metrics(ast))
            metrics.update(self._collect_maintainability_metrics(ast))
            return metrics
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {str(e)}")
            raise

    @abstractmethod
    def normalize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスを正規化"""
        try:
            normalized = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    normalized[key] = self._normalize_value(value, key)
                else:
                    normalized[key] = value
            return normalized
        except Exception as e:
            self.logger.error(f"Failed to normalize metrics: {str(e)}")
            raise

    @abstractmethod
    def evaluate_metrics(self, normalized_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスを評価"""
        try:
            evaluation = {}
            for metric_name, value in normalized_metrics.items():
                evaluation[metric_name] = {
                    'value': value,
                    'score': self._calculate_score(value, metric_name),
                    'recommendation': self._generate_recommendation(value, metric_name)
                }
            return evaluation
        except Exception as e:
            self.logger.error(f"Failed to evaluate metrics: {str(e)}")
            raise

class ResultManager:
    """結果管理"""
    def __init__(self, context: 'AnalysisContext'):
        self.context = context
        self.logger = logging.getLogger(__name__)
        self._results: Dict[str, Any] = {}

    async def save_to_postgresql(self) -> None:
        """結果をPostgreSQLに保存"""
        try:
            async with self.context.db_manager.transaction() as conn:
                await conn.execute("""
                    INSERT INTO analysis_results_partitioned (
                        result_id, task_id, source_id, analysis_type,
                        status, results, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, UUID(), self.context.task_id, self.context.source_id,
                    self.context.analysis_type, "completed",
                    json.dumps(self._results), datetime.utcnow())
        except Exception as e:
            self.logger.error(f"Failed to save results to PostgreSQL: {str(e)}")
            raise

    async def save_to_mongodb(self) -> None:
        """結果をMongoDBに保存"""
        try:
            document = {
                "task_id": str(self.context.task_id),
                "source_id": str(self.context.source_id),
                "analysis_type": self.context.analysis_type,
                "results": self._results,
                "created_at": datetime.utcnow()
            }
            await self.context.mongo_client[self.context.database]["analysis_results"].insert_one(document)
        except Exception as e:
            self.logger.error(f"Failed to save results to MongoDB: {str(e)}")
            raise

class AnalysisLogger:
    """解析ログ"""
    def __init__(self, context: 'AnalysisContext'):
        self.context = context
        self.logger = logging.getLogger(__name__)

    def log_info(self, component: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """情報ログを記録"""
        try:
            self._log_entry("INFO", component, message, details)
        except Exception as e:
            self.logger.error(f"Failed to log info: {str(e)}")

    def log_warning(self, component: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """警告ログを記録"""
        try:
            self._log_entry("WARNING", component, message, details)
        except Exception as e:
            self.logger.error(f"Failed to log warning: {str(e)}")

    def log_error(self, component: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """エラーログを記録"""
        try:
            self._log_entry("ERROR", component, message, details)
        except Exception as e:
            self.logger.error(f"Failed to log error: {str(e)}")

class BaseAnalyzer(ABC):
    """解析タスク基底クラス"""
    def __init__(self, context: 'AnalysisContext'):
        self.context = context
        self.logger = logging.getLogger(__name__)
        self.result_manager = ResultManager(context)

    @abstractmethod
    def prepare(self) -> bool:
        """解析の準備を行う"""
        try:
            self.logger.info(f"Preparing analysis for task {self.context.task_id}")
            self.context.start_time = datetime.utcnow()
            return self._validate_prerequisites() and self._initialize_resources()
        except Exception as e:
            self.logger.error(f"Preparation failed: {str(e)}")
            return False

    @abstractmethod
    def analyze(self) -> bool:
        """解析を実行"""
        try:
            self.logger.info(f"Starting analysis for task {self.context.task_id}")
            analysis_result = self._perform_analysis()
            self.result_manager.add_result("analysis", analysis_result)
            return True
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return False

    @abstractmethod
    def post_process(self) -> bool:
        """解析後の処理を実行"""
        try:
            self.logger.info(f"Post-processing task {self.context.task_id}")
            self.context.end_time = datetime.utcnow()
            await self.result_manager.save_to_postgresql()
            await self.result_manager.save_to_mongodb()
            return True
        except Exception as e:
            self.logger.error(f"Post-processing failed: {str(e)}")
            return False

class DatabaseConnection(ABC):
    """データベース接続管理"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def connect(self) -> None:
        """データベースに接続"""
        try:
            self.logger.info("Establishing database connection")
            await self._establish_connection()
            await self._validate_connection()
        except Exception as e:
            self.logger.error(f"Connection failed: {str(e)}")
            raise

    @abstractmethod
    async def disconnect(self) -> None:
        """データベースから切断"""
        try:
            self.logger.info("Closing database connection")
            await self._close_connection()
        except Exception as e:
            self.logger.error(f"Disconnection failed: {str(e)}")
            raise

    @abstractmethod
    async def begin_transaction(self) -> None:
        """トランザクションを開始"""
        try:
            self.logger.info("Beginning transaction")
            await self._start_transaction()
        except Exception as e:
            self.logger.error(f"Transaction start failed: {str(e)}")
            raise

    @abstractmethod
    async def commit(self) -> None:
        """トランザクションをコミット"""
        try:
            self.logger.info("Committing transaction")
            await self._commit_transaction()
        except Exception as e:
            self.logger.error(f"Commit failed: {str(e)}")
            raise

    @abstractmethod
    async def rollback(self) -> None:
        """トランザクションをロールバック"""
        try:
            self.logger.info("Rolling back transaction")
            await self._rollback_transaction()
        except Exception as e:
            self.logger.error(f"Rollback failed: {str(e)}")
            raise