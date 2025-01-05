# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/single/implementation.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID

class SingleSourceAnalyzer:
    """単一ソース解析の実装"""

    def __init__(self, db_functions, metrics_analyzer):
        self.db = db_functions
        self.metrics = metrics_analyzer
        self.logger = logging.getLogger(__name__)

    async def analyze_source(self, source_id: UUID) -> Dict[str, Any]:
        """単一ソースの解析を実行"""
        try:
            # ASTデータの取得
            ast_data = await self.db.get_ast_data(source_id)
            if not ast_data:
                raise ValueError(f"AST data not found for source {source_id}")

            # 各カテゴリの解析実行
            results = {
                "source_id": source_id,
                "timestamp": datetime.utcnow(),
                "analysis": {
                    "structure": await self._analyze_structure(ast_data),
                    "data_items": await self._analyze_data_items(ast_data),
                    "procedures": await self._analyze_procedures(ast_data),
                    "quality": await self._analyze_quality(ast_data),
                    "complexity": await self._analyze_complexity(ast_data),
                    "security": await self._analyze_security(ast_data)
                }
            }

            # 結果の保存
            await self.db.store_analysis_results(source_id, results)
            return results

        except Exception as e:
            self.logger.error(f"Single source analysis failed: {str(e)}")
            raise

    async def _analyze_structure(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """プログラム構造の解析"""
        structure = {
            "divisions": self._analyze_divisions(ast_data),
            "sections": self._analyze_sections(ast_data),
            "paragraphs": self._analyze_paragraphs(ast_data),
            "statements": self._analyze_statements(ast_data)
        }

        # メトリクスの計算
        metrics = {
            "total_divisions": len(structure["divisions"]),
            "total_sections": len(structure["sections"]),
            "total_paragraphs": len(structure["paragraphs"]),
            "total_statements": len(structure["statements"]),
            "average_section_size": sum(s["statement_count"] for s in structure["sections"]) / len(structure["sections"]) if structure["sections"] else 0,
            "max_nesting_depth": max(s["nesting_level"] for s in structure["statements"]) if structure["statements"] else 0
        }

        return {
            "details": structure,
            "metrics": metrics,
            "evaluation": self._evaluate_structure(metrics)
        }

    async def _analyze_data_items(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """データ項目の解析"""
        working_storage = self._analyze_working_storage(ast_data)
        linkage = self._analyze_linkage_section(ast_data)
        file_section = self._analyze_file_section(ast_data)

        metrics = {
            "total_items": len(working_storage) + len(linkage) + len(file_section),
            "working_storage_items": len(working_storage),
            "linkage_items": len(linkage),
            "file_section_items": len(file_section),
            "complex_items": len([i for i in working_storage if i.get("redefines") or i.get("occurs")]),
            "group_items": len([i for i in working_storage if i["level"] < 49])
        }

        return {
            "details": {
                "working_storage": working_storage,
                "linkage": linkage,
                "file_section": file_section
            },
            "metrics": metrics,
            "evaluation": self._evaluate_data_items(metrics)
        }

    async def _analyze_procedures(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """手続き部の解析"""
        procedure_division = ast_data.get("procedure_division", {})
        
        # セクションとパラグラフの解析
        sections = procedure_division.get("sections", [])
        section_analysis = [self._analyze_section(s) for s in sections]
        
        # 制御フローの解析
        control_flow = self._analyze_control_flow(procedure_division)
        
        # データアクセスの解析
        data_access = self._analyze_data_access(procedure_division)

        metrics = {
            "total_sections": len(sections),
            "total_paragraphs": sum(len(s.get("paragraphs", [])) for s in sections),
            "control_flow_complexity": control_flow["complexity"],
            "data_access_patterns": len(data_access["patterns"])
        }

        return {
            "details": {
                "sections": section_analysis,
                "control_flow": control_flow,
                "data_access": data_access
            },
            "metrics": metrics,
            "evaluation": self._evaluate_procedures(metrics)
        }

    async def _analyze_quality(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """品質の解析"""
        # コーディング規約の遵守度
        coding_standards = self._analyze_coding_standards(ast_data)
        
        # 命名規則の遵守度
        naming_conventions = self._analyze_naming_conventions(ast_data)
        
        # コメントの充実度
        documentation = self._analyze_documentation(ast_data)
        
        # モジュール性
        modularity = self._analyze_modularity(ast_data)

        metrics = {
            "coding_standards_score": coding_standards["score"],
            "naming_conventions_score": naming_conventions["score"],
            "documentation_score": documentation["score"],
            "modularity_score": modularity["score"]
        }

        return {
            "details": {
                "coding_standards": coding_standards,
                "naming_conventions": naming_conventions,
                "documentation": documentation,
                "modularity": modularity
            },
            "metrics": metrics,
            "evaluation": self._evaluate_quality(metrics)
        }

    def _evaluate_structure(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """構造の評価"""
        score = 100
        issues = []

        # 各メトリクスのしきい値チェック
        if metrics["total_sections"] > 20:
            score -= 10
            issues.append("過剰なセクション数")
        if metrics["average_section_size"] > 50:
            score -= 15
            issues.append("セクションサイズが大きい")
        if metrics["max_nesting_depth"] > 5:
            score -= 20
            issues.append("ネストが深すぎる")

        return {
            "score": score,
            "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "issues": issues
        }

    def _evaluate_data_items(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """データ項目の評価"""
        score = 100
        issues = []

        if metrics["complex_items"] > metrics["total_items"] * 0.3:
            score -= 20
            issues.append("複雑なデータ項目が多い")
        if metrics["working_storage_items"] > 100:
            score -= 15
            issues.append("作業領域のデータ項目が多い")

        return {
            "score": score,
            "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "issues": issues
        }

    def _evaluate_procedures(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """手続きの評価"""
        score = 100
        issues = []

        if metrics["control_flow_complexity"] > 30:
            score -= 25
            issues.append("制御フローが複雑")
        if metrics["total_paragraphs"] > 50:
            score -= 15
            issues.append("パラグラフ数が多い")

        return {
            "score": score,
            "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "issues": issues
        }

    def _evaluate_quality(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """品質の評価"""
        score = (metrics["coding_standards_score"] * 0.3 +
                metrics["naming_conventions_score"] * 0.2 +
                metrics["documentation_score"] * 0.2 +
                metrics["modularity_score"] * 0.3)

        issues = []
        if metrics["coding_standards_score"] < 70:
            issues.append("コーディング規約の遵守が不十分")
        if metrics["documentation_score"] < 60:
            issues.append("ドキュメント不足")

        return {
            "score": score,
            "level": "high" if score >= 80 else "medium" if score >= 60 else "low",
            "issues": issues
        }