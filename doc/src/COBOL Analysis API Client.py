```python
import aiohttp
import asyncio
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from uuid import UUID
from dataclasses import dataclass
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

@dataclass
class AnalysisConfig:
    """解析設定"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1

@dataclass
class AnalysisTask:
    """解析タスク情報"""
    task_id: UUID
    status: str
    created_at: datetime
    details: Optional[Dict[str, Any]] = None

class AnalysisApiClient:
    """COBOL解析APIクライアント"""
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """コンテキストマネージャーのエントリー"""
        if not self.session:
            self.session = await self._create_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーのイグジット"""
        if self.session:
            await self.session.close()
            self.session = None

    async def _create_session(self) -> aiohttp.ClientSession:
        """セッションの作成"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        return aiohttp.ClientSession(
            base_url=self.config.base_url,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def start_single_analysis(
        self,
        source_id: UUID,
        analysis_types: List[str],
        options: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None
    ) -> AnalysisTask:
        """単一ソース解析の開始"""
        try:
            if not self.session:
                self.session = await self._create_session()

            payload = {
                "source_id": str(source_id),
                "analysis_types": analysis_types,
                "options": options or {},
                "callback_url": callback_url
            }

            async with self.session.post("/api/v1/analysis/single", json=payload) as response:
                if response.status == 202:
                    data = await response.json()
                    return AnalysisTask(
                        task_id=UUID(data["task_id"]),
                        status=data["status"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        details=data.get("details")
                    )
                else:
                    error_data = await response.json()
                    raise AnalysisApiError(f"API error: {error_data.get('error', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"Failed to start analysis: {str(e)}")
            raise

    async def start_batch_analysis(
        self,
        source_ids: List[UUID],
        analysis_types: List[str],
        options: Optional[Dict[str, Any]] = None,
        callback_url: Optional[str] = None
    ) -> AnalysisTask:
        """バッチ解析の開始"""
        try:
            if not self.session:
                self.session = await self._create_session()

            payload = {
                "source_ids": [str(sid) for sid in source_ids],
                "analysis_types": analysis_types,
                "options": options or {},
                "callback_url": callback_url
            }

            async with self.session.post("/api/v1/analysis/batch", json=payload) as response:
                if response.status == 202:
                    data = await response.json()
                    return AnalysisTask(
                        task_id=UUID(data["task_id"]),
                        status=data["status"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        details=data.get("details")
                    )
                else:
                    error_data = await response.json()
                    raise AnalysisApiError(f"API error: {error_data.get('error', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"Failed to start batch analysis: {str(e)}")
            raise

    async def get_result(self, task_id: UUID) -> Dict[str, Any]:
        """解析結果の取得"""
        try:
            if not self.session:
                self.session = await self._create_session()

            async with self.session.get(f"/api/v1/analysis/{task_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ResultNotFoundError(f"Result not found for task: {task_id}")
                else:
                    error_data = await response.json()
                    raise AnalysisApiError(f"API error: {error_data.get('error', 'Unknown error')}")

        except Exception as e:
            self.logger.error(f"Failed to get result: {str(e)}")
            raise

    async def wait_for_completion(
        self,
        task_id: UUID,
        polling_interval: float = 1.0,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """解析完了を待機"""
        start_time = datetime.utcnow()
        while True:
            try:
                status = await self.get_status(task_id)
                if status["status"] == "completed":
                    return await self.get_result(task_id)
                elif status["status"] == "failed":
                    raise AnalysisFailedError(f"Analysis failed for task: {task_id}")

                if timeout:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    if elapsed > timeout:
                        raise TimeoutError(f"Analysis timed out after {timeout} seconds")

                await asyncio.sleep(polling_interval)

            except Exception as e:
                self.logger.error(f"Error while waiting for completion: {str(e)}")
                raise

# 使用例
async def example_usage():
    config = AnalysisConfig(
        base_url="http://api.example.com",
        api_key="your-api-key"
    )

    async with AnalysisApiClient(config) as client:
        # 単一ソース解析
        task = await client.start_single_analysis(
            source_id=UUID("12345678-1234-5678-1234-567812345678"),
            analysis_types=["structure", "quality", "security"]
        )

        # 結果の待機
        try:
            result = await client.wait_for_completion(
                task.task_id,
                timeout=300  # 5分タイムアウト
            )
            print(f"Analysis completed: {result}")
        except TimeoutError:
            print("Analysis timed out")
        except AnalysisFailedError as e:
            print(f"Analysis failed: {e}")

        # バッチ解析
        batch_task = await client.start_batch_analysis(
            source_ids=[
                UUID("12345678-1234-5678-1234-567812345678"),
                UUID("87654321-4321-8765-4321-876543210987")
            ],
            analysis_types=["structure", "quality"]
        )

        # 結果の待機
        try:
            batch_result = await client.wait_for_completion(
                batch_task.task_id,
                timeout=600  # 10分タイムアウト
            )
            print(f"Batch analysis completed: {batch_result}")
        except Exception as e:
            print(f"Batch analysis failed: {e}")

if __name__ == "__main__":
    asyncio.run(example_usage())
```