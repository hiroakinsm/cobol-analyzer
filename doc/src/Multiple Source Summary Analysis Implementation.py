# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/summary/implementation.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import statistics
from collections import defaultdict

class SummaryAnalyzer:
    """複数ソースサマリ解析の実装"""

    def __init__(self, db_functions, metrics_analyzer):
        self.db = db_functions
        self.metrics = metrics_analyzer
        self.logger = logging.getLogger(__name__)

    async def analyze_sources(self, source_ids: List[UUID]) -> Dict[str, Any]:
        """選択されたソース群のサマリ解析を実行"""
        try:
            # 各ソースの解析結果を取得
            individual_results = {}
            for source_id in source_ids:
                result = await self.db.get_analysis_results(source_id)
                if result:
                    individual_results[source_id] = result

            if not individual_results:
                raise ValueError("No analysis results found for selected sources")

            # サマリ解析の実行
            summary = {
                "timestamp": datetime.utcnow(),
                "source_count": len(individual_results),
                "summary": {
                    "overall": await self._analyze_overall_metrics(individual_results),
                    "structural": await self._analyze_structural_patterns(individual_results),
                    "quality": await self._analyze_quality_trends(individual_results),
                    "complexity": await self._analyze_complexity_distribution(individual_results),
                    "security": await self._analyze_security_summary(individual_results)
                }
            }

            # サマリ結果の保存
            await self.db.store_summary_results(source_ids, summary)
            return summary

        except Exception as e:
            self.logger.error(f"Summary analysis failed: {str(e)}")
            raise

    async def _analyze_overall_metrics(self, results: Dict[UUID, Dict[str, Any]]) -> Dict[str, Any]:
        """全体的なメトリクスの分析"""
        metrics = {
            "total_lines": [],
            "complexity_scores": [],
            "quality_scores": [],
            "security_scores": []
        }

        # メトリクスの収集
        for result in results.values():
            analysis = result.get("analysis", {})
            metrics["total_lines"].append(analysis.get("structure", {}).get("metrics", {}).get("total_lines", 0))
            metrics["complexity_scores"].append(analysis.get("complexity", {}).get("metrics", {}).get("total_complexity", 0))
            metrics["quality_scores"].append(analysis.get("quality", {}).get("metrics", {}).get("overall_score", 0))
            metrics["security_scores"].append(analysis.get("security", {}).get("metrics", {}).get("security_score", 0))

        # 統計値の計算
        return {
            "size_metrics": {
                "total_sources": len(results),
                "total_lines": sum(metrics["total_lines"]),
                "average_lines": statistics.mean(metrics["total_lines"]),
                "std_dev_lines": statistics.stdev(metrics["total_lines"]) if len(metrics["total_lines"]) > 1 else 0
            },
            "quality_metrics": {
                "average_complexity": statistics.mean(metrics["complexity_scores"]),
                "average_quality": statistics.mean(metrics["quality_scores"]),
                "average_security": statistics.mean(metrics["security_scores"]),
                "quality_distribution": self._calculate_distribution(metrics["quality_scores"])
            }
        }

    async def _analyze_structural_patterns(self, results: Dict[UUID, Dict[str, Any]]) -> Dict[str, Any]:
        """構造パターンの分析"""
        patterns = defaultdict(int)
        section_sizes = []
        data_patterns = defaultdict(int)

        for result in results.values():
            structure = result.get("analysis", {}).get("structure", {})
            
            # セクション構造のパターン分析
            sections = structure.get("details", {}).get("sections", [])
            for section in sections:
                patterns[section.get("type", "unknown")] += 1
                section_sizes.append(section.get("statement_count", 0))

            # データ構造のパターン分析
            data_items = result.get("analysis", {}).get("data_items", {}).get("details", {})
            for section, items in data_items.items():
                for item in items:
                    pattern_type = self._classify_data_pattern(item)
                    data_patterns[pattern_type] += 1

        return {
            "section_patterns": {
                "types": dict(patterns),
                "average_size": statistics.mean(section_sizes) if section_sizes else 0,
                "size_distribution": self._calculate_distribution(section_sizes)
            },
            "data_patterns": {
                "types": dict(data_patterns),
                "common_patterns": self._identify_common_patterns(data_patterns)
            },
            "structure_metrics": {
                "pattern_consistency": self._calculate_pattern_consistency(patterns),
                "data_complexity": self._calculate_data_complexity(data_patterns)
            }
        }

    async def _analyze_quality_trends(self, results: Dict[UUID, Dict[str, Any]]) -> Dict[str, Any]:
        """品質傾向の分析"""
        quality_metrics = defaultdict(list)
        issues = defaultdict(int)
        best_practices = defaultdict(int)

        for result in results.values():
            quality = result.get("analysis", {}).get("quality", {})
            metrics = quality.get("metrics", {})
            
            # 品質メトリクスの収集
            for metric_name, value in metrics.items():
                quality_metrics[metric_name].append(value)

            # 品質問題の集計
            for issue in quality.get("details", {}).get("issues", []):
                issues[issue["type"]] += 1

            # ベストプラクティスの集計
            for practice in quality.get("details", {}).get("best_practices", []):
                best_practices[practice] += 1

        return {
            "metrics_trends": {
                name: {
                    "average": statistics.mean(values),
                    "trend": self._calculate_trend(values),
                    "distribution": self._calculate_distribution(values)
                }
                for name, values in quality_metrics.items()
            },
            "common_issues": {
                issue: count
                for issue, count in sorted(
                    issues.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            },
            "best_practices_adoption": {
                practice: count / len(results)
                for practice, count in best_practices.items()
            }
        }

    async def _analyze_complexity_distribution(self, results: Dict[UUID, Dict[str, Any]]) -> Dict[str, Any]:
        """複雑度分布の分析"""
        complexity_metrics = defaultdict(list)
        hotspots = []

        for source_id, result in results.items():
            complexity = result.get("analysis", {}).get("complexity", {})
            metrics = complexity.get("metrics", {})
            
            # 複雑度メトリクスの収集
            for metric_name, value in metrics.items():
                complexity_metrics[metric_name].append(value)

            # 複雑度の高いホットスポットの特定
            if metrics.get("total_complexity", 0) > 30:
                hotspots.append({
                    "source_id": source_id,
                    "complexity": metrics["total_complexity"],
                    "factors": complexity.get("details", {}).get("complexity_factors", [])
                })

        return {
            "distribution": {
                metric: self._calculate_detailed_distribution(values)
                for metric, values in complexity_metrics.items()
            },
            "hotspots": sorted(
                hotspots,
                key=lambda x: x["complexity"],
                reverse=True
            ),
            "complexity_profiles": self._generate_complexity_profiles(complexity_metrics)
        }

    async def _analyze_security_summary(self, results: Dict[UUID, Dict[str, Any]]) -> Dict[str, Any]:
        """セキュリティサマリの分析"""
        vulnerability_types = defaultdict(int)
        risk_levels = defaultdict(int)
        security_patterns = defaultdict(int)

        for result in results.values():
            security = result.get("analysis", {}).get("security", {})
            
            # 脆弱性タイプの集計
            for vuln in security.get("details", {}).get("vulnerabilities", []):
                vulnerability_types[vuln["type"]] += 1
                risk_levels[vuln["risk_level"]] += 1

            # セキュリティパターンの分析
            for pattern in security.get("details", {}).get("security_patterns", []):
                security_patterns[pattern["type"]] += 1

        return {
            "risk_summary": {
                "risk_levels": dict(risk_levels),
                "total_vulnerabilities": sum(vulnerability_types.values()),
                "risk_score": self._calculate_risk_score(risk_levels)
            },
            "vulnerability_analysis": {
                "types": dict(vulnerability_types),
                "common_patterns": dict(security_patterns),
                "trend_analysis": self._analyze_vulnerability_trends(results)
            },
            "security_metrics": {
                "security_coverage": self._calculate_security_coverage(results),
                "mitigation_effectiveness": self._calculate_mitigation_effectiveness(results)
            }
        }

    def _calculate_distribution(self, values: List[float]) -> Dict[str, float]:
        """分布の計算"""
        if not values:
            return {}
        return {
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0
        }

    def _calculate_detailed_distribution(self, values: List[float]) -> Dict[str, Any]:
        """詳細な分布の計算"""
        basic_dist = self._calculate_distribution(values)
        
        # パーセンタイルの計算
        sorted_values = sorted(values)
        length = len(sorted_values)
        
        return {
            **basic_dist,
            "percentiles": {
                "25th": sorted_values[int(length * 0.25)],
                "50th": sorted_values[int(length * 0.50)],
                "75th": sorted_values[int(length * 0.75)],
                "90th": sorted_values[int(length * 0.90)]
            },
            "distribution_curve": self._generate_distribution_curve(values)
        }

    def _classify_data_pattern(self, item: Dict[str, Any]) -> str:
        """データパターンの分類"""
        if item.get("redefines"):
            return "redefines"
        elif item.get("occurs"):
            return "table"
        elif item.get("usage") == "index":
            return "index"
        elif item.get("level", 88) == 88:
            return "condition"
        else:
            return "simple"

    def _calculate_pattern_consistency(self, patterns: Dict[str, int]) -> float:
        """パターンの一貫性スコアを計算"""
        total = sum(patterns.values())
        if total == 0:
            return 0
        # パターンの偏りをスコア化
        pattern_ratios = [count / total for count in patterns.values()]
        return 1 - statistics.pstdev(pattern_ratios)

    def _calculate_trend(self, values: List[float]) -> str:
        """トレンドの計算"""
        if len(values) < 2:
            return "insufficient_data"
        # 移動平均の計算
        moving_avg = [
            statistics.mean(values[max(0, i-2):i+1])
            for i in range(len(values))
        ]
        if moving_avg[-1] > moving_avg[0]:
            return "improving"
        elif moving_avg[-1] < moving_avg[0]:
            return "degrading"
        else:
            return "stable"