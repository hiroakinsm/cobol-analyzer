# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/structure/components.py

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum

@dataclass
class DivisionInfo:
    name: str
    start_line: int
    end_line: int
    sections: List['SectionInfo']
    statements_count: int
    complexity: int

@dataclass
class SectionInfo:
    name: str
    parent_division: str
    start_line: int
    end_line: int
    paragraphs: List['ParagraphInfo']
    statements_count: int
    complexity: int

@dataclass
class ParagraphInfo:
    name: str
    parent_section: str
    start_line: int
    end_line: int
    statements: List[Dict[str, Any]]
    complexity: int

class StructureAnalyzer(ASTAnalyzer):
    """プログラム構造の解析基底クラス"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.divisions: List[DivisionInfo] = []
        self.sections: List[SectionInfo] = []
        self.paragraphs: List[ParagraphInfo] = []

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_divisions(ast)
        self._analyze_sections()
        self._analyze_paragraphs()
        return {
            "divisions": self.divisions,
            "sections": self.sections,
            "paragraphs": self.paragraphs,
            "structure_metrics": self._calculate_structure_metrics()
        }

    def _analyze_divisions(self, ast: Dict[str, Any]) -> None:
        """DIVISION構造の解析"""
        for division_node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.DIVISION):
            division_info = self._create_division_info(division_node)
            self.divisions.append(division_info)

    def _analyze_sections(self) -> None:
        """SECTION解析を実行"""
        try:
            for division in self.divisions:
                for section_node in self._get_section_nodes(division):
                    section = SectionInfo(
                        name=section_node["name"],
                        parent_division=division.name,
                        start_line=section_node.get("source_line", 0),
                        end_line=section_node.get("end_line", 0),
                        paragraphs=self._get_paragraphs(section_node),
                        statements_count=self._count_statements(section_node),
                        complexity=self._calculate_section_complexity(section_node)
                    )

                    # セクションの依存関係を分析
                    dependencies = self._analyze_section_dependencies(section_node)
                    section.dependencies = dependencies

                    # セクション内のデータ参照を分析
                    data_references = self._analyze_section_data_references(section_node)
                    section.data_references = data_references

                self.sections.append(section)

            # セクション間の順序と依存関係を検証
            self._validate_section_order()
            self._validate_section_dependencies()

        except Exception as e:
            self.logger.error(f"Section analysis failed: {str(e)}")
            raise

    def _analyze_paragraphs(self) -> None:
        """PARAGRAPH解析を実行"""
        try:
            for section in self.sections:
                for paragraph_node in self._get_paragraph_nodes(section):
                    paragraph = ParagraphInfo(
                        name=paragraph_node["name"],
                        parent_section=section.name,
                        start_line=paragraph_node.get("source_line", 0),
                        end_line=paragraph_node.get("end_line", 0),
                        statements=self._get_statements(paragraph_node),
                        complexity=self._calculate_paragraph_complexity(paragraph_node)
                    )

                    # パラグラフの制御フローを分析
                    control_flow = self._analyze_paragraph_control_flow(paragraph_node)
                    paragraph.control_flow = control_flow

                    # パラグラフ内のデータアクセスを分析
                    data_access = self._analyze_paragraph_data_access(paragraph_node)
                    paragraph.data_access = data_access

                    section.paragraphs.append(paragraph)

            # パラグラフ間の関係を検証
            self._validate_paragraph_references()
            self._validate_paragraph_flow()

        except Exception as e:
            self.logger.error(f"Paragraph analysis failed: {str(e)}")
            raise

    def _calculate_structure_metrics(self) -> Dict[str, Any]:
        """構造に関するメトリクスを計算"""
        return {
            "total_divisions": len(self.divisions),
            "total_sections": len(self.sections),
            "total_paragraphs": len(self.paragraphs),
            "average_section_size": self._calculate_average_section_size(),
            "average_paragraph_size": self._calculate_average_paragraph_size(),
            "structure_depth": self._calculate_structure_depth()
        }

class ControlFlowAnalyzer(ASTAnalyzer):
    """制御フローの解析クラス"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.control_flows: List[Dict[str, Any]] = []
        self.entry_points: Set[str] = set()
        self.exit_points: Set[str] = set()
        self.cyclic_dependencies: List[List[str]] = []

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_control_flow(ast)
        return {
            "control_flow_graph": self.control_flows,
            "entry_points": list(self.entry_points),
            "exit_points": list(self.exit_points),
            "cyclic_dependencies": self.cyclic_dependencies,
            "control_flow_metrics": self._calculate_control_flow_metrics()
        }

    def _analyze_control_flow(self, ast: Dict[str, Any]) -> None:
        """制御フローの解析を実行"""
        self._analyze_perform_statements(ast)
        self._analyze_conditional_statements(ast)
        self._analyze_goto_statements(ast)
        self._detect_cycles()

    def _analyze_perform_statements(self, ast: Dict[str, Any]) -> None:
        """PERFORM文の解析を実行"""
        try:
            for node in self._traverse_ast(ast):
                if node["type"] == "statement" and node["statement_type"] == "PERFORM":
                    perform_info = {
                        "type": "perform",
                        "location": (node.get("source_line", 0), node.get("column", 0)),
                        "target": node.get("target"),
                        "perform_type": self._determine_perform_type(node),
                        "times": node.get("times"),
                        "varying": node.get("varying"),
                        "until_condition": node.get("until_condition"),
                        "through": node.get("through")
                    }

                    # PERFORM TIMESの解析
                    if perform_info["perform_type"] == "times":
                        self._analyze_perform_times(node, perform_info)

                    # PERFORM UNTILの解析
                    elif perform_info["perform_type"] == "until":
                        self._analyze_perform_until(node, perform_info)

                    # PERFORM VARYINGの解析
                    elif perform_info["perform_type"] == "varying":
                        self._analyze_perform_varying(node, perform_info)

                    self.control_flows.append(perform_info)

        except Exception as e:
            self.logger.error(f"PERFORM statement analysis failed: {str(e)}")
            raise

    def _analyze_conditional_statements(self, ast: Dict[str, Any]) -> None:
        """条件分岐の解析を実行"""
        try:
            for node in self._traverse_ast(ast):
                if node["type"] == "statement":
                    if node["statement_type"] == "IF":
                        # IF文の解析
                        condition_info = {
                            "type": "condition",
                            "statement_type": "IF",
                            "location": (node.get("source_line", 0), node.get("column", 0)),
                            "condition": node.get("condition"),
                            "then_statements": self._analyze_then_branch(node),
                            "else_statements": self._analyze_else_branch(node),
                            "nesting_level": self._calculate_nesting_level(node)
                        }
                        self.control_flows.append(condition_info)

                    elif node["statement_type"] == "EVALUATE":
                        # EVALUATE文の解析
                        evaluate_info = {
                            "type": "condition",
                            "statement_type": "EVALUATE",
                            "location": (node.get("source_line", 0), node.get("column", 0)),
                            "subject": node.get("subject"),
                            "cases": self._analyze_evaluate_cases(node),
                            "when_other": self._analyze_when_other(node),
                            "nesting_level": self._calculate_nesting_level(node)
                        }
                        self.control_flows.append(evaluate_info)

        except Exception as e:
            self.logger.error(f"Conditional statement analysis failed: {str(e)}")
            raise

    def _analyze_goto_statements(self, ast: Dict[str, Any]) -> None:
        """GOTO文の解析を実行"""
        try:
            for node in self._traverse_ast(ast):
                if node["type"] == "statement" and node["statement_type"] == "GO":
                    goto_info = {
                        "type": "goto",
                        "location": (node.get("source_line", 0), node.get("column", 0)),
                        "target": node.get("target"),
                        "depending": node.get("depending"),
                        "targets": node.get("targets", []),
                        "scope": self._determine_goto_scope(node)
                    }

                    # GOTOの対象が有効かチェック
                    if not self._validate_goto_target(goto_info["target"]):
                        self.logger.warning(f"Invalid GOTO target at line {goto_info['location'][0]}")

                    # GOTOの影響範囲を分析
                    impact = self._analyze_goto_impact(node)
                    goto_info["impact"] = impact

                    self.control_flows.append(goto_info)

        except Exception as e:
            self.logger.error(f"GOTO statement analysis failed: {str(e)}")
            raise

    def _detect_cycles(self) -> None:
        """循環参照の検出を実行"""
        try:
            visited = set()
            current_path = []
        
            def dfs(node: str) -> None:
                if node in current_path:
                    # 循環参照を検出
                    cycle = current_path[current_path.index(node):]
                    self.cyclic_dependencies.append(cycle)
                    return
                
                if node in visited:
                    return
                
                visited.add(node)
                current_path.append(node)
            
                # 隣接ノードを探索
                if node in self.control_flows:
                    for target in self._get_node_targets(node):
                        dfs(target)
                    
                current_path.pop()
        
            # 各ノードからDFSを開始
            for node in self.entry_points:
                dfs(node)

            # 検出された循環参照の分析
            for cycle in self.cyclic_dependencies:
                self._analyze_cycle_impact(cycle)

        except Exception as e:
            self.logger.error(f"Cycle detection failed: {str(e)}")
            raise

    def _calculate_control_flow_metrics(self) -> Dict[str, Any]:
        return {
            "cyclomatic_complexity": self._calculate_cyclomatic_complexity(),
            "essential_complexity": self._calculate_essential_complexity(),
            "control_density": self._calculate_control_density()
        }

