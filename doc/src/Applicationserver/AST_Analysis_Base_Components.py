# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/ast/base.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Iterator, Generic, TypeVar
from abc import ABC, abstractmethod
from enum import Enum
import pymongo
from bson import ObjectId
import logging
from collections import defaultdict

class ASTNodeType(Enum):
    PROGRAM = "program"
    DIVISION = "division"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    STATEMENT = "statement"
    DATA_ITEM = "data_item"
    CONDITION = "condition"
    EXPRESSION = "expression"

@dataclass
class ASTNode:
    node_type: ASTNodeType
    value: Any
    children: List['ASTNode']
    attributes: Dict[str, Any]
    source_line: Optional[int] = None
    source_column: Optional[int] = None

class ASTVisitor(ABC):
    """ASTの走査を行う基底クラス"""
    @abstractmethod
    def visit_node(self, node: Dict[str, Any]) -> None:
        """各ノードの訪問処理を実装"""
        # メトリクス収集のための基本情報を取得
        node_type = node.get('type')
        node_value = node.get('value')
        node_attributes = node.get('attributes', {})
        
        # ノードタイプに応じた処理の実行
        if node_type == ASTNodeType.PROGRAM.value:
            self._visit_program_node(node)
        elif node_type == ASTNodeType.DIVISION.value:
            self._visit_division_node(node)
        elif node_type == ASTNodeType.SECTION.value:
            self._visit_section_node(node)
        elif node_type == ASTNodeType.PARAGRAPH.value:
            self._visit_paragraph_node(node)
        elif node_type == ASTNodeType.STATEMENT.value:
            self._visit_statement_node(node)
        elif node_type == ASTNodeType.DATA_ITEM.value:
            self._visit_data_item_node(node)
            
        # 子ノードの再帰的な処理
        for child in node.get('children', []):
            self.visit_node(child)

    def _visit_program_node(self, node: Dict[str, Any]) -> None:
    """プログラムノードの処理"""
        # プログラム全体の情報を収集
        program_name = node.get('program_id')
        division_count = len([child for child in node.get('children', []) 
                         if child.get('type') == ASTNodeType.DIVISION.value])
    
        # プログラムレベルのメトリクスを記録
        self.program_metrics = {
            'program_name': program_name,
            'division_count': division_count,
            'start_line': node.get('source_line', 0),
            'total_lines': self._calculate_total_lines(node),
            'identification_info': self._extract_identification_info(node)
        }

    def _visit_division_node(self, node: Dict[str, Any]) -> None:
    """DIVISIONノードの処理"""
        division_name = node.get('name')
        # 各DIVISIONの構造を分析
        division_metrics = {
            'name': division_name,
            'section_count': len([child for child in node.get('children', [])
                                if child.get('type') == ASTNodeType.SECTION.value]),
            'start_line': node.get('source_line', 0),
            'end_line': node.get('end_line', 0),
            'size': self._calculate_division_size(node)
        }
    
        # DIVISION特有の解析
        if division_name == 'DATA DIVISION':
            division_metrics.update(self._analyze_data_division(node))
        elif division_name == 'PROCEDURE DIVISION':
            division_metrics.update(self._analyze_procedure_division(node))
        
        self.division_metrics[division_name] = division_metrics

    def _visit_section_node(self, node: Dict[str, Any]) -> None:
    """SECTIONノードの処理"""
        section_name = node.get('name')
        parent_division = node.get('parent_division')
    
        # セクションの詳細メトリクスを収集
        section_metrics = {
            'name': section_name,
            'parent_division': parent_division,
            'paragraph_count': len([child for child in node.get('children', [])
                                  if child.get('type') == ASTNodeType.PARAGRAPH.value]),
            'start_line': node.get('source_line', 0),
            'end_line': node.get('end_line', 0),
            'complexity': self._calculate_section_complexity(node),
            'data_references': self._collect_data_references(node)
        }
    
        self.section_metrics[section_name] = section_metrics

    def _visit_paragraph_node(self, node: Dict[str, Any]) -> None:
    """PARAGRAPHノードの処理"""
        paragraph_name = node.get('name')
        parent_section = node.get('parent_section')
    
        # パラグラフの詳細メトリクスを収集
        paragraph_metrics = {
            'name': paragraph_name,
            'parent_section': parent_section,
            'statement_count': len([child for child in node.get('children', [])
                                  if child.get('type') == ASTNodeType.STATEMENT.value]),
            'start_line': node.get('source_line', 0),
            'end_line': node.get('end_line', 0),
            'cyclomatic_complexity': self._calculate_paragraph_complexity(node),
            'nesting_depth': self._calculate_nesting_depth(node),
            'references': self._collect_paragraph_references(node)
        }
    
        self.paragraph_metrics[paragraph_name] = paragraph_metrics

    def _visit_statement_node(self, node: Dict[str, Any]) -> None:
    """STATEMENTノードの処理"""
        statement_type = node.get('statement_type')
    
        # 文の詳細情報を収集
        statement_info = {
            'type': statement_type,
            'line': node.get('source_line', 0),
            'operands': node.get('operands', []),
            'complexity': self._calculate_statement_complexity(node),
            'references': self._extract_statement_references(node)
        }
    
        # 文タイプ別の特殊解析
        if statement_type in ['CALL', 'INVOKE']:
            statement_info.update(self._analyze_call_statement(node))
        elif statement_type in ['IF', 'EVALUATE']:
            statement_info.update(self._analyze_conditional_statement(node))
        elif statement_type in ['PERFORM']:
            statement_info.update(self._analyze_perform_statement(node))
        
        self.statement_metrics.setdefault(statement_type, []).append(statement_info)

    def _visit_data_item_node(self, node: Dict[str, Any]) -> None:
    """DATA ITEMノードの処理"""
        data_name = node.get('name')
        level = node.get('level')
    
        # データ項目の詳細情報を収集
        data_item_info = {
            'name': data_name,
            'level': level,
            'picture': node.get('picture'),
            'usage': node.get('usage'),
            'occurs': node.get('occurs'),
            'redefines': node.get('redefines'),
            'line': node.get('source_line', 0),
            'size': self._calculate_data_item_size(node),
            'referenced_by': self._collect_data_item_references(node)
        }
    
        # レベル別の特殊処理
        if level == 1:
            data_item_info.update(self._analyze_group_item(node))
        elif level == 77:
            data_item_info.update(self._analyze_independent_item(node))
        elif level == 88:
            data_item_info.update(self._analyze_condition_item(node))
        
        self.data_item_metrics[data_name] = data_item_info

