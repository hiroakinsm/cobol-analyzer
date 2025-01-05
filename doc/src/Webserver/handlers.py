# /home/administrator/cobol-analyzer/src/api/handlers.py
# API Handlers.py

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4, validator, Field
from datetime import datetime, timedelta
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
import jwt
from jose import JWTError
from uuid import uuid4
import asyncio
from prometheus_client import Counter, Histogram
import hashlib
import secrets
from databases import Database

# メトリクス定義
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['endpoint'])
RESPONSE_TIME = Histogram('api_response_time_seconds', 'API response time')

# セキュリティ設定
SECRET_KEY = "your-secret-key"  # 環境変数から読み込むべき
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# データベース設定
DATABASE_URL = "postgresql://user:password@localhost/dbname"
database = Database(DATABASE_URL)

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    disabled: Optional[bool] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SecurityConfig:
    """セキュリティ設定"""
    def __init__(self):
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.rate_limiter = Limiter(key_func=get_remote_address)
        self.pwd_context = hashlib.sha256()

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user(username)
        if not user:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    async def get_user(self, username: str) -> Optional[UserInDB]:
        query = "SELECT * FROM users WHERE username = :username"
        result = await database.fetch_one(query=query, values={"username": username})
        if result:
            return UserInDB(**result)
        return None

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.get_password_hash(plain_password) == hashed_password

    def get_password_hash(self, password: str) -> str:
        self.pwd_context.update(password.encode())
        return self.pwd_context.hexdigest()

    async def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    async def verify_token(self, token: str = Depends(oauth2_scheme)) -> TokenData:
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
        return token_data

# リクエストモデル
class AnalysisRequestModel(BaseModel):
    source_id: UUID4
    analysis_types: List[str]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: Optional[int] = Field(ge=0, le=10, default=0)
    callback_url: Optional[str] = None

    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        valid_types = {t.value for t in AnalysisType}
        if not all(t in valid_types for t in v):
            raise ValueError(f"Invalid analysis type. Valid types: {valid_types}")
        return v

    @validator('callback_url')
    def validate_callback_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("Invalid callback URL format")
        return v

class BatchAnalysisRequestModel(BaseModel):
    source_ids: List[UUID4]
    analysis_types: List[str]
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: Optional[int] = Field(ge=0, le=10, default=0)
    callback_url: Optional[str] = None

    @validator('source_ids')
    def validate_source_ids(cls, v):
        if len(v) > 100:
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
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# セキュリティ設定
security_config = SecurityConfig()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# レート制限設定
limiter = security_config.rate_limiter
app.state.limiter = limiter

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """ログインエンドポイント"""
    user = await security_config.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await security_config.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_analysis_factory() -> AnalysisUseCaseFactory:
    """解析ファクトリの取得"""
    engine_manager = AnalysisEngineManager()
    result_integrator = ResultIntegrator()
    ast_accessor = ASTAccessor()
    return AnalysisUseCaseFactory(engine_manager, result_integrator, ast_accessor)

async def execute_analysis_task(usecase: Any, request: AnalysisRequestModel, task_id: UUID4):
    """解析タスクの実行"""
    try:
        analysis_request = AnalysisRequest(
            source_id=request.source_id,
            analysis_types=[AnalysisType(t) for t in request.analysis_types],
            options=request.options,
            priority=request.priority,
            callback_url=request.callback_url
        )
        
        await usecase.execute(analysis_request)
        
        if request.callback_url:
            await notify_callback(request.callback_url, task_id, "completed")
            
    except Exception as e:
        logging.error(f"Analysis task failed: {str(e)}")
        if request.callback_url:
            await notify_callback(request.callback_url, task_id, "failed", str(e))
        raise

async def notify_callback(url: str, task_id: UUID4, status: str, error: Optional[str] = None):
    """コールバック通知の実行"""
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "task_id": str(task_id),
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            if error:
                payload["error"] = error
                
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logging.error(f"Callback failed: {await response.text()}")
        except Exception as e:
            logging.error(f"Callback request failed: {str(e)}")

@app.post("/api/v1/analysis/single", response_model=AnalysisResponseModel)
@limiter.limit("5/minute")
@RESPONSE_TIME.time()
async def start_single_analysis(
    request: AnalysisRequestModel,
    background_tasks: BackgroundTasks,
    token: TokenData = Depends(security_config.verify_token),
    factory: AnalysisUseCaseFactory = Depends(get_analysis_factory)
):
    """単一ソース解析の開始"""
    REQUEST_COUNT.labels(endpoint="/analysis/single").inc()
    
    try:
        # ユーザーの検証
        user = await security_config.get_user(token.username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        # ソースへのアクセス権限の検証
        if not await validate_source_access(user.username, request.source_id):
            raise HTTPException(status_code=403, detail="Access denied to source")

        # タスクの作成
        task_id = uuid4()
        usecase = factory.create_single_source_usecase()
        
        # タスクをデータベースに記録
        await database.execute(
            """
            INSERT INTO analysis_tasks (task_id, source_id, status, created_at, user_id)
            VALUES (:task_id, :source_id, :status, :created_at, :user_id)
            """,
            {
                "task_id": str(task_id),
                "source_id": str(request.source_id),
                "status": "pending",
                "created_at": datetime.utcnow(),
                "user_id": user.username
            }
        )

        # バックグラウンドタスクの追加
        background_tasks.add_task(
            execute_analysis_task,
            usecase,
            request,
            task_id
        )

        return AnalysisResponseModel(
            task_id=task_id,
            status="accepted",
            created_at=datetime.utcnow(),
            details={
                "user_id": user.username,
                "request_id": str(uuid4())
            }
        )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logging.error(f"Analysis start failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        
@app.get("/api/v1/analysis/{task_id}", response_model=AnalysisResultModel)
@limiter.limit("10/minute")
@RESPONSE_TIME.time()
async def get_analysis_result(
    task_id: UUID4 = Path(..., description="The ID of the analysis task"),
    token: TokenData = Depends(security_config.verify_token)
):
    """解析結果の取得"""
    REQUEST_COUNT.labels(endpoint="/analysis/result").inc()
    
    try:
        # ユーザーの検証
        user = await security_config.get_user(token.username)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid user")

        # タスク情報の取得
        task = await database.fetch_one(
            "SELECT * FROM analysis_tasks WHERE task_id = :task_id",
            {"task_id": str(task_id)}
        )
        
        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis task not found: {task_id}"
            )

        # アクセス権限の検証
        if not await validate_task_access(user.username, task_id):
            raise HTTPException(status_code=403, detail="Access denied to task")

        # 結果の取得
        result = await database.fetch_one(
            """
            SELECT r.*, t.analysis_types
            FROM analysis_results r
            JOIN analysis_tasks t ON r.task_id = t.task_id
            WHERE r.task_id = :task_id
            ""