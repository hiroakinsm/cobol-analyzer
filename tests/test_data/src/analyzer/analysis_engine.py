from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

@dataclass
class DivisionMetrics:
    """DIVISION毎のメトリクス"""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    sections: List[str] = None
    paragraphs: List[str] = None

    def __post_init__(self):
        if self.sections is None:
            self.sections = []
        if self.paragraphs is None:
            self.paragraphs = []

@dataclass
class AnalysisResult:
    """解析結果を保持するデータクラス"""
    source_id: str
    analysis_type: str
    timestamp: datetime
    metrics: Dict[str, Any]
    details: Dict[str, Any]

class AnalysisEngine:
    """COBOLソース解析エンジン"""
    def __init__(self, db_handler):
        self.db_handler = db_handler

    async def analyze_single_source(self, source_id: str) -> AnalysisResult:
        """単一ソースの解析を実行"""
        try:
            # メタデータとASTの取得
            metadata = await self.db_handler.get_metadata(source_id)
            ast = await self.db_handler.get_ast(source_id)

            # 基本メトリクスの収集
            metrics = await self._collect_basic_metrics(ast)
            
            # 詳細解析の実行
            details = await self._perform_detailed_analysis(ast, metadata)

            return AnalysisResult(
                source_id=source_id,
                analysis_type="single",
                timestamp=datetime.now(),
                metrics=metrics,
                details=details
            )
        except Exception as e:
            logger.error(f"単一ソース解析でエラー: {str(e)}")
            raise

    async def _collect_basic_metrics(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """基本メトリクスの収集"""
        return {
            'total_lines': self._count_total_lines(ast),
            'code_lines': self._count_code_lines(ast),
            'comment_lines': self._count_comment_lines(ast),
            'division_stats': self._analyze_divisions(ast),
            'complexity_metrics': self._calculate_complexity(ast)
        }

    async def _perform_detailed_analysis(self, ast: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """詳細解析の実行"""
        return {
            'structure_analysis': await self._analyze_structure(ast),
            'data_flow_analysis': await self._analyze_data_flow(ast),
            'quality_metrics': await self._analyze_code_quality(ast, metadata)
        }

    def _count_total_lines(self, ast: Dict[str, Any]) -> int:
        """総行数のカウント"""
        try:
            source_lines = ast.get('source_lines', [])
            return len(source_lines)
        except Exception as e:
            logger.error(f"総行数カウントでエラー: {str(e)}")
            return 0

    def _count_code_lines(self, ast: Dict[str, Any]) -> int:
        """実コード行数のカウント"""
        try:
            source_lines = ast.get('source_lines', [])
            code_lines = [line for line in source_lines if 
                         line.strip() and 
                         not line.strip().startswith('*') and 
                         not line.strip().startswith('/')]
            return len(code_lines)
        except Exception as e:
            logger.error(f"コード行数カウントでエラー: {str(e)}")
            return 0

    def _count_comment_lines(self, ast: Dict[str, Any]) -> int:
        """コメント行数のカウント"""
        try:
            source_lines = ast.get('source_lines', [])
            comment_lines = [line for line in source_lines if 
                           line.strip() and 
                           (line.strip().startswith('*') or 
                            line.strip().startswith('/'))]
            return len(comment_lines)
        except Exception as e:
            logger.error(f"コメント行数カウントでエラー: {str(e)}")
            return 0

    def _analyze_divisions(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """DIVISION構造の解析"""
        try:
            divisions = {
                'IDENTIFICATION': DivisionMetrics(),
                'ENVIRONMENT': DivisionMetrics(),
                'DATA': DivisionMetrics(),
                'PROCEDURE': DivisionMetrics()
            }
            
            current_division = None
            source_lines = ast.get('source_lines', [])
            
            for line in source_lines:
                line_text = line.strip()
                
                # DIVISION判定
                if 'DIVISION' in line_text:
                    for div_name in divisions.keys():
                        if f"{div_name} DIVISION" in line_text:
                            current_division = div_name
                            break
                
                if not current_division:
                    continue
                
                # 各DIVISIONの行数カウント
                div_metrics = divisions[current_division]
                div_metrics.total_lines += 1
                
                if not line_text:
                    div_metrics.blank_lines += 1
                elif line_text.startswith(('*', '/')):
                    div_metrics.comment_lines += 1
                else:
                    div_metrics.code_lines += 1
                
                # SECTIONとPARAGRAPHの収集
                if current_division == 'PROCEDURE':
                    if 'SECTION' in line_text:
                        section_name = line_text.split('SECTION')[0].strip()
                        div_metrics.sections.append(section_name)
                    elif line_text and line_text[0].isalpha() and '.' in line_text:
                        para_name = line_text.split('.')[0].strip()
                        div_metrics.paragraphs.append(para_name)

            return {
                div_name: {
                    'total_lines': metrics.total_lines,
                    'code_lines': metrics.code_lines,
                    'comment_lines': metrics.comment_lines,
                    'blank_lines': metrics.blank_lines,
                    'comment_ratio': (metrics.comment_lines / metrics.total_lines * 100) if metrics.total_lines > 0 else 0,
                    'sections': metrics.sections if div_name == 'PROCEDURE' else [],
                    'paragraphs': metrics.paragraphs if div_name == 'PROCEDURE' else []
                }
                for div_name, metrics in divisions.items()
            }
        except Exception as e:
            logger.error(f"DIVISION構造解析でエラー: {str(e)}")
            return {}

    def _calculate_complexity(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度の計算"""
        try:
            source_lines = ast.get('source_lines', [])
            complexity_metrics = {
                'cyclomatic_complexity': 0,
                'nested_level': 0,
                'max_nested_level': 0,
                'conditional_statements': 0,
                'perform_statements': 0
            }
            
            current_nested_level = 0
            
            for line in source_lines:
                line_text = line.strip().upper()
                
                # 条件分岐のカウント
                if any(keyword in line_text for keyword in ['IF ', 'EVALUATE ']):
                    complexity_metrics['cyclomatic_complexity'] += 1
                    complexity_metrics['conditional_statements'] += 1
                    current_nested_level += 1
                
                # PERFORM文のカウントとネストレベルの更新
                if 'PERFORM ' in line_text:
                    complexity_metrics['perform_statements'] += 1
                    if 'UNTIL ' in line_text or 'VARYING ' in line_text:
                        current_nested_level += 1
                
                # END-IF, END-EVALUATE等でネストレベルを減算
                if line_text.startswith('END-'):
                    current_nested_level = max(0, current_nested_level - 1)
                
                complexity_metrics['max_nested_level'] = max(
                    complexity_metrics['max_nested_level'],
                    current_nested_level
                )
            
            complexity_metrics['nested_level'] = current_nested_level
            
            return complexity_metrics
        except Exception as e:
            logger.error(f"複雑度計算でエラー: {str(e)}")
            return {}

    async def _analyze_structure(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """プログラム構造の解析"""
        try:
            # IDENTIFICATION DIVISIONの解析
            id_division = self._analyze_identification_division(ast)
            
            # PROCEDURE DIVISIONの構造解析
            procedure_structure = self._analyze_procedure_structure(ast)
            
            # プログラム全体の構造情報
            return {
                'program_info': id_division,
                'procedure_structure': procedure_structure,
                'call_hierarchy': await self._analyze_call_hierarchy(ast),
                'control_flow': await self._analyze_control_flow(ast)
            }
        except Exception as e:
            logger.error(f"プログラム構造解析でエラー: {str(e)}")
            return {}

    def _analyze_identification_division(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """IDENTIFICATION DIVISIONの解析"""
        try:
            id_info = {
                'program_id': None,
                'author': None,
                'installation': None,
                'date_written': None,
                'remarks': []
            }
            
            source_lines = ast.get('source_lines', [])
            in_id_division = False
            in_remarks = False
            
            for line in source_lines:
                line_text = line.strip().upper()
                
                if 'IDENTIFICATION DIVISION' in line_text:
                    in_id_division = True
                    continue
                elif in_id_division and any(div in line_text for div in ['ENVIRONMENT DIVISION', 'DATA DIVISION', 'PROCEDURE DIVISION']):
                    break
                
                if not in_id_division:
                    continue
                    
                if 'PROGRAM-ID.' in line_text:
                    id_info['program_id'] = line_text.split('PROGRAM-ID.')[1].strip().rstrip('.')
                elif 'AUTHOR.' in line_text:
                    id_info['author'] = line_text.split('AUTHOR.')[1].strip()
                elif 'INSTALLATION.' in line_text:
                    id_info['installation'] = line_text.split('INSTALLATION.')[1].strip()
                elif 'DATE-WRITTEN.' in line_text:
                    id_info['date_written'] = line_text.split('DATE-WRITTEN.')[1].strip()
                elif 'REMARKS.' in line_text:
                    in_remarks = True
                elif in_remarks and line_text.startswith(('*', '/')):
                    id_info['remarks'].append(line_text.lstrip('*/').strip())
            
            return id_info
        except Exception as e:
            logger.error(f"IDENTIFICATION DIVISION解析でエラー: {str(e)}")
            return {}

    def _analyze_procedure_structure(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """PROCEDURE DIVISION構造の解析"""
        try:
            structure = {
                'sections': [],
                'paragraphs': [],
                'hierarchy': {}
            }
            
            source_lines = ast.get('source_lines', [])
            current_section = None
            in_procedure = False
            
            for line in source_lines:
                line_text = line.strip().upper()
                
                if 'PROCEDURE DIVISION' in line_text:
                    in_procedure = True
                    continue
                
                if not in_procedure:
                    continue
                
                if 'SECTION' in line_text:
                    section_name = line_text.split('SECTION')[0].strip()
                    current_section = section_name
                    structure['sections'].append({
                        'name': section_name,
                        'paragraphs': []
                    })
                elif line_text and line_text[0].isalpha() and '.' in line_text:
                    para_name = line_text.split('.')[0].strip()
                    structure['paragraphs'].append({
                        'name': para_name,
                        'section': current_section
                    })
                    if current_section:
                        for section in structure['sections']:
                            if section['name'] == current_section:
                                section['paragraphs'].append(para_name)
                                break
            
            return structure
        except Exception as e:
            logger.error(f"PROCEDURE DIVISION構造解析でエラー: {str(e)}")
            return {}

    async def _analyze_call_hierarchy(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """呼び出し階層の解析"""
        try:
            hierarchy = {
                'internal_calls': [],  # 内部呼び出し（PERFORM）
                'external_calls': [],  # 外部呼び出し（CALL）
                'call_tree': {}       # 呼び出し階層ツリー
            }
            
            source_lines = ast.get('source_lines', [])
            current_paragraph = None
            
            for line in source_lines:
                line_text = line.strip().upper()
                
                # パラグラフ名の特定
                if line_text and line_text[0].isalpha() and '.' in line_text:
                    current_paragraph = line_text.split('.')[0].strip()
                    hierarchy['call_tree'][current_paragraph] = []
                
                # PERFORM文の解析
                if 'PERFORM ' in line_text and current_paragraph:
                    target = line_text.split('PERFORM ')[1].split()[0].strip()
                    hierarchy['internal_calls'].append({
                        'from': current_paragraph,
                        'to': target,
                        'type': 'PERFORM'
                    })
                    hierarchy['call_tree'][current_paragraph].append({
                        'target': target,
                        'type': 'PERFORM'
                    })
                
                # CALL文の解析
                if 'CALL ' in line_text and current_paragraph:
                    target = line_text.split('CALL ')[1].split()[0].strip().strip('"\'')
                    hierarchy['external_calls'].append({
                        'from': current_paragraph,
                        'to': target,
                        'type': 'CALL'
                    })
                    hierarchy['call_tree'][current_paragraph].append({
                        'target': target,
                        'type': 'CALL'
                    })
            
            return hierarchy
        except Exception as e:
            logger.error(f"呼び出し階層解析でエラー: {str(e)}")
            return {}

    async def _analyze_data_flow(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """データフローの解析"""
        try:
            data_flow = {
                'variables': {},        # 変数定義と使用状況
                'file_operations': [],  # ファイル操作
                'data_dependencies': {} # データ項目の依存関係
            }
            
            # DATA DIVISIONの解析
            data_items = self._analyze_data_division(ast)
            data_flow['variables'] = data_items
            
            # PROCEDURE DIVISIONでの使用状況解析
            usage_info = self._analyze_data_usage(ast, data_items)
            data_flow['data_dependencies'] = usage_info['dependencies']
            data_flow['file_operations'] = usage_info['file_ops']
            
            return data_flow
        except Exception as e:
            logger.error(f"データフロー解析でエラー: {str(e)}")
            return {}

    def _analyze_data_division(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """DATA DIVISIONの解析"""
        try:
            data_items = {}
            source_lines = ast.get('source_lines', [])
            in_data_division = False
            current_level = 0
            parent_stack = []
            
            for line in source_lines:
                line_text = line.strip().upper()
                
                if 'DATA DIVISION' in line_text:
                    in_data_division = True
                    continue
                elif in_data_division and any(div in line_text for div in ['PROCEDURE DIVISION']):
                    break
                
                if not in_data_division or not line_text or line_text.startswith(('*', '/')):
                    continue
                
                # レベル番号の取得
                if line_text[0].isdigit():
                    level_match = re.match(r'(\d+)\s+(\S+)', line_text)
                    if level_match:
                        level = int(level_match.group(1))
                        name = level_match.group(2)
                        
                        # データ項目の属性を解析
                        item_info = self._parse_data_item(line_text)
                        item_info['level'] = level
                        
                        # 階層構造の管理
                        while parent_stack and parent_stack[-1]['level'] >= level:
                            parent_stack.pop()
                        
                        if parent_stack:
                            parent = parent_stack[-1]['name']
                            item_info['parent'] = parent
                            if 'children' not in data_items[parent]:
                                data_items[parent]['children'] = []
                            data_items[parent]['children'].append(name)
                        
                        data_items[name] = item_info
                        parent_stack.append({'level': level, 'name': name})
            
            return data_items
        except Exception as e:
            logger.error(f"DATA DIVISION解析でエラー: {str(e)}")
            return {}

    def _parse_data_item(self, line_text: str) -> Dict[str, Any]:
        """データ項目の属性を解析"""
        item_info = {
            'usage': None,
            'picture': None,
            'occurs': None,
            'value': None,
            'redefines': None,
            'indexed_by': None
        }
        
        # PICTURE句の解析
        if 'PIC ' in line_text or 'PICTURE ' in line_text:
            pic_match = re.search(r'PIC(?:TURE)?\s+(\S+)', line_text)
            if pic_match:
                item_info['picture'] = pic_match.group(1)
        
        # USAGE句の解析
        for usage in ['BINARY', 'COMP', 'COMP-3', 'DISPLAY', 'PACKED-DECIMAL']:
            if f' {usage}' in line_text:
                item_info['usage'] = usage
                break
        
        # OCCURS句の解析
        occurs_match = re.search(r'OCCURS\s+(\d+)', line_text)
        if occurs_match:
            item_info['occurs'] = int(occurs_match.group(1))
        
        # VALUE句の解析
        value_match = re.search(r'VALUE\s+(?:IS\s+)?[\'"]?([^\'"]*)[\'""]?', line_text)
        if value_match:
            item_info['value'] = value_match.group(1)
        
        # REDEFINES句の解析
        redefines_match = re.search(r'REDEFINES\s+(\S+)', line_text)
        if redefines_match:
            item_info['redefines'] = redefines_match.group(1)
        
        # INDEXED BY句の解析
        indexed_match = re.search(r'INDEXED\s+BY\s+(\S+)', line_text)
        if indexed_match:
            item_info['indexed_by'] = indexed_match.group(1)
        
        return item_info

    def _analyze_data_usage(self, ast: Dict[str, Any], data_items: Dict[str, Any]) -> Dict[str, Any]:
        """データ項目の使用状況を解析"""
        try:
            usage_info = {
                'dependencies': {},
                'file_ops': []
            }
            
            source_lines = ast.get('source_lines', [])
            current_paragraph = None
            
            for i, line in enumerate(source_lines):
                line_text = line.strip().upper()
                
                # パラグラフの特定
                if line_text and line_text[0].isalpha() and '.' in line_text:
                    current_paragraph = line_text.split('.')[0].strip()
                    continue
                
                # ファイル操作の解析
                if any(op in line_text for op in ['OPEN', 'CLOSE', 'READ', 'WRITE', 'REWRITE', 'DELETE']):
                    file_op = {
                        'operation': None,
                        'file': None,
                        'line': i + 1,
                        'paragraph': current_paragraph
                    }
                    
                    for op in ['OPEN', 'CLOSE', 'READ', 'WRITE', 'REWRITE', 'DELETE']:
                        if op in line_text:
                            file_op['operation'] = op
                            file_parts = line_text.split(op)[1].strip().split()
                            if file_parts:
                                file_op['file'] = file_parts[0]
                            break
                    
                    usage_info['file_ops'].append(file_op)
                
                # データ項目の依存関係解析
                for item_name in data_items.keys():
                    if f' {item_name} ' in f' {line_text} ':
                        if item_name not in usage_info['dependencies']:
                            usage_info['dependencies'][item_name] = {
                                'used_in_paragraphs': set(),
                                'modified_in': set(),
                                'referenced_in': set()
                            }
                        
                        if current_paragraph:
                            usage_info['dependencies'][item_name]['used_in_paragraphs'].add(current_paragraph)
                        
                        # 代入操作の検出
                        if 'MOVE' in line_text and line_text.index(item_name) > line_text.index('MOVE'):
                            usage_info['dependencies'][item_name]['modified_in'].add(i + 1)
                        else:
                            usage_info['dependencies'][item_name]['referenced_in'].add(i + 1)
            
            # setをリストに変換（JSON化のため）
            for item in usage_info['dependencies'].values():
                item['used_in_paragraphs'] = list(item['used_in_paragraphs'])
                item['modified_in'] = list(item['modified_in'])
                item['referenced_in'] = list(item['referenced_in'])
            
            return usage_info
        except Exception as e:
            logger.error(f"データ使用状況解析でエラー: {str(e)}")
            return {'dependencies': {}, 'file_ops': []}

    async def _analyze_code_quality(self, ast: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """コード品質の解析"""
        try:
            quality_metrics = {
                'maintainability': self._analyze_maintainability(ast),
                'reliability': self._analyze_reliability(ast),
                'coding_standards': self._analyze_coding_standards(ast),
                'potential_issues': self._detect_potential_issues(ast)
            }
            return quality_metrics
        except Exception as e:
            logger.error(f"コード品質解析でエラー: {str(e)}")
            return {}

    def _analyze_maintainability(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """保守性の分析"""
        try:
            source_lines = ast.get('source_lines', [])
            metrics = {
                'paragraph_metrics': {},  # パラグラフごとのメトリクス
                'documentation': {        # ドキュメント状況
                    'comment_ratio': 0.0,
                    'header_quality': 'LOW',
                    'inline_comments': 0
                },
                'complexity_score': {     # 複雑度スコア
                    'value': 0,
                    'rating': 'LOW',
                    'factors': []
                }
            }

            # パラグラフ分析
            current_paragraph = None
            paragraph_lines = []
            
            for line in source_lines:
                line_text = line.strip().upper()
                
                if line_text and line_text[0].isalpha() and '.' in line_text:
                    if current_paragraph and paragraph_lines:
                        metrics['paragraph_metrics'][current_paragraph] = self._calculate_paragraph_metrics(paragraph_lines)
                    current_paragraph = line_text.split('.')[0].strip()
                    paragraph_lines = []
                elif current_paragraph:
                    paragraph_lines.append(line)

            # 最後のパラグラフを処理
            if current_paragraph and paragraph_lines:
                metrics['paragraph_metrics'][current_paragraph] = self._calculate_paragraph_metrics(paragraph_lines)

            # ドキュメント分析
            total_lines = len(source_lines)
            comment_lines = sum(1 for line in source_lines if line.strip().startswith(('*', '/')))
            metrics['documentation']['comment_ratio'] = (comment_lines / total_lines * 100) if total_lines > 0 else 0
            metrics['documentation']['inline_comments'] = sum(1 for line in source_lines if '//' in line)

            # ヘッダー品質の評価
            header_score = self._evaluate_header_quality(ast)
            metrics['documentation']['header_quality'] = header_score

            # 複雑度スコアの計算
            complexity_info = self._calculate_complexity_score(ast)
            metrics['complexity_score'] = complexity_info

            return metrics
        except Exception as e:
            logger.error(f"保守性分析でエラー: {str(e)}")
            return {}

    def _calculate_paragraph_metrics(self, lines: List[str]) -> Dict[str, Any]:
        """パラグラフごとのメトリクス計算"""
        return {
            'total_lines': len(lines),
            'code_lines': sum(1 for line in lines if line.strip() and not line.strip().startswith(('*', '/'))),
            'comment_lines': sum(1 for line in lines if line.strip().startswith(('*', '/'))),
            'complexity': sum(1 for line in lines if any(kw in line.upper() for kw in ['IF', 'EVALUATE', 'PERFORM'])),
            'has_goto': any('GO TO' in line.upper() for line in lines)
        }

    def _evaluate_header_quality(self, ast: Dict[str, Any]) -> str:
        """ヘッダーコメントの品質評価"""
        source_lines = ast.get('source_lines', [])
        header_lines = []
        
        for line in source_lines:
            if line.strip().startswith(('*', '/')):
                header_lines.append(line)
            elif line.strip() and not line.strip().startswith(('*', '/')):
                break

        # ヘッダー品質の評価基準
        required_elements = ['PROGRAM-ID', 'AUTHOR', 'DATE', 'PURPOSE']
        found_elements = sum(1 for elem in required_elements if any(elem in line.upper() for line in header_lines))
        
        if found_elements >= len(required_elements):
            return 'HIGH'
        elif found_elements >= len(required_elements) // 2:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _calculate_complexity_score(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度スコアの計算"""
        source_lines = ast.get('source_lines', [])
        factors = []
        score = 0

        # 複雑度要因の分析
        if len(source_lines) > 1000:
            factors.append('LARGE_PROGRAM')
            score += 2

        conditional_count = sum(1 for line in source_lines if 'IF ' in line.upper())
        if conditional_count > 50:
            factors.append('EXCESSIVE_CONDITIONS')
            score += 2

        goto_count = sum(1 for line in source_lines if 'GO TO' in line.upper())
        if goto_count > 0:
            factors.append('USES_GOTO')
            score += goto_count

        # スコアに基づく評価
        rating = 'HIGH' if score <= 3 else 'MEDIUM' if score <= 6 else 'LOW'

        return {
            'value': score,
            'rating': rating,
            'factors': factors
        }

    def _analyze_reliability(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """信頼性の分析"""
        try:
            source_lines = ast.get('source_lines', [])
            metrics = {
                'error_handling': {
                    'coverage': 0.0,
                    'handlers': []
                },
                'data_validation': {
                    'input_checks': [],
                    'boundary_checks': []
                },
                'file_operations': {
                    'with_status_check': [],
                    'without_status_check': []
                }
            }

            # エラーハンドリングの分析
            for i, line in enumerate(source_lines):
                line_text = line.strip().upper()
                
                # エラーハンドラーの検出
                if any(err in line_text for err in ['ON ERROR', 'ON EXCEPTION', 'ON OVERFLOW', 'ON SIZE ERROR']):
                    metrics['error_handling']['handlers'].append({
                        'type': next(err for err in ['ON ERROR', 'ON EXCEPTION', 'ON OVERFLOW', 'ON SIZE ERROR'] if err in line_text),
                        'line': i + 1
                    })

                # データ検証の検出
                if 'IF ' in line_text and any(check in line_text for check in ['NUMERIC', 'ALPHABETIC', '>', '<', '=']):
                    metrics['data_validation']['input_checks'].append({
                        'condition': line_text,
                        'line': i + 1
                    })

                # ファイル操作のステータスチェック
                if any(op in line_text for op in ['READ', 'WRITE', 'REWRITE', 'DELETE']):
                    if 'STATUS' in line_text or 'AT END' in line_text:
                        metrics['file_operations']['with_status_check'].append(i + 1)
                    else:
                        metrics['file_operations']['without_status_check'].append(i + 1)

            # エラーハンドリングのカバレッジ計算
            total_operations = len(metrics['file_operations']['with_status_check']) + len(metrics['file_operations']['without_status_check'])
            if total_operations > 0:
                metrics['error_handling']['coverage'] = len(metrics['file_operations']['with_status_check']) / total_operations * 100

            return metrics
        except Exception as e:
            logger.error(f"信頼性分析でエラー: {str(e)}")
            return {}

    def _analyze_coding_standards(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """コーディング規約の準拠確認"""
        try:
            source_lines = ast.get('source_lines', [])
            standards = {
                'violations': [],
                'compliance_score': 100.0,
                'recommendations': []
            }

            violation_count = 0
            
            for i, line in enumerate(source_lines):
                line_text = line.strip().upper()
                
                # 命名規則違反のチェック
                if line_text and line_text[0].isdigit() and not line_text.startswith(('66', '77', '88')):
                    standards['violations'].append({
                        'type': 'NAMING_CONVENTION',
                        'line': i + 1,
                        'description': '不適切なレベル番号'
                    })
                    violation_count += 1

                # GOTO文の使用チェック
                if 'GO TO' in line_text:
                    standards['violations'].append({
                        'type': 'GOTO_USAGE',
                        'line': i + 1,
                        'description': 'GO TO文の使用'
                    })
                    violation_count += 1

                # 過度に長い行のチェック
                if len(line) > 72:
                    standards['violations'].append({
                        'type': 'LINE_LENGTH',
                        'line': i + 1,
                        'description': '行が72文字を超過'
                    })
                    violation_count += 1

            # コンプライアンススコアの計算
            if len(source_lines) > 0:
                standards['compliance_score'] = max(0, 100 - (violation_count / len(source_lines) * 100))

            # 改善推奨事項の生成
            if standards['violations']:
                standards['recommendations'] = self._generate_recommendations(standards['violations'])

            return standards
        except Exception as e:
            logger.error(f"コーディング規約チェックでエラー: {str(e)}")
            return {}

    def _detect_potential_issues(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """潜在的な問題の検出"""
        try:
            source_lines = ast.get('source_lines', [])
            issues = {
                'performance_issues': [],
                'security_risks': [],
                'logic_issues': [],
                'resource_issues': []
            }

            open_files = set()
            current_paragraph = None
            
            for i, line in enumerate(source_lines):
                line_text = line.strip().upper()
                
                # パラグラフの追跡
                if line_text and line_text[0].isalpha() and '.' in line_text:
                    current_paragraph = line_text.split('.')[0].strip()

                # パフォーマンス問題の検出
                if 'PERFORM ' in line_text and current_paragraph:
                    # 再帰的なPERFORM
                    if current_paragraph in line_text:
                        issues['performance_issues'].append({
                            'type': 'RECURSIVE_PERFORM',
                            'line': i + 1,
                            'description': '再帰的なPERFORM文の使用'
                        })

                # リソース問題の検出
                if 'OPEN ' in line_text:
                    file_name = line_text.split('OPEN ')[1].split()[0]
                    open_files.add(file_name)
                elif 'CLOSE ' in line_text:
                    file_name = line_text.split('CLOSE ')[1].split()[0]
                    if file_name in open_files:
                        open_files.remove(file_name)

                # ロジック問題の検出
                if 'IF ' in line_text:
                    # 空のIF文
                    next_line = source_lines[i + 1].strip() if i + 1 < len(source_lines) else ''
                    if next_line.startswith(('ELSE', 'END-IF')):
                        issues['logic_issues'].append({
                            'type': 'EMPTY_IF',
                            'line': i + 1,
                            'description': '空のIF文'
                        })

            # 未クローズのファイルをリソース問題として報告
            for file_name in open_files:
                issues['resource_issues'].append({
                    'type': 'UNCLOSED_FILE',
                    'file': file_name,
                    'description': 'プログラム終了時に開いたままのファイル'
                })

            return issues
        except Exception as e:
            logger.error(f"潜在的問題の検出でエラー: {str(e)}")
            return {}

    def _generate_recommendations(self, violations: List[Dict[str, Any]]) -> List[str]:
        """違反に基づく改善推奨事項の生成"""
        recommendations = []
        violation_types = set(v['type'] for v in violations)
        
        if 'GOTO_USAGE' in violation_types:
            recommendations.append('GO TO文の使用を避け、構造化プログラミングの原則に従ってください')
        
        if 'LINE_LENGTH' in violation_types:
            recommendations.append('行の長さは72文字以内に収めてください')
        
        if 'NAMING_CONVENTION' in violation_types:
            recommendations.append('適切なレベル番号の使用を確認してください')
        
        return recommendations

    async def _analyze_control_flow(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """制御フローの解析"""
        try:
            control_flow = {
                'conditional_blocks': [],  # IF, EVALUATE等の条件分岐
                'loop_blocks': [],        # PERFORM UNTIL等のループ
                'goto_statements': [],    # GO TO文
                'error_handlers': [],     # エラーハンドリング
                'flow_graph': {}          # 制御フローグラフ
            }
            
            source_lines = ast.get('source_lines', [])
            current_paragraph = None
            current_block = None
            block_stack = []
            
            for i, line in enumerate(source_lines):
                line_text = line.strip().upper()
                
                # パラグラフの開始位置を記録
                if line_text and line_text[0].isalpha() and '.' in line_text:
                    current_paragraph = line_text.split('.')[0].strip()
                    control_flow['flow_graph'][current_paragraph] = {
                        'start_line': i + 1,
                        'end_line': None,
                        'contains': []
                    }
                
                # 条件分岐の解析
                if 'IF ' in line_text:
                    block = {
                        'type': 'IF',
                        'start_line': i + 1,
                        'end_line': None,
                        'condition': line_text.split('IF ')[1].split('THEN')[0].strip(),
                        'paragraph': current_paragraph,
                        'nested_level': len(block_stack)
                    }
                    block_stack.append(block)
                    control_flow['conditional_blocks'].append(block)
                    if current_paragraph:
                        control_flow['flow_graph'][current_paragraph]['contains'].append(block)
                
                elif 'EVALUATE ' in line_text:
                    block = {
                        'type': 'EVALUATE',
                        'start_line': i + 1,
                        'end_line': None,
                        'subject': line_text.split('EVALUATE ')[1].strip(),
                        'paragraph': current_paragraph,
                        'cases': [],
                        'nested_level': len(block_stack)
                    }
                    block_stack.append(block)
                    control_flow['conditional_blocks'].append(block)
                    if current_paragraph:
                        control_flow['flow_graph'][current_paragraph]['contains'].append(block)
                
                # ループ構造の解析
                elif 'PERFORM ' in line_text and ('UNTIL ' in line_text or 'VARYING ' in line_text):
                    block = {
                        'type': 'LOOP',
                        'start_line': i + 1,
                        'end_line': None,
                        'condition': line_text,
                        'paragraph': current_paragraph,
                        'nested_level': len(block_stack)
                    }
                    block_stack.append(block)
                    control_flow['loop_blocks'].append(block)
                    if current_paragraph:
                        control_flow['flow_graph'][current_paragraph]['contains'].append(block)
                
                # GO TO文の解析
                elif 'GO TO ' in line_text:
                    goto = {
                        'from_paragraph': current_paragraph,
                        'to_paragraph': line_text.split('GO TO ')[1].strip(),
                        'line': i + 1
                    }
                    control_flow['goto_statements'].append(goto)
                
                # エラーハンドリングの解析
                elif any(err in line_text for err in ['ON ERROR', 'ON EXCEPTION', 'ON OVERFLOW', 'ON SIZE ERROR']):
                    handler = {
                        'type': 'ERROR_HANDLER',
                        'condition': line_text,
                        'paragraph': current_paragraph,
                        'start_line': i + 1,
                        'end_line': None
                    }
                    control_flow['error_handlers'].append(handler)
                
                # ブロックの終了を検出
                elif line_text.startswith('END-'):
                    if block_stack:
                        current_block = block_stack.pop()
                        current_block['end_line'] = i + 1
                
                # WHEN句の解析（EVALUATE用）
                elif line_text.startswith('WHEN ') and block_stack:
                    current_block = block_stack[-1]
                    if current_block['type'] == 'EVALUATE':
                        current_block['cases'].append({
                            'condition': line_text.split('WHEN ')[1].strip(),
                            'start_line': i + 1
                        })
            
            # パラグラフの終了行を設定
            last_paragraph = None
            for paragraph in control_flow['flow_graph'].values():
                if last_paragraph:
                    last_paragraph['end_line'] = paragraph['start_line'] - 1
                last_paragraph = paragraph
            if last_paragraph:
                last_paragraph['end_line'] = len(source_lines)
            
            return control_flow
        except Exception as e:
            logger.error(f"制御フロー解析でエラー: {str(e)}")
            return {} 

    async def analyze_multiple_sources(self, source_ids: List[str]) -> Dict[str, Any]:
        """複数ソースの解析とサマリ生成"""
        try:
            # 個別ソースの解析結果を収集
            analysis_results = []
            for source_id in source_ids:
                result = await self.analyze_single_source(source_id)
                analysis_results.append(result)

            # サマリ解析の実行
            summary = {
                'overview': self._generate_overview(analysis_results),
                'complexity_analysis': self._analyze_complexity_distribution(analysis_results),
                'quality_metrics': self._summarize_quality_metrics(analysis_results),
                'common_patterns': await self._analyze_common_patterns(analysis_results),
                'cross_references': await self._analyze_cross_references(analysis_results)
            }

            return summary
        except Exception as e:
            logger.error(f"複数ソース解析でエラー: {str(e)}")
            raise

    def _generate_overview(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """全体概要の生成"""
        try:
            total_lines = 0
            total_code_lines = 0
            total_comment_lines = 0
            division_stats = {
                'IDENTIFICATION': {'total': 0, 'code': 0, 'comment': 0},
                'ENVIRONMENT': {'total': 0, 'code': 0, 'comment': 0},
                'DATA': {'total': 0, 'code': 0, 'comment': 0},
                'PROCEDURE': {'total': 0, 'code': 0, 'comment': 0}
            }

            # 基本メトリクスの集計
            for result in results:
                metrics = result.metrics
                total_lines += metrics['total_lines']
                total_code_lines += metrics['code_lines']
                total_comment_lines += metrics['comment_lines']

                # DIVISION統計の集計
                for div_name, stats in metrics['division_stats'].items():
                    division_stats[div_name]['total'] += stats['total_lines']
                    division_stats[div_name]['code'] += stats['code_lines']
                    division_stats[div_name]['comment'] += stats['comment_lines']

            return {
                'total_programs': len(results),
                'total_lines': total_lines,
                'total_code_lines': total_code_lines,
                'total_comment_lines': total_comment_lines,
                'average_program_size': total_lines / len(results) if results else 0,
                'comment_ratio': (total_comment_lines / total_lines * 100) if total_lines > 0 else 0,
                'division_distribution': division_stats
            }
        except Exception as e:
            logger.error(f"概要生成でエラー: {str(e)}")
            return {}

    def _analyze_complexity_distribution(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """複雑度分布の分析"""
        try:
            complexity_data = {
                'cyclomatic_complexity': [],
                'nested_levels': [],
                'conditional_counts': [],
                'perform_counts': []
            }

            for result in results:
                complexity = result.metrics['complexity_metrics']
                complexity_data['cyclomatic_complexity'].append(complexity['cyclomatic_complexity'])
                complexity_data['nested_levels'].append(complexity['max_nested_level'])
                complexity_data['conditional_counts'].append(complexity['conditional_statements'])
                complexity_data['perform_counts'].append(complexity['perform_statements'])

            return {
                'complexity_stats': {
                    'cyclomatic': {
                        'min': min(complexity_data['cyclomatic_complexity']),
                        'max': max(complexity_data['cyclomatic_complexity']),
                        'avg': sum(complexity_data['cyclomatic_complexity']) / len(results)
                    },
                    'nested_level': {
                        'min': min(complexity_data['nested_levels']),
                        'max': max(complexity_data['nested_levels']),
                        'avg': sum(complexity_data['nested_levels']) / len(results)
                    }
                },
                'complexity_distribution': {
                    'low': len([c for c in complexity_data['cyclomatic_complexity'] if c <= 10]),
                    'medium': len([c for c in complexity_data['cyclomatic_complexity'] if 10 < c <= 20]),
                    'high': len([c for c in complexity_data['cyclomatic_complexity'] if c > 20])
                }
            }
        except Exception as e:
            logger.error(f"複雑度分布分析でエラー: {str(e)}")
            return {} 

    def _summarize_quality_metrics(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """品質メトリクスのサマリ分析"""
        try:
            quality_summary = {
                'maintainability': {
                    'scores': [],
                    'issues': {
                        'high': 0,
                        'medium': 0,
                        'low': 0
                    },
                    'common_problems': {}
                },
                'reliability': {
                    'error_handling_coverage': [],
                    'data_validation_coverage': [],
                    'risk_levels': {
                        'high': 0,
                        'medium': 0,
                        'low': 0
                    }
                },
                'coding_standards': {
                    'compliance_scores': [],
                    'common_violations': {},
                    'overall_compliance': 0.0
                },
                'documentation': {
                    'comment_ratios': [],
                    'documentation_quality': {
                        'good': 0,
                        'adequate': 0,
                        'poor': 0
                    }
                }
            }

            # 各プログラムの品質メトリクスを集計
            for result in results:
                quality_metrics = result.details.get('quality_metrics', {})
                
                # 保守性の集計
                maintainability = quality_metrics.get('maintainability', {})
                complexity_score = maintainability.get('complexity_score', {}).get('value', 0)
                quality_summary['maintainability']['scores'].append(complexity_score)
                
                # 問題の重要度によるカウント
                if complexity_score > 20:
                    quality_summary['maintainability']['issues']['high'] += 1
                elif complexity_score > 10:
                    quality_summary['maintainability']['issues']['medium'] += 1
                else:
                    quality_summary['maintainability']['issues']['low'] += 1

                # 共通の問題点を集計
                for factor in maintainability.get('complexity_score', {}).get('factors', []):
                    quality_summary['maintainability']['common_problems'][factor] = \
                        quality_summary['maintainability']['common_problems'].get(factor, 0) + 1

                # 信頼性の集計
                reliability = quality_metrics.get('reliability', {})
                error_coverage = reliability.get('error_handling', {}).get('coverage', 0)
                quality_summary['reliability']['error_handling_coverage'].append(error_coverage)
                
                # データ検証カバレッジの集計
                validation_count = len(reliability.get('data_validation', {}).get('input_checks', []))
                total_data_items = len(result.details.get('data_flow_analysis', {}).get('variables', {}))
                validation_coverage = (validation_count / total_data_items * 100) if total_data_items > 0 else 0
                quality_summary['reliability']['data_validation_coverage'].append(validation_coverage)

                # コーディング規約準拠の集計
                standards = quality_metrics.get('coding_standards', {})
                compliance_score = standards.get('compliance_score', 0)
                quality_summary['coding_standards']['compliance_scores'].append(compliance_score)
                
                # 共通の違反を集計
                for violation in standards.get('violations', []):
                    violation_type = violation.get('type')
                    if violation_type:
                        quality_summary['coding_standards']['common_violations'][violation_type] = \
                            quality_summary['coding_standards']['common_violations'].get(violation_type, 0) + 1

                # ドキュメント品質の集計
                documentation = maintainability.get('documentation', {})
                comment_ratio = documentation.get('comment_ratio', 0)
                quality_summary['documentation']['comment_ratios'].append(comment_ratio)
                
                if comment_ratio >= 20:
                    quality_summary['documentation']['documentation_quality']['good'] += 1
                elif comment_ratio >= 10:
                    quality_summary['documentation']['documentation_quality']['adequate'] += 1
                else:
                    quality_summary['documentation']['documentation_quality']['poor'] += 1

            # 平均値と全体的な評価の計算
            if results:
                quality_summary['coding_standards']['overall_compliance'] = \
                    sum(quality_summary['coding_standards']['compliance_scores']) / len(results)

            # 共通の問題点とコーディング規約違反をソート
            quality_summary['maintainability']['common_problems'] = \
                dict(sorted(quality_summary['maintainability']['common_problems'].items(),
                           key=lambda x: x[1], reverse=True))
            quality_summary['coding_standards']['common_violations'] = \
                dict(sorted(quality_summary['coding_standards']['common_violations'].items(),
                           key=lambda x: x[1], reverse=True))

            return quality_summary
        except Exception as e:
            logger.error(f"品質メトリクスのサマリ分析でエラー: {str(e)}")
            return {} 

    async def _analyze_common_patterns(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """共通パターンの分析"""
        try:
            patterns = {
                'code_patterns': {
                    'perform_patterns': {},    # PERFORM文のパターン
                    'data_patterns': {},       # データ処理パターン
                    'error_patterns': {},      # エラー処理パターン
                    'io_patterns': {}          # 入出力パターン
                },
                'structure_patterns': {
                    'division_patterns': {},   # DIVISION構造パターン
                    'section_patterns': {},    # SECTION構造パターン
                    'paragraph_patterns': {}   # パラグラフ構造パターン
                },
                'naming_patterns': {
                    'program_naming': {},      # プログラム命名パターン
                    'data_naming': {},         # データ項目命名パターン
                    'paragraph_naming': {}     # パラグラフ命名パターン
                }
            }

            # 各ソースのパターンを分析
            for result in results:
                # コードパターンの分析
                self._analyze_code_patterns(result, patterns['code_patterns'])
                
                # 構造パターンの分析
                self._analyze_structure_patterns(result, patterns['structure_patterns'])
                
                # 命名パターンの分析
                self._analyze_naming_patterns(result, patterns['naming_patterns'])

            # パターンの頻度でソートと上位パターンの抽出
            patterns = self._sort_and_filter_patterns(patterns)

            return patterns
        except Exception as e:
            logger.error(f"共通パターン分析でエラー: {str(e)}")
            return {}

    def _analyze_code_patterns(self, result: AnalysisResult, patterns: Dict[str, Dict]):
        """コードパターンの分析"""
        try:
            structure = result.details.get('structure_analysis', {})
            control_flow = structure.get('control_flow', {})
            
            # PERFORM文パターンの分析
            for block in control_flow.get('loop_blocks', []):
                pattern_key = self._normalize_pattern(block.get('condition', ''))
                patterns['perform_patterns'][pattern_key] = \
                    patterns['perform_patterns'].get(pattern_key, 0) + 1

            # エラー処理パターンの分析
            for handler in control_flow.get('error_handlers', []):
                pattern_key = self._normalize_pattern(handler.get('condition', ''))
                patterns['error_patterns'][pattern_key] = \
                    patterns['error_patterns'].get(pattern_key, 0) + 1

            # データ処理パターンの分析
            data_flow = result.details.get('data_flow_analysis', {})
            for operation in data_flow.get('file_operations', []):
                pattern_key = f"{operation.get('operation', '')}_{operation.get('file', '')}"
                patterns['io_patterns'][pattern_key] = \
                    patterns['io_patterns'].get(pattern_key, 0) + 1

        except Exception as e:
            logger.error(f"コードパターン分析でエラー: {str(e)}")

    def _analyze_structure_patterns(self, result: AnalysisResult, patterns: Dict[str, Dict]):
        """構造パターンの分析"""
        try:
            # DIVISION構造のパターン
            division_stats = result.metrics.get('division_stats', {})
            division_pattern = '_'.join(f"{k}:{v['total_lines']}" 
                                      for k, v in division_stats.items())
            patterns['division_patterns'][division_pattern] = \
                patterns['division_patterns'].get(division_pattern, 0) + 1

            # SECTION/パラグラフ構造のパターン
            structure = result.details.get('structure_analysis', {})
            procedure = structure.get('procedure_structure', {})
            
            for section in procedure.get('sections', []):
                section_pattern = f"SECTION_{len(section.get('paragraphs', []))}_PARAS"
                patterns['section_patterns'][section_pattern] = \
                    patterns['section_patterns'].get(section_pattern, 0) + 1

            for paragraph in procedure.get('paragraphs', []):
                if 'contains' in paragraph:
                    pattern_key = self._analyze_paragraph_pattern(paragraph['contains'])
                    patterns['paragraph_patterns'][pattern_key] = \
                        patterns['paragraph_patterns'].get(pattern_key, 0) + 1

        except Exception as e:
            logger.error(f"構造パターン分析でエラー: {str(e)}")

    def _analyze_naming_patterns(self, result: AnalysisResult, patterns: Dict[str, Dict]):
        """命名パターンの分析"""
        try:
            # プログラム名のパターン
            program_info = result.details.get('structure_analysis', {}).get('program_info', {})
            if program_id := program_info.get('program_id'):
                prefix = program_id[:3]
                patterns['program_naming'][prefix] = \
                    patterns['program_naming'].get(prefix, 0) + 1

            # データ項目の命名パターン
            data_flow = result.details.get('data_flow_analysis', {})
            for var_name in data_flow.get('variables', {}):
                prefix = self._extract_naming_pattern(var_name)
                patterns['data_naming'][prefix] = \
                    patterns['data_naming'].get(prefix, 0) + 1

            # パラグラフの命名パターン
            structure = result.details.get('structure_analysis', {})
            for para in structure.get('procedure_structure', {}).get('paragraphs', []):
                prefix = self._extract_naming_pattern(para.get('name', ''))
                patterns['paragraph_naming'][prefix] = \
                    patterns['paragraph_naming'].get(prefix, 0) + 1

        except Exception as e:
            logger.error(f"命名パターン分析でエラー: {str(e)}")

    def _normalize_pattern(self, pattern: str) -> str:
        """パターン文字列の正規化"""
        return re.sub(r'\s+', ' ', pattern.strip().upper())

    def _analyze_paragraph_pattern(self, contents: List[Dict]) -> str:
        """パラグラフの内部構造パターンを分析"""
        pattern_elements = []
        for item in contents:
            if item_type := item.get('type'):
                pattern_elements.append(item_type)
        return '_'.join(pattern_elements)

    def _extract_naming_pattern(self, name: str) -> str:
        """命名パターンの抽出"""
        name = name.upper()
        match = re.match(r'^([A-Z-]+)', name)
        return match.group(1) if match else name[:3]

    def _sort_and_filter_patterns(self, patterns: Dict[str, Dict]) -> Dict[str, Dict]:
        """パターンのソートとフィルタリング"""
        result = {}
        for category, pattern_dict in patterns.items():
            result[category] = {}
            for pattern_type, pattern_counts in pattern_dict.items():
                # 出現頻度でソート
                sorted_patterns = dict(sorted(pattern_counts.items(), 
                                            key=lambda x: x[1], 
                                            reverse=True))
                # 上位10パターンを抽出
                result[category][pattern_type] = dict(list(sorted_patterns.items())[:10])
        return result 

    async def _analyze_cross_references(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """相互参照の分析"""
        try:
            cross_refs = {
                'program_calls': {},      # プログラム間の呼び出し関係
                'data_dependencies': {},   # データ項目の依存関係
                'file_dependencies': {},   # ファイル操作の依存関係
                'common_resources': {      # 共有リソース
                    'files': {},
                    'data_items': {},
                    'call_targets': {}
                }
            }

            # プログラム間の関係分析
            for result in results:
                program_id = result.details.get('structure_analysis', {}).get('program_info', {}).get('program_id')
                if not program_id:
                    continue

                # 呼び出し関係の分析
                call_hierarchy = result.details.get('structure_analysis', {}).get('call_hierarchy', {})
                external_calls = call_hierarchy.get('external_calls', [])
                
                if program_id not in cross_refs['program_calls']:
                    cross_refs['program_calls'][program_id] = {
                        'calls': [],      # このプログラムが呼び出す他のプログラム
                        'called_by': [],   # このプログラムを呼び出す他のプログラム
                        'call_count': 0    # 呼び出し回数
                    }

                # 外部呼び出しの記録
                for call in external_calls:
                    target = call.get('to')
                    if target:
                        cross_refs['program_calls'][program_id]['calls'].append(target)
                        cross_refs['common_resources']['call_targets'][target] = \
                            cross_refs['common_resources']['call_targets'].get(target, 0) + 1

                # データ依存関係の分析
                data_flow = result.details.get('data_flow_analysis', {})
                variables = data_flow.get('variables', {})
                
                for var_name, var_info in variables.items():
                    if var_info.get('external_reference'):  # 外部参照データ項目
                        if var_name not in cross_refs['data_dependencies']:
                            cross_refs['data_dependencies'][var_name] = {
                                'referenced_by': [],
                                'reference_count': 0
                            }
                        cross_refs['data_dependencies'][var_name]['referenced_by'].append(program_id)
                        cross_refs['data_dependencies'][var_name]['reference_count'] += 1
                        cross_refs['common_resources']['data_items'][var_name] = \
                            cross_refs['common_resources']['data_items'].get(var_name, 0) + 1

                # ファイル依存関係の分析
                file_ops = data_flow.get('file_operations', [])
                for op in file_ops:
                    file_name = op.get('file')
                    if file_name:
                        if file_name not in cross_refs['file_dependencies']:
                            cross_refs['file_dependencies'][file_name] = {
                                'accessed_by': [],
                                'operations': {
                                    'READ': 0,
                                    'WRITE': 0,
                                    'REWRITE': 0,
                                    'DELETE': 0
                                }
                            }
                        if program_id not in cross_refs['file_dependencies'][file_name]['accessed_by']:
                            cross_refs['file_dependencies'][file_name]['accessed_by'].append(program_id)
                        operation = op.get('operation', 'UNKNOWN')
                        if operation in cross_refs['file_dependencies'][file_name]['operations']:
                            cross_refs['file_dependencies'][file_name]['operations'][operation] += 1
                        cross_refs['common_resources']['files'][file_name] = \
                            cross_refs['common_resources']['files'].get(file_name, 0) + 1

            # 相互参照の逆方向リンクを構築
            self._build_reverse_references(cross_refs['program_calls'])
            
            # 共有リソースの使用頻度でソート
            cross_refs['common_resources'] = self._sort_common_resources(cross_refs['common_resources'])
            
            # 依存関係の分析結果を追加
            cross_refs['dependency_analysis'] = self._analyze_dependencies(cross_refs)

            return cross_refs
        except Exception as e:
            logger.error(f"相互参照分析でエラー: {str(e)}")
            return {}

    def _build_reverse_references(self, program_calls: Dict[str, Dict]):
        """プログラム間の逆方向参照を構築"""
        try:
            # called_by関係の構築
            for program, refs in program_calls.items():
                for target in refs['calls']:
                    if target in program_calls:
                        if program not in program_calls[target]['called_by']:
                            program_calls[target]['called_by'].append(program)
                            program_calls[target]['call_count'] += 1
        except Exception as e:
            logger.error(f"逆方向参照構築でエラー: {str(e)}")

    def _sort_common_resources(self, resources: Dict[str, Dict]) -> Dict[str, Dict]:
        """共有リソースを使用頻度でソート"""
        try:
            sorted_resources = {}
            for resource_type, items in resources.items():
                sorted_resources[resource_type] = dict(
                    sorted(items.items(), key=lambda x: x[1], reverse=True)
                )
            return sorted_resources
        except Exception as e:
            logger.error(f"共有リソースのソートでエラー: {str(e)}")
            return resources

    def _analyze_dependencies(self, cross_refs: Dict[str, Any]) -> Dict[str, Any]:
        """依存関係の分析"""
        try:
            analysis = {
                'high_impact_programs': [],    # 影響度の高いプログラム
                'isolated_programs': [],       # 独立したプログラム
                'circular_dependencies': [],    # 循環参照
                'risk_assessment': {}          # リスク評価
            }

            # 影響度の高いプログラムを特定
            for program, refs in cross_refs['program_calls'].items():
                impact_score = len(refs['called_by']) + len(refs['calls'])
                if impact_score > 5:  # 閾値は要調整
                    analysis['high_impact_programs'].append({
                        'program': program,
                        'impact_score': impact_score,
                        'called_by_count': len(refs['called_by']),
                        'calls_count': len(refs['calls'])
                    })

            # 独立したプログラムを特定
            for program, refs in cross_refs['program_calls'].items():
                if not refs['calls'] and not refs['called_by']:
                    analysis['isolated_programs'].append(program)

            # 循環参照の検出
            analysis['circular_dependencies'] = self._detect_circular_dependencies(
                cross_refs['program_calls']
            )

            # リスク評価
            analysis['risk_assessment'] = self._assess_dependency_risks(
                cross_refs, analysis['circular_dependencies']
            )

            return analysis
        except Exception as e:
            logger.error(f"依存関係分析でエラー: {str(e)}")
            return {} 