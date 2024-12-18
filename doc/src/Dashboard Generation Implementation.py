from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import mermaid

class DashboardGenerator:
    """ダッシュボード生成処理"""

    def __init__(self, db_functions):
        self.db = db_functions
        self.logger = logging.getLogger(__name__)

    async def generate_single_source_dashboard(self, source_id: UUID) -> Dict[str, Any]:
        """単一ソース解析用ダッシュボードの生成"""
        try:
            # 解析結果の取得
            analysis_results = await self.db.get_analysis_results(source_id)
            if not analysis_results:
                raise ValueError(f"Analysis results not found for source {source_id}")

            # プログラム情報の取得
            program_info = await self.db.get_source_info(source_id)

            # ダッシュボードの構築
            dashboard = {
                "type": "single_source",
                "metadata": {
                    "program_name": program_info["name"],
                    "analysis_date": datetime.utcnow().isoformat(),
                    "source_id": str(source_id)
                },
                "sections": {
                    "overview": self._create_overview_section(analysis_results),
                    "structure": self._create_structure_section(analysis_results),
                    "quality": self._create_quality_section(analysis_results),
                    "security": self._create_security_section(analysis_results)
                }
            }

            return dashboard

        except Exception as e:
            self.logger.error(f"Dashboard generation failed: {str(e)}")
            raise

    async def generate_summary_dashboard(self, source_ids: List[UUID]) -> Dict[str, Any]:
        """サマリ解析用ダッシュボードの生成"""
        try:
            # サマリ解析結果の取得
            summary_results = await self.db.get_summary_results(source_ids)
            if not summary_results:
                raise ValueError("Summary results not found")

            # プログラム群の情報取得
            program_infos = await self.db.get_source_infos(source_ids)

            # ダッシュボードの構築
            dashboard = {
                "type": "summary",
                "metadata": {
                    "analysis_date": datetime.utcnow().isoformat(),
                    "program_count": len(source_ids),
                    "programs": [p["name"] for p in program_infos]
                },
                "sections": {
                    "overview": self._create_summary_overview_section(summary_results),
                    "trends": self._create_trends_section(summary_results),
                    "patterns": self._create_patterns_section(summary_results),
                    "issues": self._create_issues_section(summary_results)
                }
            }

            return dashboard

        except Exception as e:
            self.logger.error(f"Summary dashboard generation failed: {str(e)}")
            raise

    def _create_overview_section(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """概要セクションの生成"""
        metrics = analysis_results["analysis"]
        
        return {
            "type": "overview",
            "title": "プログラム概要",
            "components": [
                {
                    "type": "metrics_grid",
                    "title": "主要メトリクス",
                    "data": {
                        "総行数": metrics["structure"]["metrics"]["total_lines"],
                        "複雑度": metrics["complexity"]["metrics"]["total_complexity"],
                        "品質スコア": metrics["quality"]["metrics"]["overall_score"],
                        "セキュリティスコア": metrics["security"]["metrics"]["security_score"]
                    }
                },
                {
                    "type": "radar_chart",
                    "title": "品質指標",
                    "data": {
                        "labels": ["複雑度", "保守性", "信頼性", "セキュリティ"],
                        "values": [
                            metrics["complexity"]["metrics"]["normalized_score"],
                            metrics["quality"]["metrics"]["maintainability_score"],
                            metrics["quality"]["metrics"]["reliability_score"],
                            metrics["security"]["metrics"]["security_score"]
                        ]
                    }
                }
            ]
        }

    def _create_structure_section(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """構造セクションの生成"""
        structure = analysis_results["analysis"]["structure"]
        
        return {
            "type": "structure",
            "title": "プログラム構造",
            "components": [
                {
                    "type": "mermaid_diagram",
                    "title": "プログラム構造図",
                    "data": self._generate_structure_diagram(structure)
                },
                {
                    "type": "tree_view",
                    "title": "コンポーネント階層",
                    "data": self._generate_component_tree(structure)
                },
                {
                    "type": "metrics_table",
                    "title": "構造メトリクス",
                    "data": {
                        "headers": ["メトリクス", "値", "評価"],
                        "rows": [
                            ["セクション数", structure["metrics"]["total_sections"], self._evaluate_metric(structure["metrics"]["total_sections"], "sections")],
                            ["平均セクションサイズ", structure["metrics"]["average_section_size"], self._evaluate_metric(structure["metrics"]["average_section_size"], "section_size")],
                            ["最大ネスト深度", structure["metrics"]["max_nesting_depth"], self._evaluate_metric(structure["metrics"]["max_nesting_depth"], "nesting")]
                        ]
                    }
                }
            ]
        }

    def _create_quality_section(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """品質セクションの生成"""
        quality = analysis_results["analysis"]["quality"]
        
        return {
            "type": "quality",
            "title": "品質分析",
            "components": [
                {
                    "type": "bar_chart",
                    "title": "品質スコア内訳",
                    "data": {
                        "labels": ["コーディング規約", "命名規則", "ドキュメント", "モジュール性"],
                        "values": [
                            quality["metrics"]["coding_standards_score"],
                            quality["metrics"]["naming_conventions_score"],
                            quality["metrics"]["documentation_score"],
                            quality["metrics"]["modularity_score"]
                        ]
                    }
                },
                {
                    "type": "issues_list",
                    "title": "品質課題",
                    "data": self._format_quality_issues(quality["details"]["issues"])
                },
                {
                    "type": "metrics_table",
                    "title": "品質メトリクス詳細",
                    "data": {
                        "headers": ["指標", "値", "ベンチマーク", "評価"],
                        "rows": self._generate_quality_metrics_rows(quality["metrics"])
                    }
                }
            ]
        }

    def _create_security_section(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティセクションの生成"""
        security = analysis_results["analysis"]["security"]
        
        return {
            "type": "security",
            "title": "セキュリティ分析",
            "components": [
                {
                    "type": "donut_chart",
                    "title": "脆弱性リスクレベル分布",
                    "data": {
                        "labels": ["Critical", "High", "Medium", "Low"],
                        "values": [
                            security["metrics"]["critical_vulnerabilities"],
                            security["metrics"]["high_vulnerabilities"],
                            security["metrics"]["medium_vulnerabilities"],
                            security["metrics"]["low_vulnerabilities"]
                        ]
                    }
                },
                {
                    "type": "security_table",
                    "title": "セキュリティ課題一覧",
                    "data": {
                        "headers": ["重要度", "種別", "説明", "対策"],
                        "rows": self._format_security_issues(security["details"]["vulnerabilities"])
                    }
                }
            ]
        }

    def _create_summary_overview_section(self, summary_results: Dict[str, Any]) -> Dict[str, Any]:
        """サマリ概要セクションの生成"""
        return {
            "type": "summary_overview",
            "title": "サマリ概要",
            "components": [
                {
                    "type": "metrics_summary",
                    "title": "全体メトリクス",
                    "data": self._format_summary_metrics(summary_results["summary"]["overall"])
                },
                {
                    "type": "distribution_chart",
                    "title": "品質分布",
                    "data": self._generate_quality_distribution(summary_results)
                }
            ]
        }

    def _generate_structure_diagram(self, structure: Dict[str, Any]) -> str:
        """構造図の生成（Mermaid形式）"""
        nodes = []
        edges = []
        
        # DIVISIONノードの生成
        for division in structure["details"]["divisions"]:
            nodes.append(f"{division['name']}[{division['name']}]")
            
            # SECTIONとの接続
            for section in division.get("sections", []):
                section_id = f"{section['name'].replace(' ', '_')}"
                nodes.append(f"{section_id}[{section['name']}]")
                edges.append(f"{division['name']} --> {section_id}")
        
        # Mermaidダイアグラムの生成
        return f"""graph TD
    {chr(10).join(nodes)}
    {chr(10).join(edges)}
        """

    def _format_quality_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """品質課題のフォーマット"""
        return [
            {
                "severity": issue["severity"],
                "category": issue["category"],
                "description": issue["description"],
                "recommendation": issue["recommendation"]
            }
            for issue in issues
        ]

    def _evaluate_metric(self, value: float, metric_type: str) -> str:
        """メトリクスの評価"""
        thresholds = {
            "sections": {"low": 5, "high": 20},
            "section_size": {"low": 30, "high": 100},
            "nesting": {"low": 3, "high": 6}
        }
        
        threshold = thresholds.get(metric_type, {"low": 0, "high": 0})
        if value <= threshold["low"]:
            return "良好"
        elif value >= threshold["high"]:
            return "要改善"
        else:
            return "普通"