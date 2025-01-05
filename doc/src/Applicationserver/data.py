# /home/administrator/cobol-analyzer/src/models/data.py

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class AnalysisType(str, Enum):
    STRUCTURE = "structure"
    QUALITY = "quality"
    SECURITY = "security"
    METRICS = "metrics"
    CROSS_REFERENCE = "cross_reference"
    EMBEDDED = "embedded"

class ErrorLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class BaseModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

# 解析タスク関連モデル
class AnalysisTask(BaseModel):
    task_id: UUID
    source_id: UUID
    analysis_type: AnalysisType
    status: AnalysisStatus = AnalysisStatus.PENDING
    priority: int = 0
    options: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AnalysisSource(BaseModel):
    source_id: UUID
    file_path: str
    file_type: str
    file_hash: str
    file_size: int
    encoding: Optional[str] = None
    line_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AnalysisResult(BaseModel):
    result_id: UUID
    task_id: UUID
    source_id: UUID
    analysis_type: AnalysisType
    status: AnalysisStatus
    results: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None

# メトリクスと評価関連モデル
class MetricsData(BaseModel):
    source_id: UUID
    metric_type: str
    metric_name: str
    value: float
    threshold: Optional[float] = None
    comparison_result: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class SecurityIssue(BaseModel):
    issue_id: UUID
    source_id: UUID
    severity: str
    category: str
    description: str
    location: Dict[str, Any]
    recommendation: Optional[str] = None
    cve_id: Optional[str] = None

class QualityMetrics(BaseModel):
    source_id: UUID
    complexity_score: float
    maintainability_score: float
    reliability_score: float
    documentation_score: float
    test_coverage: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)

# 解析ログモデル
class AnalysisLog(BaseModel):
    log_id: int
    task_id: UUID
    source_id: Optional[UUID]
    level: ErrorLevel
    component: str
    message: str
    details: Optional[Dict[str, Any]] = None

# クロスリファレンスモデル
class CrossReference(BaseModel):
    source_id: UUID
    target_id: UUID
    reference_type: str
    location: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)

# 集約結果モデル
class AggregatedResult(BaseModel):
    aggregation_id: UUID
    source_ids: List[UUID]
    analysis_type: AnalysisType
    metrics: Dict[str, Any]
    summary: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)