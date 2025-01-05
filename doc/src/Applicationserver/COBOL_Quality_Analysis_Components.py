# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/quality/components.py

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import logging
import numpy as np
from datetime import datetime

class QualityMetricType(Enum):
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    READABILITY = "readability"
    TESTABILITY = "testability"
    MODULARITY = "modularity"
    DOCUMENTATION = "documentation"

@dataclass
class QualityMetricDefinition:
    """品質メトリクスの定義"""
    name: str
    metric_type: QualityMetricType
    min_value: float
    max_value: float
    target_value: float
    weight: float = 1.0
    thresholds: Dict[str, float] = None

class QualityAnalyzer:
    """拡張された品質解析"""
    def __init__(self, ast_accessor: 'ASTAccessor', metric_definitions: List[QualityMetricDefinition]):
        self.ast_accessor = ast_accessor
        self.metric_definitions = {metric.name: metric for metric in metric_definitions}
        self.logger = logging.getLogger(__name__)
        self.results = defaultdict(dict)

    async def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """拡張された品質解析の実行"""
        try:
            # 基本メトリクスの収集
            complexity_metrics = self._analyze_complexity_metrics(ast)
            maintainability_metrics = self._analyze_maintainability_metrics(ast)
            readability_metrics = self._analyze_readability_metrics(ast)
            testability_metrics = self._analyze_testability_metrics(ast)
            modularity_metrics = self._analyze_modularity_metrics(ast)
            documentation_metrics = self._analyze_documentation_metrics(ast)

            # メトリクスの評価と正規化
            evaluated_metrics = self._evaluate_all_metrics({
                **complexity_metrics,
                **maintainability_metrics,
                **readability_metrics,
                **testability_metrics,
                **modularity_metrics,
                **documentation_metrics
            })

            # 品質スコアの計算
            quality_scores = self._calculate_quality_scores(evaluated_metrics)

            # 改善提案の生成
            recommendations = self._generate_recommendations(evaluated_metrics)

            return {
                "metrics": evaluated_metrics,
                "scores": quality_scores,
                "recommendations": recommendations,
                "summary": self._create_quality_summary(quality_scores)
            }

        except Exception as e:
            self.logger.error(f"Quality analysis failed: {str(e)}")
            raise

    def _analyze_complexity_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """複雑度メトリクスの分析"""
        metrics = {}
        
        # 循環的複雑度
        metrics["cyclomatic_complexity"] = self._calculate_cyclomatic_complexity(ast)
        
        # 認知的複雑度
        metrics["cognitive_complexity"] = self._calculate_cognitive_complexity(ast)
        
        # Halstead複雑度メトリクス
        halstead_metrics = self._calculate_halstead_metrics(ast)
        metrics.update(halstead_metrics)
        
        # 制御フロー複雑度
        metrics["control_flow_complexity"] = self._analyze_control_flow_complexity(ast)
        
        # データフロー複雑度
        metrics["data_flow_complexity"] = self._analyze_data_flow_complexity(ast)
        
        return metrics

    def _analyze_maintainability_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """保守性メトリクスの分析"""
        metrics = {}
        
        # 保守性指標
        metrics["maintainability_index"] = self._calculate_maintainability_index(ast)
        
        # コードの重複度
        metrics["code_duplication_ratio"] = self._analyze_code_duplication(ast)
        
        # モジュール結合度
        metrics["module_coupling"] = self._analyze_module_coupling(ast)
        
        # コードの凝集度
        metrics["code_cohesion"] = self._analyze_code_cohesion(ast)
        
        # 変更容易性
        metrics["change_flexibility"] = self._analyze_change_flexibility(ast)
        
        return metrics

    def _analyze_readability_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """可読性メトリクスの分析"""
        metrics = {}
        
        # 命名規則遵守率
        metrics["naming_convention_compliance"] = self._analyze_naming_conventions(ast)
        
        # コメント率
        metrics["comment_ratio"] = self._calculate_comment_ratio(ast)
        
        # インデント一貫性
        metrics["indentation_consistency"] = self._analyze_indentation(ast)
        
        # 文の複雑さ
        metrics["statement_complexity"] = self._analyze_statement_complexity(ast)
        
        # レイアウトの一貫性
        metrics["layout_consistency"] = self._analyze_layout_consistency(ast)
        
        return metrics

    def _analyze_testability_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """テスト容易性メトリクスの分析"""
        metrics = {}
        
        # 入力依存度
        metrics["input_dependency"] = self._analyze_input_dependencies(ast)
        
        # 出力予測可能性
        metrics["output_predictability"] = self._analyze_output_predictability(ast)
        
        # 副作用の程度
        metrics["side_effect_freedom"] = self._analyze_side_effects(ast)
        
        # データ分離度
        metrics["data_isolation"] = self._analyze_data_isolation(ast)
        
        # モック容易性
        metrics["mockability"] = self._analyze_mockability(ast)
        
        return metrics

    def _analyze_modularity_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """モジュール性メトリクスの分析"""
        metrics = {}
        
        # モジュールサイズ
        metrics["module_size"] = self._calculate_module_size(ast)
        
        # インターフェース複雑度
        metrics["interface_complexity"] = self._analyze_interface_complexity(ast)
        
        # 依存関係の深さ
        metrics["dependency_depth"] = self._analyze_dependency_depth(ast)
        
        # モジュール独立性
        metrics["module_independence"] = self._analyze_module_independence(ast)
        
        return metrics

    def _analyze_documentation_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """ドキュメント品質メトリクスの分析"""
        metrics = {}
        
        # ドキュメント網羅率
        metrics["documentation_coverage"] = self._calculate_documentation_coverage(ast)
        
        # API文書化率
        metrics["api_documentation_ratio"] = self._analyze_api_documentation(ast)
        
        # コメント品質
        metrics["comment_quality"] = self._analyze_comment_quality(ast)
        
        # 例外文書化率
        metrics["error_documentation_ratio"] = self._analyze_error_documentation(ast)
        
        return metrics

    def _evaluate_all_metrics(self, metrics: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
        """全メトリクスの評価"""
        evaluated = {}
        for metric_name, value in metrics.items():
            if metric_name in self.metric_definitions:
                definition = self.metric_definitions[metric_name]
                evaluated[metric_name] = self._evaluate_metric(value, definition)
        return evaluated

    def _evaluate_metric(self, value: float, definition: QualityMetricDefinition) -> Dict[str, Any]:
        """個別メトリクスの評価"""
        normalized_value = self._normalize_value(value, definition)
        score = self._calculate_metric_score(normalized_value, definition)
        evaluation = {
            "value": value,
            "normalized_value": normalized_value,
            "score": score,
            "status": self._determine_status(normalized_value, definition),
            "improvement_needed": score < 0.7
        }
        return evaluation

    def _calculate_quality_scores(self, evaluated_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """品質スコアの計算"""
        scores = defaultdict(list)
        
        for metric_name, evaluation in evaluated_metrics.items():
            if metric_name in self.metric_definitions:
                metric_type = self.metric_definitions[metric_name].metric_type
                scores[metric_type.value].append(evaluation["score"])

        return {
            metric_type: np.mean(type_scores) if type_scores else 0.0
            for metric_type, type_scores in scores.items()
        }

    def _generate_recommendations(self, evaluated_metrics: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """改善提案の生成"""
        recommendations = []
        
        for metric_name, evaluation in evaluated_metrics.items():
            if evaluation.get("improvement_needed", False):
                recommendations.append({
                    "metric": metric_name,
                    "current_value": evaluation["value"],
                    "target_value": self.metric_definitions[metric_name].target_value,
                    "priority": self._determine_priority(evaluation),
                    "suggestions": self._get_improvement_suggestions(metric_name, evaluation)
                })
                
        return sorted(recommendations, key=lambda x: x["priority"], reverse=True)

    def _create_quality_summary(self, quality_scores: Dict[str, float]) -> Dict[str, Any]:
        """品質サマリーの作成"""
        return {
            "overall_score": np.mean(list(quality_scores.values())),
            "quality_scores": quality_scores,
            "evaluation_date": datetime.utcnow().isoformat(),
            "critical_metrics": self._identify_critical_metrics(),
            "improvement_priorities": self._determine_improvement_priorities()
        }