from typing import Dict, Any, List, Optional, Callable
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import numpy as np
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """最適化戦略の種類"""
    ADAPTIVE = "adaptive"      # 適応的最適化
    PREDICTIVE = "predictive"  # 予測的最適化
    RESOURCE = "resource"      # リソース最適化
    PERFORMANCE = "performance"  # パフォーマンス最適化

@dataclass
class StrategyConfig:
    """最適化戦略の設定"""
    strategy_type: OptimizationStrategy = OptimizationStrategy.ADAPTIVE
    learning_rate: float = 0.1
    window_size: int = 100
    threshold: float = 0.8
    max_iterations: int = 1000
    target_metrics: List[str] = None

    def __post_init__(self):
        if self.target_metrics is None:
            self.target_metrics = ['cpu_usage', 'memory_usage', 'response_time']

class OptimizationEngine:
    """最適化エンジンを管理するクラス"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self._history: Dict[str, List[float]] = {
            metric: [] for metric in config.target_metrics
        }
        self._current_state: Dict[str, float] = {}
        self._optimization_functions: Dict[str, Callable] = {
            OptimizationStrategy.ADAPTIVE.value: self._adaptive_optimization,
            OptimizationStrategy.PREDICTIVE.value: self._predictive_optimization,
            OptimizationStrategy.RESOURCE.value: self._resource_optimization,
            OptimizationStrategy.PERFORMANCE.value: self._performance_optimization
        }

    async def optimize(self, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """最適化の実行"""
        try:
            # メトリクスの更新
            self._update_metrics(current_metrics)
            
            # 最適化戦略の実行
            optimization_func = self._optimization_functions.get(
                self.config.strategy_type.value,
                self._adaptive_optimization
            )
            
            result = await optimization_func(current_metrics)
            
            # 最適化結果の検証
            validated_result = await self._validate_optimization(result)
            
            return validated_result

        except Exception as e:
            logger.error(f"最適化実行でエラー: {str(e)}")
            return {}

    def _update_metrics(self, metrics: Dict[str, Any]):
        """メトリクス履歴の更新"""
        try:
            for metric in self.config.target_metrics:
                if metric in metrics:
                    self._history[metric].append(metrics[metric])
                    if len(self._history[metric]) > self.config.window_size:
                        self._history[metric].pop(0)
                    self._current_state[metric] = metrics[metric]
        except Exception as e:
            logger.error(f"メトリクス更新でエラー: {str(e)}")

    async def _adaptive_optimization(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """適応的最適化戦略"""
        try:
            optimized = {}
            
            for metric in self.config.target_metrics:
                if metric not in self._history:
                    continue
                    
                history = self._history[metric]
                if not history:
                    continue

                # トレンド分析
                trend = self._calculate_trend(history)
                
                # 適応的調整
                if trend > 0:  # 増加傾向
                    adjustment = -self.config.learning_rate
                elif trend < 0:  # 減少傾向
                    adjustment = self.config.learning_rate
                else:
                    adjustment = 0

                # 新しい値の計算
                current = self._current_state.get(metric, 0)
                optimized[metric] = max(0, current + adjustment)

            return optimized
        except Exception as e:
            logger.error(f"適応的最適化でエラー: {str(e)}")
            return {}

    async def _predictive_optimization(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """予測的最適化戦略"""
        try:
            predictions = {}
            
            for metric in self.config.target_metrics:
                if metric not in self._history:
                    continue
                    
                history = self._history[metric]
                if len(history) < 2:
                    continue

                # 時系列予測
                prediction = self._predict_next_value(history)
                
                # 最適値の予測
                optimal = self._calculate_optimal_value(prediction, metric)
                
                predictions[metric] = optimal

            return predictions
        except Exception as e:
            logger.error(f"予測的最適化でエラー: {str(e)}")
            return {}

    async def _resource_optimization(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """リソース最適化戦略"""
        try:
            optimized = {}
            
            # リソース使用率の分析
            cpu_usage = metrics.get('cpu_usage', 0)
            memory_usage = metrics.get('memory_usage', 0)
            
            # リソース配分の最適化
            if cpu_usage > self.config.threshold:
                optimized['batch_size'] = self._reduce_batch_size()
                optimized['concurrent_tasks'] = self._reduce_concurrency()
            elif memory_usage > self.config.threshold:
                optimized['cache_size'] = self._optimize_cache_size()
                optimized['buffer_size'] = self._optimize_buffer_size()
            else:
                optimized['batch_size'] = self._increase_batch_size()
                optimized['concurrent_tasks'] = self._increase_concurrency()

            return optimized
        except Exception as e:
            logger.error(f"リソース最適化でエラー: {str(e)}")
            return {}

    async def _performance_optimization(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """パフォーマンス最適化戦略"""
        try:
            optimized = {}
            
            # パフォーマンスメトリクスの分析
            response_time = metrics.get('response_time', 0)
            throughput = metrics.get('throughput', 0)
            
            # パフォーマンスパラメータの最適化
            if response_time > self.config.threshold:
                optimized['queue_size'] = self._optimize_queue_size()
                optimized['timeout'] = self._optimize_timeout()
            
            if throughput < self.config.threshold:
                optimized['worker_count'] = self._optimize_worker_count()
                optimized['buffer_size'] = self._optimize_buffer_size()

            return optimized
        except Exception as e:
            logger.error(f"パフォーマンス最適化でエラー: {str(e)}")
            return {}

    def _calculate_trend(self, history: List[float]) -> float:
        """トレンドの計算"""
        try:
            if len(history) < 2:
                return 0
            return np.polyfit(range(len(history)), history, 1)[0]
        except Exception as e:
            logger.error(f"トレンド計算でエラー: {str(e)}")
            return 0

    def _predict_next_value(self, history: List[float]) -> float:
        """次の値の予測"""
        try:
            if len(history) < 2:
                return history[-1] if history else 0
                
            # 線形回帰による予測
            x = np.array(range(len(history)))
            y = np.array(history)
            coefficients = np.polyfit(x, y, 1)
            return np.polyval(coefficients, len(history))
        except Exception as e:
            logger.error(f"値予測でエラー: {str(e)}")
            return 0

    async def _validate_optimization(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """最適化結果の検証"""
        try:
            validated = {}
            
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    # 数値の範囲チェック
                    validated[key] = max(0, min(value, 100))
                else:
                    validated[key] = value

            return validated
        except Exception as e:
            logger.error(f"最適化検証でエラー: {str(e)}")
            return result 