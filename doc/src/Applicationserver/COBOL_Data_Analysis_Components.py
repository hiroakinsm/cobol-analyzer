# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/data/components.py

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
from enum import Enum

@dataclass
class DataItem:
    name: str
    level: int
    parent: Optional[str]
    children: List[str]
    picture: Optional[str]
    usage: Optional[str]
    occurs: Optional[int]
    redefines: Optional[str]
    value: Optional[str]
    location: Tuple[int, int]  # 行番号、列番号

@dataclass
class DataDependency:
    source: str
    target: str
    dependency_type: str  # 'redefines', 'occurs depending', 'value', etc.
    location: Tuple[int, int]

@dataclass
class DataFlow:
    source_item: str
    target_item: str
    statement_type: str  # 'MOVE', 'COMPUTE', etc.
    location: Tuple[int, int]
    conditions: List[str]  # 実行条件

class DataHierarchyAnalyzer(ASTAnalyzer):
    """データ項目の階層構造を解析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.data_items: Dict[str, DataItem] = {}
        self.hierarchy_groups: Dict[str, List[str]] = defaultdict(list)
        self.redefines_groups: Dict[str, List[str]] = defaultdict(list)

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_working_storage(ast)
        self._analyze_linkage_section(ast)
        self._analyze_file_section(ast)
        self._build_hierarchy_groups()
        
        return {
            "data_items": self.data_items,
            "hierarchy": self.hierarchy_groups,
            "redefines": self.redefines_groups,
            "metrics": self._calculate_hierarchy_metrics()
        }

    def _analyze_working_storage(self, ast: Dict[str, Any]) -> None:
        """WORKING-STORAGE SECTIONの解析"""
        for data_node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.DATA_ITEM):
            if data_node.get("section") == "WORKING-STORAGE":
                self._process_data_item(data_node)

    def _process_data_item(self, node: Dict[str, Any]) -> None:
        """データ項目の処理"""
        item = DataItem(
            name=node["name"],
            level=node["level"],
            parent=self._find_parent(node),
            children=[],
            picture=node.get("picture"),
            usage=node.get("usage"),
            occurs=node.get("occurs"),
            redefines=node.get("redefines"),
            value=node.get("value"),
            location=(node.get("line", 0), node.get("column", 0))
        )
        self.data_items[item.name] = item

    def _calculate_hierarchy_metrics(self) -> Dict[str, Any]:
        """階層構造に関するメトリクス計算"""
        return {
            "total_items": len(self.data_items),
            "max_depth": self._calculate_max_depth(),
            "average_children": self._calculate_average_children(),
            "redefines_count": len(self.redefines_groups)
        }

class DataDependencyAnalyzer(ASTAnalyzer):
    """データ項目間の依存関係を解析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.dependencies: List[DataDependency] = []
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.critical_items: Set[str] = set()

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_redefines_dependencies(ast)
        self._analyze_occurs_dependencies(ast)
        self._analyze_value_dependencies(ast)
        self._identify_critical_items()
        
        return {
            "dependencies": self.dependencies,
            "dependency_graph": self._convert_graph_to_dict(),
            "critical_items": list(self.critical_items),
            "metrics": self._calculate_dependency_metrics()
        }

    def _analyze_redefines_dependencies(self, ast: Dict[str, Any]) -> None:
        """REDEFINES句による依存関係の解析"""
        for data_node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.DATA_ITEM):
            if redefines := data_node.get("redefines"):
                self._add_dependency(data_node["name"], redefines, "redefines")

    def _identify_critical_items(self) -> None:
        """重要なデータ項目の特定"""
        for item, dependencies in self.dependency_graph.items():
            if len(dependencies) > 5:  # 依存関係が多いものを重要とする
                self.critical_items.add(item)

    def _calculate_dependency_metrics(self) -> Dict[str, Any]:
        """依存関係に関するメトリクス計算"""
        return {
            "total_dependencies": len(self.dependencies),
            "average_dependencies": self._calculate_average_dependencies(),
            "max_dependencies": self._calculate_max_dependencies(),
            "critical_items_count": len(self.critical_items)
        }

