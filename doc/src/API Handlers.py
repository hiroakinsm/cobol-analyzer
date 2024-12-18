```python
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4, validator
from datetime import datetime
import logging

# リクエストモデル
class AnalysisRequestModel(BaseModel):
    source_id: UUID4
    analysis_types: List[str]
    options: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 0
    callback_url: Optional[str] = None

    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        valid_types = {t.value for t in AnalysisType}
        if not all(t in valid_types for t in v):
            raise ValueError(f"Invalid analysis type. Valid types are: {valid_types}")
        return v

class BatchAnalysisRequestModel(BaseModel):
    source_ids: List[UUID4]
    analysis_types: List[str]
    options: Optional[Dict[str, Any]] = {}
    priority: Optional[int] = 0
    callback_url: Optional[str] = None

    @validator('source_ids')
    def validate_source_ids(cls, v):
        if len(v) > 100:  # 一度に処理できる最大数を制限
            raise ValueError("Maximum 100 sources can be processed in one batch")
        return v

# レスポンスモデル
class AnalysisResponseModel(BaseModel):
    task_id: UUID4
    status: str
    created_at: datetime
    details: Optional[Dict[str, Any]] = None

class AnalysisResultModel(BaseModel):
    integration_id: UUID4
    source_ids: List[UUID4]
    analysis_types: List[str]
    status: str
    results: Dict[str, Any]
    created_at: datetime

# APIアプリケーション
app = FastAPI(
    title="COBOL Analysis API",
    description="API for analyzing COBOL source code",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 依存性注入
def get_analysis_factory():
    # 実際の実装では適切な依存関係を注入
    engine_manager = AnalysisEngineManager()
    result_integrator = ResultIntegrator()
    ast_accessor = ASTAccessor()
    return AnalysisUseCaseFactory(engine_manager, result_integrator, ast_accessor)

# エンドポイント
@app.post("/api/v1/analysis/single", response_model=AnalysisResponseModel)
async def start_single_analysis(
    request: AnalysisRequestModel,
    background_tasks: BackgroundTasks,
    factory: AnalysisUseCaseFactory = Depends(get_analysis_factory)
):
    """単一ソース解析の開始"""
    try:
        usecase = factory.create_single_source_usecase()
        task_id = uuid4()
        
        background_tasks.add_task(
            usecase.execute,
            AnalysisRequest(
                source_id=request.source_id,
                analysis_types=[AnalysisType(t) for t in request.analysis_types],
                options=request.options,
                priority=request.priority,
                callback_url=request.callback_url
            )
        )

        return AnalysisResponseModel(
            task_id=task_id,
            status="accepted",
            created_at=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/analysis/batch", response_model=AnalysisResponseModel)
async def start_batch_analysis(
    request: BatchAnalysisRequestModel,
    background_tasks: BackgroundTasks,
    factory: AnalysisUseCaseFactory = Depends(get_analysis_factory)
):
    """バッチ解析の開始"""
    try:
        usecase = factory.create_batch_usecase()
        task_id = uuid4()

        background_tasks.add_task(
            usecase.execute,
            BatchAnalysisRequest(
                source_ids=request.source_ids,
                analysis_types=[AnalysisType(t) for t in request.analysis_types],
                options=request.options,
                priority=request.priority,
                callback_url=request.callback_url
            )
        )

        return AnalysisResponseModel(
            task_id=task_id,
            status="accepted",
            created_at=datetime.utcnow()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Failed to start batch analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/analysis/{task_id}", response_model=AnalysisResultModel)
async def get_analysis_result(
    task_id: UUID4 = Path(..., description="The ID of the analysis task"),
    factory: AnalysisUseCaseFactory = Depends(get_analysis_factory)
):
    """解析結果の取得"""
    try:
        # 結果の取得ロジック
        result = await _get_analysis_result(task_id)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis result not found for task_id: {task_id}"
            )
        return result

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to get analysis result: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/analysis/status/{task_id}")
async def get_analysis_status(
    task_id: UUID4 = Path(..., description="The ID of the analysis task")
):
    """解析状態の取得"""
    try:
        # 状態の取得ロジック
        status = await _get_analysis_status(task_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis task not found: {task_id}"
            )
        return {"status": status}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to get analysis status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/analysis/cancel/{task_id}")
async def cancel_analysis(
    task_id: UUID4 = Path(..., description="The ID of the analysis task"),
    factory: AnalysisUseCaseFactory = Depends(get_analysis_factory)
):
    """解析のキャンセル"""
    try:
        # キャンセル処理ロジック
        success = await _cancel_analysis(task_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis task not found or already completed: {task_id}"
            )
        return {"status": "cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Failed to cancel analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# エラーハンドラー
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```