class ASTAnalyzer(ABC):
    """AST解析の基底クラス"""
    def __init__(self, ast_accessor: 'ASTAccessor'):
        self.ast_accessor = ast_accessor
        self.results: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """AST解析を実行"""
        try:
            # 基本的な解析の実行
            self._analyze_structure(ast)
            self._analyze_metrics(ast)
            self._analyze_dependencies(ast)
            
            # 結果の検証と整形
            self._validate_results()
            self._format_results()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"AST analysis failed: {str(e)}")
            raise

    def _analyze_structure(self, ast: Dict[str, Any]) -> None:
        """構造解析の実行"""
        structure_metrics = {
            'total_nodes': self._count_nodes(ast),
            'depth': self._calculate_depth(ast),
            'complexity': self._calculate_complexity(ast)
        }
        self.results['structure'] = structure_metrics

    def _analyze_metrics(self, ast: Dict[str, Any]) -> None:
        """メトリクス解析の実行"""
        metrics = {
            'cyclomatic_complexity': self._calculate_cyclomatic_complexity(ast),
            'halstead_metrics': self._calculate_halstead_metrics(ast),
            'maintainability_index': self._calculate_maintainability_index(ast)
        }
        self.results['metrics'] = metrics

    def _analyze_dependencies(self, ast: Dict[str, Any]) -> None:
        """依存関係の解析"""
        dependencies = {
            'data_dependencies': self._analyze_data_dependencies(ast),
            'control_dependencies': self._analyze_control_dependencies(ast),
            'module_dependencies': self._analyze_module_dependencies(ast)
        }
        self.results['dependencies'] = dependencies