class DataFlowAnalyzer(ASTAnalyzer):
    """データフローを解析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.data_flows: List[DataFlow] = []
        self.flow_graph: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: defaultdict(list))
        self.transformations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_moves(ast)
        self._analyze_computations(ast)
        self._analyze_string_operations(ast)
        self._build_flow_graph()
        
        return {
            "data_flows": self.data_flows,
            "flow_graph": self.flow_graph,
            "transformations": self.transformations,
            "metrics": self._calculate_flow_metrics()
        }

    def _analyze_moves(self, ast: Dict[str, Any]) -> None:
        """MOVE文の解析"""
        for statement in self.ast_accessor.get_node_by_type(ast, ASTNodeType.STATEMENT):
            if statement.get("statement_type") == "MOVE":
                self._process_move_statement(statement)

    def _analyze_computations(self, ast: Dict[str, Any]) -> None:
        """COMPUTE文の解析"""
        for statement in self.ast_accessor.get_node_by_type(ast, ASTNodeType.STATEMENT):
            if statement.get("statement_type") == "COMPUTE":
                self._process_compute_statement(statement)

    def _build_flow_graph(self) -> None:
        """データフローグラフの構築"""
        for flow in self.data_flows:
            self.flow_graph[flow.source_item][flow.target_item].append(flow.statement_type)

    def _calculate_flow_metrics(self) -> Dict[str, Any]:
        """データフローに関するメトリクス計算"""
        return {
            "total_flows": len(self.data_flows),
            "move_operations": self._count_operation_type("MOVE"),
            "compute_operations": self._count_operation_type("COMPUTE"),
            "string_operations": self._count_operation_type("STRING"),
            "average_transformations": self._calculate_average_transformations()
        }

class DataQualityAnalyzer(ASTAnalyzer):
    """データ品質の解析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.quality_issues: List[Dict[str, Any]] = []
        self.validation_points: List[Dict[str, Any]] = []

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_data_validation(ast)
        self._analyze_error_handling(ast)
        self._analyze_data_consistency(ast)
        
        return {
            "quality_issues": self.quality_issues,
            "validation_points": self.validation_points,
            "metrics": self._calculate_quality_metrics()
        }

    def _analyze_data_validation(self, ast: Dict[str, Any]) -> None:
        """データ検証処理の解析

        Args:
            ast: 解析対象のAST

        解析内容：
        - データ項目の検証ロジック
        - 入力値チェック
        - 範囲チェック
        - 必須項目チェック
        """
        try:
            for node in self._traverse_ast(ast):
                if node.get("type") == ASTNodeType.STATEMENT.value:
                    statement_type = node.get("statement_type")
                    
                    # データ検証関連の文を分析
                    if statement_type in ["IF", "EVALUATE"]:
                        conditions = self._extract_validation_conditions(node)
                        if conditions:
                            self.validation_points.append({
                                "type": "data_validation",
                                "location": (node.get("line", 0), node.get("column", 0)),
                                "statement_type": statement_type,
                                "conditions": conditions,
                                "target_items": self._identify_validated_items(node),
                                "validation_type": self._determine_validation_type(conditions)
                            })

                    # 88レベルの条件名による検証
                    elif node.get("level") == 88:
                        self.validation_points.append({
                            "type": "condition_name",
                            "location": (node.get("line", 0), node.get("column", 0)),
                            "parent_item": node.get("parent_name"),
                            "values": node.get("values", []),
                            "validation_type": "value_set"
                        })

            # 検証の網羅性をチェック
            self._analyze_validation_coverage()
        
            # 未検証の重要データ項目を特定
            unvalidated_items = self._identify_unvalidated_items()
            if unvalidated_items:
                self.quality_issues.append({
                    "type": "missing_validation",
                    "severity": "warning",
                    "items": unvalidated_items,
                    "message": "Important data items lack validation"
                })

        except Exception as e:
            self.logger.error(f"Data validation analysis failed: {str(e)}")
            raise

    def _analyze_error_handling(self, ast: Dict[str, Any]) -> None:
        """エラー処理の解析

        Args:
        ast: 解析対象のAST

        解析内容：
        - エラー処理ロジック
        - 例外処理
        - リカバリー処理
        - エラーメッセージ
        """
        try:
            for node in self._traverse_ast(ast):
                if node.get("type") == ASTNodeType.STATEMENT.value:
                    statement_type = node.get("statement_type")
                    
                    # ON SIZE ERRORやINVALID KEYなどのエラー処理
                    if statement_type in ["ON", "USE", "INVALID KEY"]:
                        error_handler = {
                            "type": "error_handler",
                            "location": (node.get("line", 0), node.get("column", 0)),
                            "handler_type": statement_type,
                            "handled_operations": self._identify_handled_operations(node),
                            "recovery_actions": self._analyze_recovery_actions(node)
                        }
                        self.validation_points.append(error_handler)
    
                    # エラーメッセージの表示
                    elif statement_type == "DISPLAY" and self._is_error_message(node):
                        self.validation_points.append({
                            "type": "error_message",
                            "location": (node.get("line", 0), node.get("column", 0)),
                            "message": node.get("message"),
                            "severity": self._determine_message_severity(node)
                        })

            # エラー処理の網羅性を分析
            coverage = self._analyze_error_handling_coverage()
            
            # エラー処理が不十分な操作を特定
            unhandled_operations = self._identify_unhandled_operations()
            if unhandled_operations:
                self.quality_issues.append({
                    "type": "missing_error_handling",
                    "severity": "warning",
                    "operations": unhandled_operations,
                    "message": "Critical operations lack error handling"
                })

            # リカバリー処理の妥当性をチェック
            invalid_recovery = self._validate_recovery_procedures()
            if invalid_recovery:
                self.quality_issues.append({
                    "type": "invalid_recovery",
                    "severity": "error",
                    "procedures": invalid_recovery,
                    "message": "Invalid error recovery procedures detected"
                })

        except Exception as e:
            self.logger.error(f"Error handling analysis failed: {str(e)}")
            raise

    def _calculate_quality_metrics(self) -> Dict[str, Any]:
        """品質に関するメトリクス計算"""
        return {
            "validation_coverage": self._calculate_validation_coverage(),
            "error_handling_coverage": self._calculate_error_handling_coverage(),
            "data_consistency_score": self._calculate_consistency_score()
        }
