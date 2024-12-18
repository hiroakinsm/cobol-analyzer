from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import ast
import statistics

class MetricType(Enum):
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    RELIABILITY = "reliability"

@dataclass
class MetricResult:
    value: float
    benchmark: float
    threshold: float
    evaluation: str
    details: Dict[str, Any]

class DetailedAnalyzer:
    """詳細な解析処理の実装"""
    
    def analyze_metrics(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス解析の実装"""
        return {
            "complexity": self._analyze_complexity(ast_data),
            "maintainability": self._analyze_maintainability(ast_data),
            "reliability": self._analyze_reliability(ast_data),
            "volume": self._analyze_volume(ast_data)
        }

    def _analyze_complexity(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度の解析
        - 循環的複雑度
        - 制御フロー複雑度
        - 認知的複雑度
        - データフロー複雑度
        """
        statements = ast_data.get("statements", [])
        conditionals = [s for s in statements if s["type"] in ["IF", "EVALUATE", "PERFORM"]]
        
        cyclomatic = len(conditionals) + 1
        
        # 制御フロー複雑度の計算
        control_flow = self._calculate_control_flow_complexity(statements)
        
        # 認知的複雑度の計算
        cognitive = self._calculate_cognitive_complexity(statements)
        
        # データフロー複雑度の計算
        data_flow = self._calculate_data_flow_complexity(ast_data.get("data_items", []))

        return {
            "cyclomatic": {
                "value": cyclomatic,
                "threshold": 10,
                "evaluation": "high" if cyclomatic > 10 else "medium" if cyclomatic > 5 else "low"
            },
            "control_flow": control_flow,
            "cognitive": cognitive,
            "data_flow": data_flow,
            "total_complexity": (cyclomatic * 0.3 + 
                               control_flow["value"] * 0.3 + 
                               cognitive["value"] * 0.2 + 
                               data_flow["value"] * 0.2)
        }

    def _calculate_control_flow_complexity(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """制御フロー複雑度の計算
        - ネストの深さ
        - 分岐の数
        - ループの数と構造
        """
        max_nesting = 0
        current_nesting = 0
        branch_count = 0
        loop_count = 0

        for stmt in statements:
            if stmt["type"] in ["IF", "EVALUATE"]:
                branch_count += 1
                current_nesting += 1
                max_nesting = max(max_nesting, current_nesting)
            elif stmt["type"] == "END-IF":
                current_nesting -= 1
            elif stmt["type"] == "PERFORM":
                if "TIMES" in stmt.get("modifiers", []) or "UNTIL" in stmt.get("modifiers", []):
                    loop_count += 1

        complexity_value = (max_nesting * 2 + branch_count + loop_count * 1.5)

        return {
            "value": complexity_value,
            "threshold": 15,
            "details": {
                "max_nesting": max_nesting,
                "branch_count": branch_count,
                "loop_count": loop_count
            },
            "evaluation": "high" if complexity_value > 15 else "medium" if complexity_value > 10 else "low"
        }

    def _calculate_cognitive_complexity(self, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """認知的複雑度の計算
        - ロジックの複雑さ
        - 条件の複雑さ
        - 制御構造の複雑さ
        """
        base_score = 0
        nesting_multiplier = 1

        for stmt in statements:
            if stmt["type"] in ["IF", "EVALUATE"]:
                base_score += 1 * nesting_multiplier
                nesting_multiplier += 1
            elif stmt["type"] == "END-IF":
                nesting_multiplier = max(1, nesting_multiplier - 1)
            elif stmt["type"] == "PERFORM":
                base_score += 1
                if "UNTIL" in stmt.get("modifiers", []):
                    base_score += 1 * nesting_multiplier

        return {
            "value": base_score,
            "threshold": 20,
            "evaluation": "high" if base_score > 20 else "medium" if base_score > 10 else "low"
        }

    def _calculate_data_flow_complexity(self, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データフロー複雑度の計算
        - データ項目の数と構造
        - データ依存関係の複雑さ
        - データ変換の複雑さ
        """
        # データ項目の数と階層の分析
        item_count = len(data_items)
        max_level = max((item.get("level", 1) for item in data_items), default=1)
        
        # REDEFINES項目の分析
        redefines_count = len([item for item in data_items if "redefines" in item])
        
        # 複合項目の分析
        group_items = [item for item in data_items if item.get("type") == "group"]
        group_complexity = sum(len(item.get("children", [])) for item in group_items)

        complexity_value = (item_count * 0.1 + 
                          max_level * 0.3 + 
                          redefines_count * 0.5 + 
                          group_complexity * 0.2)

        return {
            "value": complexity_value,
            "threshold": 25,
            "details": {
                "item_count": item_count,
                "max_level": max_level,
                "redefines_count": redefines_count,
                "group_complexity": group_complexity
            },
            "evaluation": "high" if complexity_value > 25 else "medium" if complexity_value > 15 else "low"
        }

    def _analyze_maintainability(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """保守性の解析"""
        # コードの構造的品質
        structure_quality = self._analyze_structure_quality(ast_data)
        
        # 命名規則の遵守度
        naming_quality = self._analyze_naming_quality(ast_data)
        
        # コメントの充実度
        documentation_quality = self._analyze_documentation_quality(ast_data)
        
        # モジュール性
        modularity = self._analyze_modularity(ast_data)

        maintainability_index = (structure_quality["value"] * 0.3 +
                               naming_quality["value"] * 0.2 +
                               documentation_quality["value"] * 0.2 +
                               modularity["value"] * 0.3)

        return {
            "maintainability_index": maintainability_index,
            "structure_quality": structure_quality,
            "naming_quality": naming_quality,
            "documentation_quality": documentation_quality,
            "modularity": modularity,
            "evaluation": "high" if maintainability_index > 80 else "medium" if maintainability_index > 60 else "low"
        }

    def _analyze_reliability(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """信頼性の解析"""
        # エラー処理の完全性
        error_handling = self._analyze_error_handling(ast_data)
        
        # 入力検証の充実度
        input_validation = self._analyze_input_validation(ast_data)
        
        # 例外処理の適切性
        exception_handling = self._analyze_exception_handling(ast_data)
        
        # データ整合性チェック
        data_integrity = self._analyze_data_integrity(ast_data)

        reliability_score = (error_handling["value"] * 0.3 +
                           input_validation["value"] * 0.3 +
                           exception_handling["value"] * 0.2 +
                           data_integrity["value"] * 0.2)

        return {
            "reliability_score": reliability_score,
            "error_handling": error_handling,
            "input_validation": input_validation,
            "exception_handling": exception_handling,
            "data_integrity": data_integrity,
            "evaluation": "high" if reliability_score > 80 else "medium" if reliability_score > 60 else "low"
        }

    def _analyze_volume(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """コード量の解析"""
        statements = ast_data.get("statements", [])
        data_items = ast_data.get("data_items", [])

        # 行数の計算
        total_lines = ast_data.get("total_lines", 0)
        code_lines = len(statements)
        comment_lines = ast_data.get("comment_lines", 0)
        
        # データ定義量の計算
        data_volume = len(data_items)
        working_storage_volume = len([item for item in data_items 
                                    if item.get("section") == "WORKING-STORAGE"])

        return {
            "total_lines": total_lines,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "comment_ratio": (comment_lines / total_lines) if total_lines > 0 else 0,
            "data_volume": {
                "total": data_volume,
                "working_storage": working_storage_volume
            },
            "evaluation": "high" if total_lines > 1000 else "medium" if total_lines > 500 else "low"
        }

    # 詳細な分析ヘルパーメソッド
    def _analyze_structure_quality(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """構造的品質の分析"""
        divisions = ast_data.get("divisions", [])
        sections = ast_data.get("sections", [])
        
        # 構造の整理度を評価
        structure_score = 100
        
        # DIVISIONの順序チェック
        expected_divisions = ["IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE"]
        actual_divisions = [d.get("name") for d in divisions]
        if actual_divisions != expected_divisions:
            structure_score -= 20

        # SECTIONの構造チェック
        for section in sections:
            if not section.get("name"):
                structure_score -= 5
            if len(section.get("paragraphs", [])) > 20:
                structure_score -= 10

        return {
            "value": structure_score,
            "details": {
                "division_order": actual_divisions,
                "section_count": len(sections)
            }
        }

    def _analyze_naming_quality(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """命名規則の分析"""
        data_items = ast_data.get("data_items", [])
        paragraphs = ast_data.get("paragraphs", [])
        
        naming_score = 100
        naming_issues = []

        # データ項目の命名チェック
        for item in data_items:
            name = item.get("name", "")
            if len(name) < 3:
                naming_score -= 2
                naming_issues.append(f"Short name: {name}")
            if not name.isalnum():
                naming_score -= 2
                naming_issues.append(f"Invalid characters in name: {name}")

        # パラグラフの命名チェック
        for para in paragraphs:
            name = para.get("name", "")
            if len(name) < 4:
                naming_score -= 2
                naming_issues.append(f"Short paragraph name: {name}")

        return {
            "value": max(0, naming_score),
            "issues": naming_issues
        }

    def _analyze_documentation_quality(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメント品質の分析"""
        total_lines = ast_data.get("total_lines", 0)
        comment_lines = ast_data.get("comment_lines", 0)
        comments = ast_data.get("comments", [])
        
        doc_score = 100

        # コメント行率のチェック
        comment_ratio = (comment_lines / total_lines) if total_lines > 0 else 0
        if comment_ratio < 0.1:
            doc_score -= 30
        elif comment_ratio < 0.2:
            doc_score -= 15

        # コメントの質チェック
        meaningful_comments = [c for c in comments if len(c) > 10]
        if len(meaningful_comments) < len(comments) * 0.5:
            doc_score -= 20

        return {
            "value": max(0, doc_score),
            "details": {
                "comment_ratio": comment_ratio,
                "meaningful_comments": len(meaningful_comments)
            }
        }

    def _analyze_modularity(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """モジュール性の分析"""
        sections = ast_data.get("sections", [])
        paragraphs = ast_data.get("paragraphs", [])
        
        modularity_score = 100
        issues = []

        # セクションサイズのチェック
        for section in sections:
            if len(section.get("paragraphs", [])) > 15:
                modularity_score -= 10
                issues.append(f"Large section: {section.get('name')}")

        # パラグラフの独立性チェック
        for para in paragraphs:
            if len(para.get("statements", [])) > 50:
                modularity_score -= 5
                issues.append(f"Large paragraph: {para.get('name')}")

        return {
            "value": max(0, modularity_score),
            "issues": issues,
            "details": {
                "section_count": len(sections),
                "average_section_size": statistics.mean([len(s.get("paragraphs", [])) for s in sections]) if sections else 0,
                "average_paragraph_size": statistics.mean([len(p.get("statements", [])) for p in paragraphs]) if paragraphs else 0
            },
            "evaluation": "high" if modularity_score > 80 else "medium" if modularity_score > 60 else "low"
        }

    def _analyze_error_handling(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """エラー処理の分析"""
        statements = ast_data.get("statements", [])
        error_sections = []
        error_handling_score = 100

        # ファイル操作のエラー処理チェック
        file_ops = [s for s in statements if s["type"] in ["OPEN", "CLOSE", "READ", "WRITE"]]
        file_status_checks = [s for s in statements if "FILE STATUS" in str(s.get("conditions", ""))]
        
        if file_ops and len(file_status_checks) < len(file_ops):
            error_handling_score -= 20
            error_sections.append("file_operations")

        # 呼び出しのエラー処理チェック
        calls = [s for s in statements if s["type"] == "CALL"]
        call_status_checks = [s for s in statements if "RETURN-CODE" in str(s.get("conditions", ""))]
        
        if calls and len(call_status_checks) < len(calls):
            error_handling_score -= 15
            error_sections.append("call_operations")

        return {
            "value": max(0, error_handling_score),
            "missing_handlers": error_sections,
            "details": {
                "file_operations": len(file_ops),
                "file_status_checks": len(file_status_checks),
                "call_operations": len(calls),
                "call_status_checks": len(call_status_checks)
            },
            "evaluation": "high" if error_handling_score > 80 else "medium" if error_handling_score > 60 else "low"
        }

    def _analyze_input_validation(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """入力検証の分析"""
        statements = ast_data.get("statements", [])
        data_items = ast_data.get("data_items", [])
        validation_score = 100
        validation_issues = []

        # 入力項目の検証
        input_items = [d for d in data_items if d.get("usage") == "input"]
        for item in input_items:
            validation_found = False
            item_name = item.get("name", "")
            
            # 項目の値チェック処理を探索
            for stmt in statements:
                if item_name in str(stmt.get("conditions", "")):
                    validation_found = True
                    break
            
            if not validation_found:
                validation_score -= 10
                validation_issues.append(f"No validation for: {item_name}")

        return {
            "value": max(0, validation_score),
            "issues": validation_issues,
            "details": {
                "input_items": len(input_items),
                "validated_items": len(input_items) - len(validation_issues)
            },
            "evaluation": "high" if validation_score > 80 else "medium" if validation_score > 60 else "low"
        }

    def _analyze_exception_handling(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """例外処理の分析"""
        statements = ast_data.get("statements", [])
        exception_score = 100
        exception_issues = []

        # DECLARATIVES部の分析
        has_declaratives = any(d.get("name") == "DECLARATIVES" for d in ast_data.get("divisions", []))
        if not has_declaratives:
            exception_score -= 30
            exception_issues.append("No DECLARATIVES section found")

        # 例外処理セクションの分析
        error_sections = [s for s in ast_data.get("sections", []) if "ERROR" in s.get("name", "")]
        if not error_sections:
            exception_score -= 20
            exception_issues.append("No dedicated error handling sections")

        return {
            "value": max(0, exception_score),
            "issues": exception_issues,
            "details": {
                "has_declaratives": has_declaratives,
                "error_sections": len(error_sections)
            },
            "evaluation": "high" if exception_score > 80 else "medium" if exception_score > 60 else "low"
        }

    def _analyze_data_integrity(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """データ整合性の分析"""
        statements = ast_data.get("statements", [])
        data_items = ast_data.get("data_items", [])
        integrity_score = 100
        integrity_issues = []

        # データ定義の整合性チェック
        for item in data_items:
            if item.get("redefines"):
                # REDEFINES項目のサイズチェック
                original_item = next((d for d in data_items if d["name"] == item["redefines"]), None)
                if original_item and item.get("size", 0) > original_item.get("size", 0):
                    integrity_score -= 10
                    integrity_issues.append(f"REDEFINES size mismatch: {item.get('name')}")

        # データ操作の整合性チェック
        move_statements = [s for s in statements if s["type"] == "MOVE"]
        for move in move_statements:
            if move.get("source_type") != move.get("target_type"):
                integrity_score -= 5
                integrity_issues.append(f"Type mismatch in MOVE operation at line {move.get('line_number')}")

        return {
            "value": max(0, integrity_score),
            "issues": integrity_issues,
            "details": {
                "redefines_count": len([d for d in data_items if d.get("redefines")]),
                "move_operations": len(move_statements),
                "type_mismatches": len([i for i in integrity_issues if "Type mismatch" in i])
            },
            "evaluation": "high" if integrity_score > 80 else "medium" if integrity_score > 60 else "low"
        }