class ASTMetricsCollector:
    """ASTからメトリクスを収集"""
    def __init__(self):
        self.metrics: Dict[str, Any] = {}

    def collect_metrics(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスを収集"""
        self._collect_size_metrics(ast)
        self._collect_complexity_metrics(ast)
        self._collect_dependency_metrics(ast)
        return self.metrics

    def _count_statements(self, ast: Dict[str, Any]) -> int:
        """文の数をカウント"""
        statement_count = 0
        for node in self._traverse_ast(ast):
            if node.get('type') == ASTNodeType.STATEMENT.value:
                statement_count += 1
        return statement_count

    def _calculate_cyclomatic_complexity(self, ast: Dict[str, Any]) -> int:
        """循環的複雑度を計算"""
        complexity = 1  # 基本値
        for node in self._traverse_ast(ast):
            if node.get('type') == ASTNodeType.STATEMENT.value:
                statement_type = node.get('statement_type', '')
                if statement_type in ['IF', 'EVALUATE', 'PERFORM UNTIL', 'PERFORM VARYING']:
                    complexity += 1
        return complexity

    def _calculate_max_nesting_depth(self, ast: Dict[str, Any]) -> int:
        """最大ネストの深さを計算"""
        max_depth = 0
        current_depth = 0
        
        def traverse_depth(node: Dict[str, Any]):
            nonlocal max_depth, current_depth
            
            if node.get('type') == ASTNodeType.STATEMENT.value:
                statement_type = node.get('statement_type', '')
                if statement_type in ['IF', 'EVALUATE', 'PERFORM']:
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                    
            for child in node.get('children', []):
                traverse_depth(child)
                
            if node.get('type') == ASTNodeType.STATEMENT.value:
                if statement_type in ['IF', 'EVALUATE', 'PERFORM']:
                    current_depth -= 1
        
        traverse_depth(ast)
        return max_depth

    def _calculate_halstead_metrics(self, ast: Dict[str, Any]) -> Dict[str, float]:
        """Halsteadメトリクスを計算"""
        operators = set()
        operands = set()
        total_operators = 0
        total_operands = 0
        
        for node in self._traverse_ast(ast):
            if node.get('type') == ASTNodeType.STATEMENT.value:
                # オペレータの収集
                operator = node.get('statement_type')
                if operator:
                    operators.add(operator)
                    total_operators += 1
                
                # オペランドの収集
                for operand in node.get('operands', []):
                    operands.add(operand)
                    total_operands += 1
        
        n1 = len(operators)  # ユニークなオペレータ数
        n2 = len(operands)   # ユニークなオペランド数
        N1 = total_operators # 総オペレータ数
        N2 = total_operands  # 総オペランド数
        
        # Halsteadメトリクスの計算
        program_length = N1 + N2
        vocabulary = n1 + n2
        volume = program_length * (vocabulary.bit_length() if vocabulary > 0 else 0)
        difficulty = (n1/2) * (N2/n2) if n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            'program_length': program_length,
            'vocabulary': vocabulary,
            'volume': volume,
            'difficulty': difficulty,
            'effort': effort
        }

    def _analyze_data_dependencies(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """データ依存関係を分析"""
        dependencies = []
        data_items = {}
        
        # データ項目の収集
        for node in self._traverse_ast(ast):
            if node.get('type') == ASTNodeType.DATA_ITEM.value:
                data_items[node.get('name')] = node
        
        # 依存関係の分析
        for node in self._traverse_ast(ast):
            if node.get('type') == ASTNodeType.STATEMENT.value:
                statement_type = node.get('statement_type')
                operands = node.get('operands', [])
                
                if statement_type in ['MOVE', 'COMPUTE']:
                    # 代入文の依存関係を分析
                    if len(operands) >= 2:
                        dependencies.append({
                            'source': operands[1],
                            'target': operands[0],
                            'type': 'data_flow',
                            'statement': statement_type
                        })
        
        return dependencies

    def _analyze_control_dependencies(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制御依存関係を分析"""
        dependencies = []
        control_stack = []
        
        def traverse_control(node: Dict[str, Any], parent_control: Optional[Dict[str, Any]] = None):
            if node.get('type') == ASTNodeType.STATEMENT.value:
                statement_type = node.get('statement_type')
                
                if statement_type in ['IF', 'EVALUATE', 'PERFORM']:
                    # 制御構造の開始
                    control_info = {
                        'type': statement_type,
                        'condition': node.get('condition'),
                        'location': (node.get('line', 0), node.get('column', 0))
                    }
                    control_stack.append(control_info)
                    
                    if parent_control:
                        dependencies.append({
                            'source': parent_control['type'],
                            'target': statement_type,
                            'condition': parent_control['condition'],
                            'location': parent_control['location']
                        })
                    
                    # 子ノードの処理
                    for child in node.get('children', []):
                        traverse_control(child, control_info)
                    
                    control_stack.pop()
                else:
                    # 通常の文の依存関係
                    if control_stack:
                        current_control = control_stack[-1]
                        dependencies.append({
                            'source': current_control['type'],
                            'target': statement_type,
                            'condition': current_control['condition'],
                            'location': current_control['location']
                        })
        
        traverse_control(ast)
        return dependencies

    def _traverse_ast(self, ast: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """ASTの走査"""
        yield ast
        for child in ast.get('children', []):
            yield from self._traverse_ast(child)