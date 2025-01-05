# /home/administrator/cobol-analyzer/src/models/data.py

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

# マスターデータ基底モデル
class BaseMaster(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    is_active: bool = True

    class Config:
        orm_mode = True

class EnvironmentMaster(BaseMaster):
    environment_id: int
    category: str
    sub_category: Optional[str]
    name: str
    value: str
    description: Optional[str]
    is_encrypted: bool = False

class SingleAnalysisMaster(BaseMaster):
    analysis_id: int
    analysis_type: str
    process_type: str
    parameter_name: str
    parameter_value: str
    data_type: str
    default_value: Optional[str]
    is_required: bool = False
    validation_rule: Optional[str]
    description: Optional[str]

class SummaryAnalysisMaster(BaseMaster):
    summary_id: int
    analysis_type: str
    process_type: str
    parameter_name: str
    parameter_value: str
    data_type: str
    default_value: Optional[str]
    is_required: bool = False
    validation_rule: Optional[str]
    description: Optional[str]

class DashboardMaster(BaseMaster):
    dashboard_id: int
    dashboard_type: str
    component_type: str
    parameter_name: str
    parameter_value: str
    display_order: int
    layout_config: Dict[str, Any] = Field(default_factory=dict)
    style_config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str]

class DocumentMaster(BaseMaster):
    document_id: int
    document_type: str
    section_type: str
    parameter_name: str
    parameter_value: str
    display_order: int
    template_path: str
    format_config: Dict[str, Any] = Field(default_factory=dict)
    description: Optional[str]

class BenchmarkMaster(BaseMaster):
    benchmark_id: int
    category: str
    sub_category: str
    metric_name: str
    description: str
    unit: Optional[str]
    min_value: Optional[float]
    max_value: Optional[float]
    target_value: Optional[float]
    warning_threshold: Optional[float]
    error_threshold: Optional[float]
    evaluation_rule: Optional[str]
    weight: float = 1.0

# ログと履歴モデル
class AnalysisLog(BaseModel):
    log_id: int
    task_id: UUID
    source_id: Optional[UUID]
    level: str
    component: str
    message: str
    details: Optional[Dict[str, Any]]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskHistory(BaseModel):
    history_id: int
    task_id: UUID
    status: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# パーティションテーブルモデル
class AnalysisTaskPartitioned(BaseModel):
    task_id: UUID
    source_id: UUID
    task_type: str
    status: str
    priority: int = 0
    analysis_config: Dict[str, Any]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    partition_key: str  # YYYYMM形式

class AnalysisResultPartitioned(BaseModel):
    result_id: UUID
    task_id: UUID
    source_id: UUID
    analysis_type: str
    status: str
    mongodb_collection: str
    mongodb_document_id: str
    summary_data: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    partition_key: str  # YYYYMM形式