from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass
import time
import statistics
from collections import deque

logger = logging.getLogger(__name__)

@dataclass
class OptimizerConfig:
    """最適化の設定"""
    sampling_interval: float = 0.1    # サンプリング間隔（秒）
    window_size: int = 100            # 移動平均のウィンドウサイズ
    batch_size: int = 1000            # バッチ処理サイズ
    compression_threshold: int = 10000 # 圧縮閾値
    max_concurrent_tasks: int = 5      # 最大同時実行タスク数

class PerformanceOptimizer:
    """パフォーマンス最適化を管理するクラス"""
    
    def __init__(self, config: OptimizerConfig):
        self.config = config
        self._performance_metrics = {
            'execution_times': deque(maxlen=config.window_size),
            'memory_usage': deque(maxlen=config.window_size),
            'batch_sizes': deque(maxlen=config.window_size)
        }
        self._semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        self._batch_queue = asyncio.Queue()
        self._is_processing = False

    async def optimize_collection(self, collector):
        """メトリクス収集の最適化"""
        try:
            # サンプリング間隔の動的調整
            optimal_interval = await self._optimize_sampling_interval(collector)
            collector.config.collect_interval = optimal_interval

            # バッチサイズの最適化
            optimal_batch = await self._optimize_batch_size()
            self.config.batch_size = optimal_batch

            # 同時実行数の調整
            await self._adjust_concurrency()

            return {
                'sampling_interval': optimal_interval,
                'batch_size': optimal_batch,
                'concurrent_tasks': self.config.max_concurrent_tasks
            }
        except Exception as e:
            logger.error(f"収集最適化でエラー: {str(e)}")
            return {}

    async def process_metrics_batch(self, metrics: List[Dict[str, Any]]):
        """メトリクスのバッチ処理"""
        try:
            start_time = time.perf_counter()
            
            # バッチをキューに追加
            for item in metrics:
                await self._batch_queue.put(item)
            
            # バッチ処理の実行
            if not self._is_processing:
                self._is_processing = True
                await self._process_batch_queue()
            
            execution_time = time.perf_counter() - start_time
            self._performance_metrics['execution_times'].append(execution_time)
            
            return {
                'processed_items': len(metrics),
                'execution_time': execution_time,
                'batch_size': self.config.batch_size
            }
        except Exception as e:
            logger.error(f"バッチ処理でエラー: {str(e)}")
            return {}

    async def _optimize_sampling_interval(self, collector) -> float:
        """サンプリング間隔の最適化"""
        try:
            # 現在の負荷状況を確認
            current_load = await self._measure_system_load()
            
            # 実行時間の統計を計算
            if self._performance_metrics['execution_times']:
                avg_execution_time = statistics.mean(self._performance_metrics['execution_times'])
                std_execution_time = statistics.stdev(self._performance_metrics['execution_times'])
            else:
                return self.config.sampling_interval

            # 負荷に基づいて間隔を調整
            if current_load > 80:  # 高負荷
                new_interval = min(
                    self.config.sampling_interval * 1.5,
                    avg_execution_time + std_execution_time
                )
            elif current_load < 30:  # 低負荷
                new_interval = max(
                    self.config.sampling_interval * 0.8,
                    avg_execution_time - std_execution_time,
                    0.1  # 最小間隔
                )
            else:
                new_interval = self.config.sampling_interval

            return round(new_interval, 2)
        except Exception as e:
            logger.error(f"サンプリング間隔最適化でエラー: {str(e)}")
            return self.config.sampling_interval

    async def _optimize_batch_size(self) -> int:
        """バッチサイズの最適化"""
        try:
            if not self._performance_metrics['execution_times']:
                return self.config.batch_size

            # 実行時間とバッチサイズの関係を分析
            avg_execution_time = statistics.mean(self._performance_metrics['execution_times'])
            avg_batch_size = statistics.mean(self._performance_metrics['batch_sizes'])
            
            # 効率を計算
            efficiency = avg_execution_time / avg_batch_size if avg_batch_size > 0 else float('inf')
            
            # バッチサイズを調整
            if efficiency > 0.1:  # 効率が悪い
                new_size = int(self.config.batch_size * 0.8)
            elif efficiency < 0.01:  # 効率が良い
                new_size = int(self.config.batch_size * 1.2)
            else:
                new_size = self.config.batch_size

            # 範囲を制限
            return max(100, min(new_size, 10000))
        except Exception as e:
            logger.error(f"バッチサイズ最適化でエラー: {str(e)}")
            return self.config.batch_size

    async def _adjust_concurrency(self):
        """同時実行数の調整"""
        try:
            # システム負荷に基づいて調整
            current_load = await self._measure_system_load()
            
            if current_load > 80:
                self.config.max_concurrent_tasks = max(1, self.config.max_concurrent_tasks - 1)
            elif current_load < 50:
                self.config.max_concurrent_tasks = min(10, self.config.max_concurrent_tasks + 1)
            
            # セマフォの更新
            self._semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        except Exception as e:
            logger.error(f"同時実行数調整でエラー: {str(e)}")

    async def _process_batch_queue(self):
        """バッチキューの処理"""
        try:
            while self._is_processing:
                if self._batch_queue.empty():
                    self._is_processing = False
                    break

                # バッチサイズ分のアイテムを収集
                batch = []
                try:
                    while len(batch) < self.config.batch_size:
                        item = self._batch_queue.get_nowait()
                        batch.append(item)
                except asyncio.QueueEmpty:
                    pass

                if batch:
                    # 並行処理でバッチを処理
                    async with self._semaphore:
                        await self._process_batch(batch)

                    self._performance_metrics['batch_sizes'].append(len(batch))

        except Exception as e:
            logger.error(f"バッチキュー処理でエラー: {str(e)}")
            self._is_processing = False

    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """バッチの処理"""
        try:
            # バッチ処理のロジック
            # 実際の実装ではデータの処理や保存を行う
            await asyncio.sleep(0.1)  # シミュレーション用
        except Exception as e:
            logger.error(f"バッチ処理でエラー: {str(e)}")

    async def _measure_system_load(self) -> float:
        """システム負荷の測定"""
        try:
            # psutilを使用してシステム負荷を測定
            import psutil
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"システム負荷測定でエラー: {str(e)}")
            return 50.0  # デフォルト値 