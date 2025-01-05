# /home/administrator/cobol-analyzer/src/api/client.py
# COBOL Analysis API Client.py

import aiohttp
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from uuid import UUID
from dataclasses import dataclass, field
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import backoff
from prometheus_client import Counter, Histogram
import jwt
from aiohttp_retry import RetryClient, ExponentialRetry

# メトリクス定義
API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['endpoint', 'status'])
API_LATENCY = Histogram('api_request_duration_seconds', 'API request duration')

@dataclass
class AnalysisConfig:
    """解析設定"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1
    max_concurrent_requests: int = 10
    connection_timeout: int = 10
    read_timeout: int = 30
    pool_size: int = 100
    keepalive_timeout: int = 30
    ssl_verify: bool = True
    compress: bool = True
    token_refresh_margin: int = 300  # トークン更新マージン（秒）

@dataclass
class AnalysisTask:
    """解析タスク情報"""
    task_id: UUID
    status: str
    created_at: datetime
    details: Optional[Dict[str, Any]] = None
    progress: float = 0.0
    estimated_completion: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class APIError(Exception):
    """API エラーの基底クラス"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(self.message)

class RetryableError(APIError):
    """再試行可能なエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None, retry_count: int = 0):
        super().__init__(message, status_code, response_body)
        self.retry_count = retry_count
        self.retryable = True

    def increment_retry(self):
        """リトライ回数をインクリメント"""
        self.retry_count += 1
        return self.retry_count

    def should_retry(self, max_retries: int) -> bool:
        """リトライすべきかの判定"""
        return self.retry_count < max_retries

class NonRetryableError(APIError):
    """再試行不可能なエラー"""
    def __init__(self, message: str, status_code: Optional[int] = None,
                 response_body: Optional[str] = None, error_code: str = ""):
        super().__init__(message, status_code, response_body)
        self.error_code = error_code
        self.retryable = False

    def get_error_details(self) -> Dict[str, Any]:
        """エラー詳細の取得"""
        return {
            "message": self.message,
            "status_code": self.status_code,
            "error_code": self.error_code,
            "response_body": self.response_body
        }

class TokenRefreshError(NonRetryableError):
    """トークン更新エラー"""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(
            message=message,
            status_code=401,
            error_code="TOKEN_REFRESH_ERROR"
        )
        self.original_error = original_error

    def get_refresh_context(self) -> Dict[str, Any]:
        """トークン更新コンテキストの取得"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "original_error": str(self.original_error) if self.original_error else None,
            "error_details": self.get_error_details()
        }

