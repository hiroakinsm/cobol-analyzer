# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/benchmark/benchmark_components.py

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from cachetools import TTLCache
import numpy as np
from .components import (
    BenchmarkType, EvaluationLevel, BenchmarkCriteria, 
    EvaluationResult, BenchmarkManager, MetricsEvaluator
)

class MetricsBenchmarkManager(BenchmarkManager):
    """メトリクス固有のベンチマーク管理"""
    def __init__(self, db_connection, cache_ttl: int = 3600):
        super().__init__(db_connection, cache_ttl)
        self.metrics_thresholds = self._load_metrics_thresholds()

    async def _load_metrics_thresholds(self) -> Dict[str, Dict[str, float]]:
        """メトリクス閾値の読み込み"""
        query = """
            SELECT metric_name, min_value, max_value, target_value
            FROM benchmark_master
            WHERE is_active = true
            ORDER BY metric_name
        """
        try:
            async with self.db.acquire() as conn:
                rows = await conn.fetch(query)
                thresholds = {}
                for row in rows:
                    thresholds[row['metric_name']] = {
                        'min': row['min_value'],
                        'max': row['max_value'],
                        'target': row['target_value']
                    }
                return thresholds
        except Exception as e:
            self.logger.error(f"Failed to load metrics thresholds: {str(e)}")
            raise

class COBOLMetricsEvaluator(MetricsEvaluator):
    """COBOL固有のメトリクス評価"""
    def __init__(self, benchmark_manager: MetricsBenchmarkManager):
        super().__init__(benchmark_manager)
        self.cobol_specific_evaluators = {
            'cyclomatic_complexity': self._evaluate_cyclomatic_complexity,
            'halstead_metrics': self._evaluate_halstead_metrics,
            'maintainability_index': self._evaluate_maintainability_index
        }

    async def _evaluate_cyclomatic_complexity(self, value: float) -> EvaluationResult:
        """循環的複雑度の評価"""
        thresholds = await self.benchmark_manager.get_criteria('cyclomatic_complexity')
        level = self._determine_complexity_level(value, thresholds)
        return EvaluationResult(
            metric_name='cyclomatic_complexity',
            actual_value=value,
            benchmark_value=thresholds.target_value,
            level=level,
            score=self._calculate_complexity_score(value, thresholds),
            details=self._create_complexity_details(value, thresholds)
        )

    async def _evaluate_halstead_metrics(self, metrics: Dict[str, float]) -> EvaluationResult:
        """Halsteadメトリクスの評価"""
        thresholds = await self.benchmark_manager.get_criteria('halstead_metrics')
        volume = metrics.get('volume', 0)
        difficulty = metrics.get('difficulty', 0)
        effort = metrics.get('effort', 0)

        level = self._determine_halstead_level(volume, difficulty, effort, thresholds)
        return EvaluationResult(
            metric_name='halstead_metrics',
            actual_value=effort,
            benchmark_value=thresholds.target_value,
            level=level,
            score=self._calculate_halstead_score(volume, difficulty, effort, thresholds),
            details=self._create_halstead_details(metrics, thresholds)
        )

    async def _evaluate_maintainability_index(self, value: float) -> EvaluationResult:
        """保守性指標の評価"""
        thresholds = await self.benchmark_manager.get_criteria('maintainability_index')
        level = self._determine_maintainability_level(value, thresholds)
        return EvaluationResult(
            metric_name='maintainability_index',
            actual_value=value,
            benchmark_value=thresholds.target_value,
            level=level,
            score=self._calculate_maintainability_score(value, thresholds),
            details=self._create_maintainability_details(value, thresholds)
        )

class BenchmarkResultProcessor:
    """ベンチマーク結果の処理"""
    def __init__(self, evaluator: COBOLMetricsEvaluator):
        self.evaluator = evaluator
        self.logger = logging.getLogger(__name__)

    async def process_results(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """結果の処理と集約"""
        try:
            processed_results = {}
            for metric_name, value in metrics.items():
                if metric_name in self.evaluator.cobol_specific_evaluators:
                    evaluator_func = self.evaluator.cobol_specific_evaluators[metric_name]
                    result = await evaluator_func(value)
                    processed_results[metric_name] = result

            return {
                'results': processed_results,
                'summary': self._create_summary(processed_results),
                'recommendations': self._generate_recommendations(processed_results)
            }

        except Exception as e:
            self.logger.error(f"Failed to process benchmark results: {str(e)}")
            raise

    def _create_summary(self, results: Dict[str, EvaluationResult]) -> Dict[str, Any]:
        """サマリーの作成"""
        critical_issues = []
        warning_issues = []
        
        for metric_name, result in results.items():
            if result.level == EvaluationLevel.CRITICAL:
                critical_issues.append({
                    'metric': metric_name,
                    'value': result.actual_value,
                    'benchmark': result.benchmark_value
                })
            elif result.level == EvaluationLevel.WARNING:
                warning_issues.append({
                    'metric': metric_name,
                    'value': result.actual_value,
                    'benchmark': result.benchmark_value
                })

        return {
            'total_metrics': len(results),
            'critical_issues': critical_issues,
            'warning_issues': warning_issues,
            'average_score': sum(r.score for r in results.values()) / len(results) if results else 0
        }

    def _generate_recommendations(self, results: Dict[str, EvaluationResult]) -> List[Dict[str, Any]]:
        """改善提案の生成"""
        recommendations = []
        for metric_name, result in results.items():
            if result.level in [EvaluationLevel.CRITICAL, EvaluationLevel.WARNING]:
                recommendations.append({
                    'metric': metric_name,
                    'priority': 'high' if result.level == EvaluationLevel.CRITICAL else 'medium',
                    'current_value': result.actual_value,
                    'target_value': result.benchmark_value,
                    'suggestion': self._create_improvement_suggestion(metric_name, result)
                })
        
        return sorted(recommendations, key=lambda x: x['priority'] == 'high', reverse=True)