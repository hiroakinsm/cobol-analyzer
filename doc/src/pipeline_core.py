# /home/administrator/cobol-analyzer/src/pipeline/pipeline_core.py
# /srv/cobol-analyzer/src/pipeline/core.py

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
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import aiodebug
import structlog
from contextvars import ContextVar

class RetryStrategy(Enum):
    """リトライ戦略"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"

@dataclass
class RetryConfig:
    """リトライ設定"""
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    jitter: bool = True

class PipelineError(Exception):
    """パイプラインエラーの基底クラス"""
    def __init__(self, message: str, task_id: UUID = None, 
                 recoverable: bool = True, retry_count: int = 0):
        self.message = message
        self.task_id = task_id
        self.recoverable = recoverable
        self.retry_count = retry_count
        super().__init__(self.message)

class ErrorRecoveryManager:
    """エラーリカバリー管理"""
    def __init__(self, retry_config: RetryConfig):
        self.config = retry_config
        self.logger = structlog.get_logger()
        self.error_counts: Dict[UUID, int] = {}
        self.recovery_strategies: Dict[str, Callable] = {}

    def register_recovery_strategy(self, error_type: str, strategy: Callable):
        """リカバリー戦略の登録"""
        self.recovery_strategies[error_type] = strategy

    async def handle_error(self, error: Exception, task_id: UUID) -> bool:
        """エラー処理"""
        error_type = type(error).__name__
        self.error_counts[task_id] = self.error_counts.get(task_id, 0) + 1

        self.logger.error("Pipeline error occurred",
                         error_type=error_type,
                         task_id=str(task_id),
                         retry_count=self.error_counts[task_id])

        if self.error_counts[task_id] > self.config.max_attempts:
            return False

        if strategy := self.recovery_strategies.get(error_type):
            try:
                await strategy(error, task_id)
                return True
            except Exception as e:
                self.logger.error("Recovery strategy failed",
                                error=str(e),
                                task_id=str(task_id))
                return False

        return isinstance(error, PipelineError) and error.recoverable

class TaskContext:
    """タスクコンテキスト"""
    def __init__(self,
                 task_id: UUID,
                 source_id: UUID,
                 priority: TaskPriority,
                 created_at: datetime,
                 timeout: int = 3600,
                 max_retries: int = 3,
                 retry_count: int = 0,
                 metadata: Optional[Dict[str, Any]] = None):
        self.task_id = task_id
        self.source_id = source_id
        self.priority = priority
        self.created_at = created_at
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_count = retry_count
        self.metadata = metadata or {}
        self.error_history: List[Dict[str, Any]] = []
        self.checkpoint_data: Dict[str, Any] = {}

    def add_error(self, error: Exception):
        """エラー履歴の追加"""
        self.error_history.append({
            "error_type": type(error).__name__,
            "message": str(error),
            "timestamp": datetime.utcnow(),
            "retry_count": self.retry_count
        })

    def save_checkpoint(self, key: str, data: Any):
        """チェックポイントの保存"""
        self.checkpoint_data[key] = {
            "data": data,
            "timestamp": datetime.utcnow()
        }

    def get_checkpoint(self, key: str) -> Optional[Any]:
        """チェックポイントの取得"""
        if checkpoint := self.checkpoint_data.get(key):
            return checkpoint["data"]
        return None

current_task_context: ContextVar[Optional[TaskContext]] = ContextVar('current_task_context', default=None)

class TaskManager:
    """タスク管理"""
    def __init__(self,
                 db_functions,
                 retry_config: RetryConfig,
                 logger=None):
        self.db = db_functions
        self.logger = logger or structlog.get_logger()
        self.active_tasks: Dict[UUID, asyncio.Task] = {}
        self.task_queue = asyncio.PriorityQueue()
        self.processing_semaphore = asyncio.Semaphore(4)
        self.error_recovery = ErrorRecoveryManager(retry_config)
        self.task_monitors: Dict[UUID, asyncio.Task] = {}

    async def submit_task(self,
                         context: TaskContext,
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
            
            # タスク監視の開始
            self.start_task_monitor(context.task_id)
            
            return context.task_id

        except Exception as e:
            self.logger.error("Task submission failed",
                            error=str(e),
                            task_id=str(context.task_id))
            raise

    def start_task_monitor(self, task_id: UUID):
        """タスク監視の開始"""
        monitor_task = asyncio.create_task(
            self._monitor_task(task_id)
        )
        self.task_monitors[task_id] = monitor_task

    async def _monitor_task(self, task_id: UUID):
        """タスク監視"""
        try:
            while True:
                await asyncio.sleep(60)  # 1分ごとにチェック
                if task_id not in self.active_tasks:
                    break
                    
                task = self.active_tasks[task_id]
                if task.done():
                    break
                    
                # タイムアウトチェック
                context = current_task_context.get()
                if context and self._is_task_timeout(context):
                    await self._handle_timeout(context, task)
                    break

        except asyncio.CancelledError:
            pass
        finally:
            self.task_monitors.pop(task_id, None)

    def _is_task_timeout(self, context: TaskContext) -> bool:
        """タイムアウトチェック"""
        elapsed = datetime.utcnow() - context.created_at
        return elapsed.total_seconds() > context.timeout

    async def _handle_timeout(self,
                            context: TaskContext,
                            task: asyncio.Task):
        """タイムアウト処理"""
        task.cancel()
        error = PipelineError(
            "Task timeout",
            context.task_id,
            recoverable=True
        )
        context.add_error(error)
        await self._handle_task_error(context, error)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=10),
        retry=retry_if_exception_type(PipelineError),
        before_sleep=before_sleep_log(logging.getLogger(), logging.INFO),
        after=after_log(logging.getLogger(), logging.INFO)
    )
    async def _execute_task(self,
                           context: TaskContext,
                           handler: Callable) -> None:
        """タスクの実行"""
        try:
            current_task_context.set(context)
            
            # タスク開始を記録
            await self.db.update_task_status(
                context.task_id,
                TaskStatus.RUNNING
            )

            # チェックポイントの復元
            if checkpoint_data := context.get_checkpoint("last_state"):
                context.metadata["restored_state"] = checkpoint_data

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
            self.logger.error("Task timeout",
                            task_id=str(context.task_id))
            await self._handle_task_error(
                context,
                PipelineError("Task timeout", context.task_id)
            )
            raise

        except Exception as e:
            self.logger.error("Task execution failed",
                            error=str(e),
                            task_id=str(context.task_id))
            await self._handle_task_error(context, e)
            raise

        finally:
            current_task_context.set(None)
            self.active_tasks.pop(context.task_id, None)

    async def _handle_task_error(self,
                                context: TaskContext,
                                error: Exception):
        """タスクエラーの処理"""
        try:
            # エラー履歴の記録
            context.add_error(error)
            
            # リカバリー試行
            if await self.error_recovery.handle_error(error, context.task_id):
                context.retry_count += 1
                await self.db.update_task_status(
                    context.task_id,
                    TaskStatus.RETRY,
                    error="Retry after error"
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
                    error=str(error)
                )

        except Exception as e:
            self.logger.error("Error handling failed",
                            error=str(e),
                            task_id=str(context.task_id))