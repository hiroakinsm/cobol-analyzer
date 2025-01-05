from typing import Dict, Any, List, Optional, Callable
import logging
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
import signal
from asyncio import Task

logger = logging.getLogger(__name__)

@dataclass
class ScheduleConfig:
    """スケジュール設定"""
    analysis_interval: int = 3600  # 解析実行間隔（秒）
    cache_refresh_interval: int = 1800  # キャッシュ更新間隔（秒）
    retry_interval: int = 300  # エラー時のリトライ間隔（秒）
    max_retries: int = 3  # 最大リトライ回数

class AnalysisScheduler:
    """解析とキャッシュ更新のスケジューリングを管理するクラス"""
    
    def __init__(self, 
                 config: ScheduleConfig,
                 analysis_engine,
                 cache_manager,
                 dashboard_generator):
        self.config = config
        self.analysis_engine = analysis_engine
        self.cache_manager = cache_manager
        self.dashboard_generator = dashboard_generator
        self.running = False
        self.tasks: List[Task] = []
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """シグナルハンドラの設定"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """シャットダウン処理"""
        logger.info(f"シグナル {signum} を受信。シャットダウンを開始します。")
        self.running = False
        
    async def start(self):
        """スケジューラーの開始"""
        try:
            self.running = True
            
            # 定期実行タスクの作成
            analysis_task = asyncio.create_task(
                self._run_periodic_analysis()
            )
            cache_task = asyncio.create_task(
                self._run_periodic_cache_refresh()
            )
            
            self.tasks.extend([analysis_task, cache_task])
            
            # タスクの完了を待機
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"スケジューラー実行でエラー: {str(e)}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """スケジューラーのシャットダウン"""
        logger.info("スケジューラーのシャットダウンを開始します")
        self.running = False
        
        # 実行中のタスクをキャンセル
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.tasks.clear()
        logger.info("スケジューラーをシャットダウンしました")

    async def _run_periodic_analysis(self):
        """定期的な解析の実行"""
        while self.running:
            try:
                # 解析対象の取得
                sources = await self._get_analysis_targets()
                
                for source_id in sources:
                    # リトライ処理付きで解析を実行
                    result = await self._execute_with_retry(
                        lambda: self.analysis_engine.analyze_single_source(source_id)
                    )
                    
                    if result:
                        # 解析結果の保存
                        await self._save_analysis_result(result)
                        
                        # ダッシュボードデータの更新
                        await self.dashboard_generator.update_dashboard(result)
                
                await asyncio.sleep(self.config.analysis_interval)
                
            except Exception as e:
                logger.error(f"定期解析でエラー: {str(e)}")
                await asyncio.sleep(self.config.retry_interval)

    async def _run_periodic_cache_refresh(self):
        """定期的なキャッシュ更新の実行"""
        while self.running:
            try:
                await self.cache_manager.refresh_cache(self.dashboard_generator)
                await asyncio.sleep(self.config.cache_refresh_interval)
            except Exception as e:
                logger.error(f"キャッシュ更新でエラー: {str(e)}")
                await asyncio.sleep(self.config.retry_interval)

    async def _get_analysis_targets(self) -> List[str]:
        """解析対象の取得"""
        try:
            # 解析が必要なソースの取得ロジック
            # 実際の実装ではDBから取得など
            return await self.analysis_engine.db_handler.get_pending_analysis_sources()
        except Exception as e:
            logger.error(f"解析対象の取得でエラー: {str(e)}")
            return []

    async def _save_analysis_result(self, result: Any):
        """解析結果の保存"""
        try:
            # 解析結果の永続化
            await self.analysis_engine.db_handler.save_analysis_result(result)
            logger.info(f"解析結果を保存しました: {result.source_id}")
        except Exception as e:
            logger.error(f"解析結果の保存でエラー: {str(e)}")

    async def _execute_with_retry(self, 
                                operation: Callable,
                                max_retries: int = None) -> Optional[Any]:
        """リトライ処理付きで操作を実行"""
        retries = 0
        max_attempts = max_retries or self.config.max_retries
        
        while retries < max_attempts:
            try:
                return await operation()
            except Exception as e:
                retries += 1
                if retries >= max_attempts:
                    logger.error(f"最大リトライ回数に到達: {str(e)}")
                    return None
                
                wait_time = self.config.retry_interval * (2 ** retries)
                logger.warning(f"操作に失敗。{wait_time}秒後にリトライします: {str(e)}")
                await asyncio.sleep(wait_time) 