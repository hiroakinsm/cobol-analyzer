# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/engine/interfaces.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

class AnalysisStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    SKIPPED = "skipped"

class AnalysisType(Enum):
    STRUCTURE = "structure"
    DATA = "data"
    QUALITY = "quality"
    METRICS = "metrics"
    SECURITY = "security"
    BENCHMARK = "benchmark"

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

class IAnalysisEngine(ABC):
    """解析エンジンの基本インターフェース"""
    
    @abstractmethod
    def analyze(self, ast: Dict[str, Any], context: Dict[str, Any]) -> AnalysisResult:
        """解析を実行

        Args:
            ast (Dict[str, Any]): 解析対象のAST
            context (Dict[str, Any]): 解析コンテキスト

        Returns:
            AnalysisResult: 解析結果

        Raises:
            ValueError: ASTまたはコンテキストが無効な場合
            AnalysisError: 解析中にエラーが発生した場合
        """
        error = AnalysisError(
            level=ErrorLevel.ERROR,
            message="Method not implemented",
            details={"ast_size": len(str(ast)), "context": context}
        )
        return AnalysisResult(
            analysis_id=UUID(),
            source_id=UUID(),
            analysis_type=AnalysisType.STRUCTURE,
            status=AnalysisStatus.FAILED,
            results={},
            errors=[error],
            execution_time=0.0
        )

    @abstractmethod
    def validate_input(self, ast: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """入力の検証

        Args:
            ast (Dict[str, Any]): 検証対象のAST
            context (Dict[str, Any]): 検証対象のコンテキスト

        Returns:
            bool: 検証結果（True: 有効、False: 無効）

        Raises:
            ValueError: 必須パラメータが不足している場合
        """
        if not ast:
            raise ValueError("AST is required")
        if not context:
            raise ValueError("Context is required")
        return True

    @abstractmethod
    def supports_analysis_type(self, analysis_type: AnalysisType) -> bool:
        """解析タイプのサポート確認

        Args:
            analysis_type (AnalysisType): 確認対象の解析タイプ

        Returns:
            bool: サポート状況（True: サポート、False: 非サポート）
        """
        return analysis_type in [
            AnalysisType.STRUCTURE,
            AnalysisType.DATA,
            AnalysisType.QUALITY,
            AnalysisType.METRICS,
            AnalysisType.SECURITY,
            AnalysisType.BENCHMARK
        ]

class IResultHandler(ABC):
    """解析結果ハンドラーのインターフェース"""
    
    @abstractmethod
    def handle_result(self, result: AnalysisResult) -> bool:
        """解析結果の処理

        Args:
            result (AnalysisResult): 処理対象の解析結果

        Returns:
            bool: 処理結果（True: 成功、False: 失敗）

        Raises:
            ValueError: 結果が無効な場合
            StorageError: 保存に失敗した場合
        """
        if not result:
            raise ValueError("Result is required")
        if not isinstance(result, AnalysisResult):
            raise ValueError("Invalid result type")
        
        # 結果の基本検証
        if not result.analysis_id or not result.source_id:
            return False
            
        # エラー数の確認
        if result.status == AnalysisStatus.SUCCESS and result.errors:
            return False
            
        # 実行時間の妥当性確認
        if result.execution_time < 0:
            return False
            
        return True

    @abstractmethod
    def handle_error(self, error: AnalysisError) -> None:
        """エラーの処理

        Args:
            error (AnalysisError): 処理対象のエラー

        Raises:
            ValueError: エラーが無効な場合
            LoggingError: ログ記録に失敗した場合
        """
        if not error:
            raise ValueError("Error is required")
        if not isinstance(error, AnalysisError):
            raise ValueError("Invalid error type")
            
        # エラーレベルの確認
        if error.level not in ErrorLevel:
            raise ValueError("Invalid error level")
            
        # タイムスタンプの確認
        if error.timestamp > datetime.utcnow():
            raise ValueError("Invalid timestamp")
            
        # 詳細情報の検証
        if error.details and not isinstance(error.details, dict):
            raise ValueError("Invalid details format")