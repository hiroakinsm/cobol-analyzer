# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/benchmark/components.py

from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

class BenchmarkType(Enum):
    INDUSTRY_STANDARD = "industry"
    ORGANIZATION_STANDARD = "organization"
    PROJECT_STANDARD = "project"
    CUSTOM = "custom"

class EvaluationLevel(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    ACCEPTABLE = "acceptable"
    GOOD = "good"
    EXCELLENT = "excellent"

@dataclass
class BenchmarkCriteria:
    metric_name: str
    benchmark_type: BenchmarkType
    min_value: Optional[float]
    max_value: Optional[float]
    target_value: Optional[float]
    weight: float = 1.0
    description: str = ""

@dataclass
class EvaluationResult:
    metric_name: str
    actual_value: float
    benchmark_value: float
    level: EvaluationLevel
    score: float
    details: Dict[str, Any]

class BenchmarkManager:
    """ベンチマーク基準の管理"""
    def __init__(self, db_connection):
        self.db = db_connection
        self.criteria_cache: Dict[str, BenchmarkCriteria] = {}

    def get_criteria(self, metric_name: str, benchmark_type: BenchmarkType) -> BenchmarkCriteria:
        """ベンチマーク基準の取得"""
        cache_key = f"{metric_name}_{benchmark_type.value}"
        if cache_key not in self.criteria_cache:
            criteria = self._load_criteria_from_db(metric_name, benchmark_type)
            self.criteria_cache[cache_key] = criteria
        return self.criteria_cache[cache_key]

    def _load_criteria_from_db(self, metric_name: str, benchmark_type: BenchmarkType) -> BenchmarkCriteria:
        """データベースからベンチマーク基準を読み込み"""
        query = """
            SELECT * FROM benchmark_master 
            WHERE metric_name = %s AND benchmark_type = %s
            AND is_active = true
        """
        result = self.db.execute(query, (metric_name, benchmark_type.value))
        if not result:
            raise ValueError(f"No benchmark criteria found for {metric_name}")
        return self._create_criteria_from_db_result(result)

class MetricsEvaluator:
    """メトリクス評価の実行"""
    def __init__(self, benchmark_manager: BenchmarkManager):
        self.benchmark_manager = benchmark_manager
        self.results: Dict[str, EvaluationResult] = {}

    def evaluate_metrics(self, metrics: Dict[str, Any], benchmark_type: BenchmarkType) -> Dict[str, EvaluationResult]:
        """メトリクスの評価を実行"""
        for metric_name, value in metrics.items():
            try:
                criteria = self.benchmark_manager.get_criteria(metric_name, benchmark_type)
                result = self._evaluate_single_metric(metric_name, value, criteria)
                self.results[metric_name] = result
            except ValueError as e:
                logging.warning(f"Skipping evaluation for {metric_name}: {str(e)}")
                continue
        return self.results

    def _evaluate_single_metric(self, metric_name: str, value: float, criteria: BenchmarkCriteria) -> EvaluationResult:
        """単一メトリクスの評価"""
        level = self._determine_level(value, criteria)
        score = self._calculate_score(value, criteria)
        return EvaluationResult(
            metric_name=metric_name,
            actual_value=value,
            benchmark_value=criteria.target_value or 0.0,
            level=level,
            score=score,
            details=self._create_evaluation_details(value, criteria)
        )

    def _determine_level(self, value: float, criteria: BenchmarkCriteria) -> EvaluationLevel:
        """評価レベルの判定"""
        if criteria.min_value is not None and value < criteria.min_value:
            return EvaluationLevel.CRITICAL
        if criteria.max_value is not None and value > criteria.max_value:
            return EvaluationLevel.WARNING
        # 他の条件による判定ロジック
        return EvaluationLevel.ACCEPTABLE

class QualityScoreCalculator:
    """品質スコアの計算"""
    def __init__(self, weights: Dict[str, float]):
        self.weights = weights
        self.score_cache: Dict[str, float] = {}

    def calculate_overall_score(self, evaluation_results: Dict[str, EvaluationResult]) -> float:
        """総合品質スコアの計算"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_name, result in evaluation_results.items():
            weight = self.weights.get(metric_name, 1.0)
            weighted_sum += result.score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def calculate_category_scores(self, evaluation_results: Dict[str, EvaluationResult]) -> Dict[str, float]:
        """カテゴリ別スコアの計算"""
        category_scores = defaultdict(lambda: {"sum": 0.0, "count": 0})
        
        for metric_name, result in evaluation_results.items():
            category = self._get_metric_category(metric_name)
            category_scores[category]["sum"] += result.score
            category_scores[category]["count"] += 1
        
        return {
            category: data["sum"] / data["count"]
            for category, data in category_scores.items()
        }

class TrendAnalyzer:
    """品質トレンドの分析"""
    def __init__(self, db_connection):
        self.db = db_connection
        self.history: Dict[str, List[Dict[str, Any]]] = {}

    def analyze_trends(self, metric_name: str, time_range: Optional[tuple] = None) -> Dict[str, Any]:
        """品質指標のトレンド分析"""
        history_data = self._load_metric_history(metric_name, time_range)
        return {
            "trend_line": self._calculate_trend_line(history_data),
            "significant_changes": self._detect_significant_changes(history_data),
            "seasonal_patterns": self._analyze_seasonal_patterns(history_data),
            "predictions": self._generate_predictions(history_data)
        }

    def _load_metric_history(self, metric_name: str, time_range: Optional[tuple]) -> List[Dict[str, Any]]:
        """メトリクス履歴データの読み込み"""
        query = """
            SELECT metric_value, evaluated_at 
            FROM metrics_history 
            WHERE metric_name = %s
        """
        params = [metric_name]
        if time_range:
            query += " AND evaluated_at BETWEEN %s AND %s"
            params.extend(time_range)
        
        return self.db.execute(query, params)

class ImprovementRecommender:
    """改善推奨事項の生成"""
    def __init__(self, evaluation_results: Dict[str, EvaluationResult]):
        self.evaluation_results = evaluation_results
        self.recommendations: List[Dict[str, Any]] = []

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """改善推奨事項の生成"""
        self._analyze_critical_issues()
        self._analyze_optimization_opportunities()
        self._prioritize_recommendations()
        return self.recommendations

    def _analyze_critical_issues(self) -> None:
        """重要な問題の分析"""
        for metric_name, result in self.evaluation_results.items():
            if result.level == EvaluationLevel.CRITICAL:
                self.recommendations.append({
                    "type": "critical",
                    "metric": metric_name,
                    "current_value": result.actual_value,
                    "target_value": result.benchmark_value,
                    "impact": "high",
                    "recommendation": self._generate_improvement_suggestion(metric_name, result)
                })

    def _generate_improvement_suggestion(self, metric_name: str, result: EvaluationResult) -> str:
        """改善提案の生成
        
        Args:
            metric_name: メトリクス名
            result: 評価結果
        
        Returns:
            str: 改善提案の文字列
        """
        suggestion_templates = {
            "cyclomatic_complexity": {
                "critical": "モジュールの複雑度が非常に高いです。以下の対策を検討してください：\n"
                           "- 大きな条件分岐をより小さな関数に分割\n"
                           "- 複雑なロジックの簡素化\n"
                           "- EVALUATE文の活用による条件分岐の整理",
                "warning": "複雑度がやや高めです。以下を検討してください：\n"
                          "- 条件分岐の簡素化\n"
                          "- ロジックのモジュール化",
                "acceptable": "複雑度は許容範囲内ですが、以下の改善を検討できます：\n"
                             "- コードの可読性向上\n"
                             "- コメントの追加"
            },
            "maintainability_index": {
                "critical": "保守性が著しく低いです。以下の対策が必要です：\n"
                           "- コードの再構造化\n"
                           "- 重複コードの排除\n"
                           "- ドキュメントの充実",
                "warning": "保守性の改善が推奨されます：\n"
                          "- モジュール性の向上\n"
                          "- 命名規則の見直し",
                "acceptable": "保守性は問題ありませんが、以下を検討できます：\n"
                          "- さらなるドキュメント化\n"
                         "- コードの整理"
            },
            "halstead_complexity": {
                "critical": "コードの複雑性が非常に高いです：\n"
                           "- オペレータとオペランドの数を削減\n"
                           "- ロジックの単純化\n"
                           "- 共通処理のサブルーチン化",
                "warning": "コードの複雑性を見直してください：\n"
                          "- 処理の分割\n"
                          "- リファクタリングの検討",
                "acceptable": "複雑性は許容範囲ですが、改善の余地があります：\n"
                             "- コードの整理\n"
                             "- 可読性の向上"
            },
            "data_complexity": {
                "critical": "データ構造が複雑すぎます：\n"
                           "- データ項目の整理\n"
                           "- REDEFINES句の見直し\n"
                           "- 階層構造の単純化",
                "warning": "データ構造の改善を検討：\n"
                          "- グループ項目の整理\n"
                          "- 未使用項目の削除",
                "acceptable": "データ構造は問題ありませんが、以下を検討：\n"
                             "- さらなる構造化\n"
                             "- ドキュメントの追加"
            }
        }

    # メトリクスのカテゴリと重要度に基づいて提案を選択
    if metric_name not in suggestion_templates:
        return f"{metric_name}に関する具体的な改善提案は利用できません。一般的なコーディング基準に従ってください。"

    if result.level == EvaluationLevel.CRITICAL:
        severity = "critical"
    elif result.level == EvaluationLevel.WARNING:
        severity = "warning"
    else:
        severity = "acceptable"

    suggestion = suggestion_templates[metric_name][severity]

    # メトリクス固有の追加情報
    if metric_name == "cyclomatic_complexity" and result.level in [EvaluationLevel.CRITICAL, EvaluationLevel.WARNING]:
        suggestion += f"\n現在の複雑度: {result.actual_value:.2f}\n"
        suggestion += f"目標値: {result.benchmark_value:.2f}\n"
        suggestion += "複雑度を下げるために、条件分岐の数を減らすことを検討してください。"

    elif metric_name == "maintainability_index":
        suggestion += f"\n現在の保守性指標: {result.actual_value:.2f}\n"
        suggestion += f"目標値: {result.benchmark_value:.2f}\n"
        if result.level == EvaluationLevel.CRITICAL:
            suggestion += "特に、コードの構造化とドキュメント化を優先的に実施してください。"

    elif metric_name == "halstead_complexity":
        suggestion += f"\n現在の複雑性: {result.actual_value:.2f}\n"
        suggestion += f"目標値: {result.benchmark_value:.2f}\n"
        if result.level in [EvaluationLevel.CRITICAL, EvaluationLevel.WARNING]:
            suggestion += "プログラムの分割とモジュール化を検討してください。"

    elif metric_name == "data_complexity":
        suggestion += f"\n現在のデータ複雑度: {result.actual_value:.2f}\n"
        suggestion += f"目標値: {result.benchmark_value:.2f}\n"
        if result.level == EvaluationLevel.CRITICAL:
            suggestion += "データ構造の簡素化と正規化を優先的に実施してください。"

    return suggestion
