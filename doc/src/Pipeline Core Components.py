from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID
import asyncio
import logging
from enum import Enum
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

class TaskPriority(Enum):
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class TaskContext:
    """タスクコンテキスト"""
    task_id: UUID
    source_id: UUID
    priority: TaskPriority
    created_at: datetime
    timeout: int = 3600  # デフォルトタイムアウト: 1時間
    max_retries: int = 3
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class PipelineError(Exception):
    """パイプラインエラーの基底クラス"""
    def __init__(self, message: str, task_id: UUID = None, 
                 recoverable: bool = True):
        self.message = message
        self.task_id = task_id
        self.recoverable = recoverable
        super().__init__(self.message)

class TaskManager:
    """タスク管理"""
    def __init__(self, db_functions, logger=None):
        self.db = db_functions
        self.logger = logger or logging.getLogger(__name__)
        self.active_tasks: Dict[UUID, asyncio.Task] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.processing_semaphore = asyncio.Semaphore(4)  # 同時実行数制限

    async def submit_task(self, context: TaskContext, 
                         handler: Callable) -> UUID:
        """タスクの投入"""
        try:
            # タスクの登録
            await self.db.store_task(context)
            # キューに追加
            await self.task_queue.put((
                context.priority.value,
                context,
                handler
            ))
            return context.task_id
        except Exception as e:
            self.logger.error(f"Task submission failed: {str(e)}")
            raise

    async def process_tasks(self):
        """タスク処理のメインループ"""
        while True:
            try:
                async with self.processing_semaphore:
                    _, context, handler = await self.task_queue.get()
                    task = asyncio.create_task(
                        self._execute_task(context, handler)
                    )
                    self.active_tasks[context.task_id] = task
                    self.task_queue.task_done()
            except Exception as e:
                self.logger.error(f"Task processing error: {str(e)}")
                await asyncio.sleep(1)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=10),
        retry=retry_if_exception_type(PipelineError)
    )
    async def _execute_task(self, context: TaskContext, 
                           handler: Callable) -> None:
        """タスクの実行"""
        try:
            # タスク開始を記録
            await self.db.update_task_status(
                context.task_id,
                TaskStatus.RUNNING
            )

            # タイムアウト付きで実行
            async with asyncio.timeout(context.timeout):
                result = await handler(context)

            # 成功を記録
            await self.db.update_task_status(
                context.task_id,
                TaskStatus.COMPLETED,
                result=result
            )

        except asyncio.TimeoutError:
            self.logger.error(f"Task {context.task_id} timed out")
            await self._handle_timeout(context)
            raise PipelineError("Task timeout", context.task_id)

        except Exception as e:
            self.logger.error(f"Task {context.task_id} failed: {str(e)}")
            await self._handle_error(context, e)
            raise

        finally:
            self.active_tasks.pop(context.task_id, None)

    async def _handle_timeout(self, context: TaskContext):
        """タイムアウト処理"""
        if context.retry_count < context.max_retries:
            context.retry_count += 1
            await self.db.update_task_status(
                context.task_id,
                TaskStatus.RETRY,
                error="Timeout"
            )
            # 再試行用にキューに戻す
            await self.task_queue.put((
                context.priority.value + 1,  # 優先度を下げる
                context,
                handler
            ))
        else:
            await self.db.update_task_status(
                context.task_id,
                TaskStatus.FAILED,
                error="Max retries exceeded"
            )

    async def _handle_error(self, context: TaskContext, error: Exception):
        """エラー処理"""
        if isinstance(error, PipelineError) and not error.recoverable:
            await self.db.update_task_status(
                context.task_id,
                TaskStatus.FAILED,
                error=str(error)
            )
        else:
            await self._handle_timeout(context)

class PipelineStage:
    """パイプラインステージの基底クラス"""
    def __init__(self, name: str, task_manager: TaskManager):
        self.name = name
        self.task_manager = task_manager
        self.logger = logging.getLogger(f"pipeline.{name}")

    async def process(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """ステージの処理を実行"""
        raise NotImplementedError

    async def handle_error(self, context: TaskContext, 
                          error: Exception) -> None:
        """エラーハンドリング"""
        self.logger.error(
            f"Stage {self.name} failed for task {context.task_id}: {str(error)}"
        )
        await self.task_manager.db.store_error(
            context.task_id,
            self.name,
            str(error)
        )

class Pipeline:
    """パイプライン本体"""
    def __init__(self, task_manager: TaskManager):
        self.task_manager = task_manager
        self.stages: List[PipelineStage] = []
        self.logger = logging.getLogger("pipeline")

    def add_stage(self, stage: PipelineStage):
        """ステージの追加"""
        self.stages.append(stage)

    async def execute(self, context: TaskContext, 
                     initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """パイプラインの実行"""
        data = initial_data
        try:
            for stage in self.stages:
                self.logger.info(
                    f"Executing stage {stage.name} for task {context.task_id}"
                )
                data = await stage.process(context, data)
                await self.task_manager.db.store_stage_result(
                    context.task_id,
                    stage.name,
                    data
                )
            return data
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}")
            await self._handle_pipeline_error(context, e)
            raise