class StatementAnalyzer(ASTAnalyzer):
    """文レベルの解析クラス"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.statements: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.statement_patterns: Dict[str, int] = defaultdict(int)

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_statements(ast)
        return {
            "statements": self.statements,
            "statement_patterns": self.statement_patterns,
            "statement_metrics": self._calculate_statement_metrics()
        }

    def _analyze_statements(self, ast: Dict[str, Any]) -> None:
        """文の解析を実行"""
        for statement_node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.STATEMENT):
            statement_type = statement_node.get("statement_type")
            self.statements[statement_type].append(statement_node)
            self.statement_patterns[statement_type] += 1
            self._analyze_statement_complexity(statement_node)

    def _analyze_statement_complexity(self, statement_node: Dict[str, Any]) -> int:
        """文の複雑度を解析"""
        try:
            complexity = 0
            statement_type = statement_node.get("statement_type")

            # 文タイプに基づく基本複雑度
            if statement_type in ["IF", "EVALUATE"]:
                complexity += self._calculate_condition_complexity(statement_node)
            elif statement_type == "PERFORM":
                complexity += self._calculate_perform_complexity(statement_node)
            elif statement_type in ["STRING", "UNSTRING"]:
                complexity += self._calculate_string_operation_complexity(statement_node)
            
            # オペランドの複雑度
            operand_complexity = self._calculate_operand_complexity(statement_node)
            complexity += operand_complexity

            # ネストレベルによる補正
            nesting_level = self._calculate_nesting_level(statement_node)
            complexity *= (1 + (nesting_level * 0.1))

            return complexity

        except Exception as e:
            self.logger.error(f"Statement complexity analysis failed: {str(e)}")
            raise

    def _calculate_statement_metrics(self) -> Dict[str, Any]:
        """文に関するメトリクスを計算"""
        return {
            "total_statements": sum(len(stmts) for stmts in self.statements.values()),
            "statement_type_distribution": dict(self.statement_patterns),
            "average_statement_complexity": self._calculate_average_statement_complexity()
        }

class CallGraphAnalyzer(ASTAnalyzer):
    """呼び出し関係の解析クラス"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.call_graph: Dict[str, Set[str]] = defaultdict(set)
        self.entry_points: Set[str] = set()
        self.leaf_nodes: Set[str] = set()

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._build_call_graph(ast)
        return {
            "call_graph": self._convert_call_graph_to_dict(),
            "entry_points": list(self.entry_points),
            "leaf_nodes": list(self.leaf_nodes),
            "call_metrics": self._calculate_call_metrics()
        }

    def _build_call_graph(self, ast: Dict[str, Any]) -> None:
        """呼び出しグラフの構築"""
        for call_node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.STATEMENT):
            if call_node.get("statement_type") in ["CALL", "INVOKE"]:
                self._process_call_statement(call_node)

    def _process_call_statement(self, call_node: Dict[str, Any]) -> None:
        """CALL文の処理を実行"""
        try:
            caller = call_node.get("parent_paragraph")
            callee = call_node.get("program_name")

            if caller and callee:
                # 呼び出し関係の登録
                self.call_graph[caller].add(callee)

                # パラメータの解析
                params = self._analyze_call_parameters(call_node)

                # 呼び出し情報の記録
                call_info = {
                    "caller": caller,
                    "callee": callee,
                    "location": (call_node.get("source_line", 0), call_node.get("column", 0)),
                    "parameters": params,
                    "using": call_node.get("using", []),
                    "giving": call_node.get("giving"),
                    "cancellable": call_node.get("cancellable", False)
                }

                # エントリーポイントとリーフノードの更新
                if caller not in self.leaf_nodes:
                    self.entry_points.add(caller)
                if callee not in self.call_graph:
                    self.leaf_nodes.add(callee)

        except Exception as e:
            self.logger.error(f"Call statement processing failed: {str(e)}")
            raise

    def _convert_call_graph_to_dict(self) -> Dict[str, List[str]]:
        """呼び出しグラフを辞書形式に変換"""
        return {caller: list(callees) for caller, callees in self.call_graph.items()}

    def _calculate_call_metrics(self) -> Dict[str, Any]:
        """呼び出し関係のメトリクスを計算"""
        return {
            "total_calls": sum(len(callees) for callees in self.call_graph.values()),
            "max_call_depth": self._calculate_max_call_depth(),
            "average_calls_per_module": self._calculate_average_calls()
        }
