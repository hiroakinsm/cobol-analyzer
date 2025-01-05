# /home/administrator/cobol-analyzer/src/models/data.py

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import UUID
from pydantic import BaseModel, Field

class MongoBaseModel(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v)
        }

class ASTData(MongoBaseModel):
    source_id: UUID
    task_id: UUID
    ast_type: str
    ast_data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parser_version: str
    source_file_hash: str

class AnalysisResultData(MongoBaseModel):
    result_id: UUID
    source_id: UUID
    analysis_type: str
    results: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    execution_time: float
    analysis_version: str

class MetricsData(MongoBaseModel):
    source_id: UUID
    metrics_type: str
    metrics_data: Dict[str, Any]
    trend_data: Optional[Dict[str, Any]] = None
    analysis_details: Optional[Dict[str, Any]] = None
    baseline_comparison: Optional[Dict[str, Any]] = None

class EmbeddedAnalysisData(MongoBaseModel):
    source_id: UUID
    element_type: str
    analysis_data: Dict[str, Any]
    location: Dict[str, Any]
    dependencies: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CrossReferenceData(MongoBaseModel):
    source_id: UUID
    reference_type: str
    references: List[Dict[str, Any]]
    dependencies: List[str]
    impact_analysis: Dict[str, Any] = Field(default_factory=dict)
    graph_data: Optional[Dict[str, Any]] = None

class BenchmarkData(MongoBaseModel):
    benchmark_id: UUID
    category: str
    metric_name: str
    benchmark_data: Dict[str, Any]
    threshold_data: Dict[str, Any]
    historical_data: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class IntegratedAnalysisResult(MongoBaseModel):
    integration_id: UUID
    source_ids: List[UUID]
    analysis_types: List[str]
    results: Dict[str, Any]
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]

class RAGAnalysisData(MongoBaseModel):
    source_id: UUID
    content_type: str
    embeddings: List[float]
    content: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    vector_id: str
    similarity_score: Optional[float] = None

class SecurityAnalysisData(MongoBaseModel):
    source_id: UUID
    vulnerability_data: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    compliance_data: Dict[str, Any]
    cve_references: List[str]
    mitigation_suggestions: List[Dict[str, Any]]

class QualityAnalysisData(MongoBaseModel):
    source_id: UUID
    quality_metrics: Dict[str, Any]
    code_smells: List[Dict[str, Any]]
    technical_debt: Dict[str, Any]
    improvement_suggestions: List[Dict[str, Any]]
    historical_trends: Dict[str, Any]

class VisualizationData(MongoBaseModel):
    source_id: UUID
    visualization_type: str
    chart_data: Dict[str, Any]
    layout_config: Dict[str, Any]
    interaction_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class CacheData(MongoBaseModel):
    cache_key: str
    cache_type: str
    data: Dict[str, Any]
    ttl: datetime
    access_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.utcnow)