```python
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod

# 基本的な列挙型
class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AnalysisType(str, Enum):
    STRUCTURE = "structure"
    QUALITY = "quality"
    SECURITY = "security"
    METRICS = "metrics"

class ErrorLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

# 基本モデル
class BaseDBModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True

    @validator('updated_at', always=True)
    def set_updated_at(cls, v, values):
        return v or values['created_at']

# PostgreSQLモデル
class AnalysisTask(BaseDBModel):
    """解析タスク"""
    task_id: UUID
    source_id: UUID
    analysis_type: AnalysisType
    status: AnalysisStatus = AnalysisStatus.PENDING
    priority: int = 0
    options: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AnalysisSource(BaseDBModel):
    """解析対象ソース"""
    source_id: UUID
    file_path: str
    file_type: str
    file_hash: str
    file_size: int
    encoding: Optional[str] = None
    line_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AnalysisResult(BaseDBModel):
    """解析結果メタデータ"""
    result_id: UUID
    task_id: UUID
    source_id: UUID
    analysis_type: AnalysisType
    status: AnalysisStatus
    mongodb_collection: str
    mongodb_document_id: str
    summary_data: Dict[str, Any] = Field(default_factory=dict)

class AnalysisLog(BaseDBModel):
    """解析ログ"""
    log_id: int
    task_id: UUID
    source_id: Optional[UUID]
    level: ErrorLevel
    component: str
    message: str
    details: Optional[Dict[str, Any]] = None

# MongoDBモデル
class ASTData(BaseDBModel):
    """AST データ"""
    source_id: UUID
    task_id: UUID
    ast_type: str
    ast_data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AnalysisResultData(BaseDBModel):
    """詳細な解析結果データ"""
    result_id: UUID
    source_id: UUID
    analysis_type: AnalysisType
    results: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    issues: Optional[List[Dict[str, Any]]] = None

class MetricsData(BaseDBModel):
    """メトリクスデータ"""
    source_id: UUID
    task_id: UUID
    metrics_type: str
    metrics_data: Dict[str, Any]
    trend_data: Optional[Dict[str, Any]] = None
    analysis_details: Optional[Dict[str, Any]] = None

# バリデーター
class DataValidator:
    """データバリデーション"""
    @staticmethod
    def validate_analysis_task(task: AnalysisTask) -> bool:
        """解析タスクのバリデーション"""
        if task.status == AnalysisStatus.COMPLETED:
            if not task.completed_at:
                raise ValueError("Completed task must have completed_at timestamp")
        return True

    @staticmethod
    def validate_analysis_result(result: AnalysisResult) -> bool:
        """解析結果のバリデーション"""
        if result.status == AnalysisStatus.FAILED and not result.summary_data.get("error"):
            raise ValueError("Failed result must include error information")
        return True

# モデルコンバーター
class ModelConverter:
    """モデル変換"""
    @staticmethod
    def to_dict(model: BaseDBModel) -> Dict[str, Any]:
        """モデルを辞書に変換"""
        return model.dict(exclude_unset=True)

    @staticmethod
    def from_dict(data: Dict[str, Any], model_class: type) -> BaseDBModel:
        """辞書からモデルに変換"""
        return model_class(**data)

# マスターデータモデル
class BenchmarkMaster(BaseDBModel):
    """ベンチマークマスター"""
    benchmark_id: int
    category: str
    sub_category: str
    metric_name: str
    description: Optional[str]
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    target_value: Optional[float]
    warning_threshold: Optional[float]
    error_threshold: Optional[float]
    evaluation_rule: Optional[str]
    weight: float = 1.0
    is_active: bool = True

class EnvironmentMaster(BaseDBModel):
    """環境マスター"""
    environment_id: int
    category: str
    sub_category: Optional[str]
    name: str
    value: str
    description: Optional[str]
    is_encrypted: bool = False
    is_active: bool = True

# 解析結果集約モデル
class IntegratedAnalysisResult(BaseDBModel):
    """統合解析結果"""
    integration_id: UUID
    source_ids: List[UUID]
    analysis_types: List[AnalysisType]
    results: Dict[str, Any]
    summary: Dict[str, Any]
    metrics: Dict[str, Any]

    @validator('results')
    def validate_results(cls, v):
        """結果の検証"""
        if not v:
            raise ValueError("Results cannot be empty")
        return v

# 使用例
async def example_model_usage():
    # 解析タスクの作成
    task = AnalysisTask(
        task_id=UUID('12345678-1234-5678-1234-567812345678'),
        source_id=UUID('87654321-4321-8765-4321-876543210987'),
        analysis_type=AnalysisType.STRUCTURE,
        priority=1,
        options={"detailed": True}
    )

    # バリデーション
    DataValidator.validate_analysis_task(task)

    # 辞書への変換
    task_dict = ModelConverter.to_dict(task)

    # AST データの作成
    ast_data = ASTData(
        source_id=UUID('12345678-1234-5678-1234-567812345678'),
        task_id=UUID('87654321-4321-8765-4321-876543210987'),
        ast_type="COBOL",
        ast_data={
            "type": "program",
            "children": []
        },
        metadata={
            "source_file": "example.cbl",
            "parser_version": "1.0.0"
        }
    )

    # 統合解析結果の作成
    integrated_result = IntegratedAnalysisResult(
        integration_id=UUID('12345678-1234-5678-1234-567812345678'),
        source_ids=[
            UUID('87654321-4321-8765-4321-876543210987'),
            UUID('98765432-5432-9876-5432-987654321098')
        ],
        analysis_types=[
            AnalysisType.STRUCTURE,
            AnalysisType.QUALITY
        ],
        results={
            "structure": {"complexity": 10},
            "quality": {"score": 0.85}
        },
        summary={
            "total_files": 2,
            "average_quality": 0.85
        },
        metrics={
            "complexity": {
                "average": 10,
                "max": 15
            }
        }
    )
```