class AnalysisApiClient:
    """COBOL解析APIクライアント"""
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.retry_client: Optional[RetryClient] = None
        self.logger = logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        self.token_cache: Dict[str, tuple[str, datetime]] = {}
        self.token_refresh_lock = asyncio.Lock()

    async def __aenter__(self):
        """コンテキストマネージャーのエントリー"""
        if not self.session:
            retry_options = ExponentialRetry(
                attempts=self.config.max_retries,
                start_timeout=self.config.retry_delay,
                max_timeout=30,
                factor=2.0
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=self.config.connection_timeout,
                sock_read=self.config.read_timeout
            )
            
            connector = aiohttp.TCPConnector(
                limit=self.config.pool_size,
                ssl=self.config.ssl_verify,
                keepalive_timeout=self.config.keepalive_timeout
            )

            self.session = aiohttp.ClientSession(
                base_url=self.config.base_url,
                headers=await self._get_headers(),
                timeout=timeout,
                connector=connector,
                raise_for_status=True,
                compress=self.config.compress
            )

            self.retry_client = RetryClient(
                client_session=self.session,
                retry_options=retry_options
            )

        return self

    async def _get_headers(self) -> Dict[str, str]:
        """ヘッダーの生成"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "COBOL-Analysis-API-Client/1.0"
        }
        
        if self.config.api_key:
            token = await self._get_valid_token()
            headers["Authorization"] = f"Bearer {token}"
        
        return headers

    async def _get_valid_token(self) -> str:
        """有効な認証トークンの取得"""
        cache_key = self.config.api_key
        if cache_key in self.token_cache:
            token, expiry = self.token_cache[cache_key]
            if expiry > datetime.utcnow() + timedelta(seconds=self.config.token_refresh_margin):
                return token

        async with self.token_refresh_lock:
            try:
                return await self._refresh_token()
            except Exception as e:
                self.logger.error(f"Token refresh failed: {str(e)}")
                raise TokenRefreshError("Failed to refresh token")

    async def _refresh_token(self) -> str:
        """トークンの更新"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config.base_url}/api/token",
                    json={"api_key": self.config.api_key},
                    ssl=self.config.ssl_verify
                ) as response:
                    if response.status != 200:
                        raise TokenRefreshError("Invalid response from token endpoint")
                    
                    data = await response.json()
                    token = data["access_token"]
                    expiry = datetime.utcnow() + timedelta(seconds=data["expires_in"])
                    
                    # キャッシュの更新
                    self.token_cache[self.config.api_key] = (token, expiry)
                    return token

        except aiohttp.ClientError as e:
            raise TokenRefreshError(f"Network error during token refresh: {str(e)}")
        except KeyError as e:
            raise TokenRefreshError(f"Invalid token response format: {str(e)}")
        except Exception as e:
            raise TokenRefreshError(f"Unexpected error during token refresh: {str(e)}")

    @retry(
        retry=retry_if_exception_type(RetryableError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        before=before_sleep_log(logging.getLogger(), logging.INFO),
        after=after_log(logging.getLogger(), logging.INFO)
    )
    async def start_single_analysis(
        self,
        source_id: UUID,
        analysis_types: List[str],
        options: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None
    ) -> AnalysisTask:
        """単一ソース解析の開始"""
        async with self.semaphore:
            try:
                API_REQUESTS.labels(endpoint="/analysis/single", status="attempt").inc()

                with API_LATENCY.time():
                    payload = {
                        "source_id": str(source_id),
                        "analysis_types": analysis_types,
                        "options": options or {},
                        "callback_url": callback_url
                    }

                    async with self.retry_client.post(
                        "/api/v1/analysis/single",
                        json=payload
                    ) as response:
                        if response.status == 202:
                            data = await response.json()
                            API_REQUESTS.labels(
                                endpoint="/analysis/single",
                                status="success"
                            ).inc()
                            
                            return AnalysisTask(
                                task_id=UUID(data["task_id"]),
                                status=data["status"],
                                created_at=datetime.fromisoformat(data["created_at"]),
                                details=data.get("details"),
                                metadata={"request_id": data.get("request_id")}
                            )
                        else:
                            error_data = await response.json()
                            API_REQUESTS.labels(
                                endpoint="/analysis/single",
                                status="error"
                            ).inc()
                            
                            if response.status in {408, 429, 503}:
                                raise RetryableError(
                                    f"Retryable error: {error_data.get('error')}",
                                    response.status,
                                    str(error_data)
                                )
                            else:
                                raise NonRetryableError(
                                    f"API error: {error_data.get('error')}",
                                    response.status,
                                    str(error_data)
                                )

            except aiohttp.ClientError as e:
                API_REQUESTS.labels(
                    endpoint="/analysis/single",
                    status="network_error"
                ).inc()
                raise RetryableError(f"Network error: {str(e)}")
            
            except asyncio.TimeoutError:
                API_REQUESTS.labels(
                    endpoint="/analysis/single",
                    status="timeout"
                ).inc()
                raise RetryableError("Request timeout")

            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                raise

    async def wait_for_completion(
        self,
        task_id: UUID,
        polling_interval: float = 1.0,
        timeout: Optional[float] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """解析完了を待機"""
        start_time = datetime.utcnow()
        last_progress = 0.0

        while True:
            try:
                status = await self.get_task_status(task_id)
                current_progress = status.get("progress", 0.0)

                if status["status"] == "completed":
                    return await self.get_task_result(task_id)
                elif status["status"] == "failed":
                    raise AnalysisFailedError(
                        f"Analysis failed: {status.get('error')}",
                        details=status.get("error_details")
                    )

                # 進捗コールバック
                if progress_callback and current_progress > last_progress:
                    await progress_callback(
                        current_progress,
                        status.get("estimated_completion")
                    )
                    last_progress = current_progress

                # タイムアウトチェック
                if timeout:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    if elapsed > timeout:
                        raise TimeoutError(
                            f"Analysis timed out after {timeout} seconds"
                        )

                await asyncio.sleep(polling_interval)

            except Exception as e:
                self.logger.error(f"Error while waiting for completion: {str(e)}")
                raise

    async def get_task_status(self, task_id: UUID) -> Dict[str, Any]:
        """タスク状態の取得"""
        try:
            async with self.retry_client.get(
                f"/api/v1/analysis/status/{task_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise TaskNotFoundError(f"Task not found: {task_id}")
                else:
                    error_data = await response.json()
                    raise APIError(
                        f"API error: {error_data.get('error')}",
                        response.status,
                        str(error_data)
                    )
        except Exception as e:
            self.logger.error(f"Status check failed: {str(e)}")
            raise

    @backoff.on_exception(
        backoff.expo,
        (RetryableError, aiohttp.ClientError),
        max_tries=3
    )
    async def get_task_result(self, task_id: UUID) -> Dict[str, Any]:
        """解析結果の取得"""
        try:
            async with self.retry_client.get(
                f"/api/v1/analysis/{task_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ResultNotFoundError(f"Result not found: {task_id}")
                else:
                    error_data = await response.json()
                    raise APIError(
                        f"API error: {error_data.get('error')}",
                        response.status,
                        str(error_data)
                    )

        except Exception as e:
            self.logger.error(f"Result retrieval failed: {str(e)}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのイグジット"""
        if self.session:
            if self.retry_client:
                await self.retry_client.close()
            await self.session.close()
            self.session = None
            self.retry_client = None

    def __del__(self):
        """リソースのクリーンアップ"""
        if self.session and not self.session.closed:
            asyncio.create_task(self.session.close())

# エラークラスの追加定義
class AnalysisFailedError(NonRetryableError):
    """解析失敗エラー"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details

class TaskNotFoundError(NonRetryableError):
    """タスク未検出エラー"""
    def __init__(self, task_id: Union[str, UUID], message: Optional[str] = None):
        super().__init__(
            message=message or f"Task not found: {task_id}",
            status_code=404,
            error_code="TASK_NOT_FOUND"
        )
        self.task_id = str(task_id)

    def get_task_context(self) -> Dict[str, Any]:
        """タスクコンテキストの取得"""
        return {
            "task_id": self.task_id,
            "error_details": self.get_error_details(),
            "timestamp": datetime.utcnow().isoformat()
        }

class ResultNotFoundError(NonRetryableError):
    """結果未検出エラー"""
    def __init__(self, task_id: Union[str, UUID], message: Optional[str] = None):
        super().__init__(
            message=message or f"Result not found for task: {task_id}",
            status_code=404,
            error_code="RESULT_NOT_FOUND"
        )
        self.task_id = str(task_id)

    def get_result_context(self) -> Dict[str, Any]:
        """結果コンテキストの取得"""
        return {
            "task_id": self.task_id,
            "error_details": self.get_error_details(),
            "timestamp": datetime.utcnow().isoformat()
        }