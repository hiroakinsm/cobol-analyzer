from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import re
from .base_parser import Parser, Token, ASTNode

logger = logging.getLogger(__name__)

@dataclass
class BatchStatement:
    """バッチ処理文の構造"""
    type: str
    name: str
    parameters: Dict[str, Any]
    line_number: int

class BatchParser(Parser):
    """バッチ処理構文解析器"""
    
    def __init__(self):
        super().__init__()
        self._batch_patterns = {
            'SORT': self._parse_sort,
            'MERGE': self._parse_merge,
            'CHECKPOINT': self._parse_checkpoint,
            'RESTART': self._parse_restart,
            'RETURN': self._parse_return,
            'RELEASE': self._parse_release
        }
        self._file_patterns = re.compile(r'SELECT\s+(\w+)\s+ASSIGN\s+TO\s+(\w+)')

    def parse(self, tokens: List[Token]) -> ASTNode:
        """バッチ処理コードの構文解析"""
        try:
            self._tokens = tokens
            self._current_pos = 0
            
            # ルートノードの作成
            root = ASTNode(
                type="BATCH_ROOT",
                value=None,
                children=[],
                metadata={'source_type': 'BATCH'}
            )
            
            # バッチ処理セクションの検出
            while self._peek():
                if self._is_batch_section():
                    section = self._parse_batch_section()
                    if section:
                        root.children.append(section)
                else:
                    self._consume()
            
            return root
            
        except Exception as e:
            logger.error(f"バッチ処理解析でエラー: {str(e)}")
            raise

    def _is_batch_section(self) -> bool:
        """バッチ処理セクションの開始判定"""
        try:
            token = self._peek()
            if not token:
                return False
                
            # バッチ処理の開始パターン
            patterns = [
                r'^\s*SORT\s+',
                r'^\s*MERGE\s+',
                r'^\s*CHECKPOINT\s+',
                r'^\s*RESTART\s+',
                r'^\s*SELECT\s+.*\s+SORT'
            ]
            
            return any(re.match(pattern, token.value) for pattern in patterns)
            
        except Exception as e:
            logger.error(f"バッチセクション判定でエラー: {str(e)}")
            return False

    def _parse_batch_section(self) -> Optional[ASTNode]:
        """バッチ処理セクションの解析"""
        try:
            section_node = ASTNode(
                type="BATCH_SECTION",
                value=None,
                children=[],
                metadata={'start_line': self._tokens[self._current_pos].line}
            )
            
            while self._peek() and not self._is_section_end():
                statement = self._parse_statement()
                if statement:
                    section_node.children.append(statement)
            
            section_node.metadata['end_line'] = self._tokens[self._current_pos-1].line
            return section_node
            
        except Exception as e:
            logger.error(f"バッチセクション解析でエラー: {str(e)}")
            return None

    def _parse_sort(self, name: str) -> ASTNode:
        """SORT文の解析"""
        try:
            parameters = self._parse_sort_parameters()
            
            return ASTNode(
                type="SORT",
                value=name,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': self._tokens[self._current_pos-1].line,
                    'keys': parameters.get('keys', []),
                    'input_files': parameters.get('input_files', []),
                    'output_files': parameters.get('output_files', [])
                }
            )
        except Exception as e:
            logger.error(f"SORT解析でエラー: {str(e)}")
            raise

    def _parse_sort_parameters(self) -> Dict[str, Any]:
        """SORTパラメータの解析"""
        try:
            parameters = {
                'keys': [],
                'input_files': [],
                'output_files': []
            }
            
            while self._peek() and not self._is_statement_end():
                token = self._consume()
                
                if token.value.upper() == 'ON':
                    # キーの解析
                    key = self._parse_sort_key()
                    if key:
                        parameters['keys'].append(key)
                elif token.value.upper() == 'USING':
                    # 入力ファイルの解析
                    while self._peek() and not self._is_statement_end():
                        file_token = self._consume()
                        if file_token.value != ',':
                            parameters['input_files'].append(file_token.value)
                elif token.value.upper() == 'GIVING':
                    # 出力ファイルの解析
                    while self._peek() and not self._is_statement_end():
                        file_token = self._consume()
                        if file_token.value != ',':
                            parameters['output_files'].append(file_token.value)
            
            return parameters
            
        except Exception as e:
            logger.error(f"SORTパラメータ解析でエラー: {str(e)}")
            return {}

    def _parse_checkpoint(self, name: str) -> ASTNode:
        """CHECKPOINT文の解析"""
        try:
            parameters = self._parse_checkpoint_parameters()
            
            return ASTNode(
                type="CHECKPOINT",
                value=name,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': self._tokens[self._current_pos-1].line,
                    'interval': parameters.get('interval'),
                    'file': parameters.get('file')
                }
            )
        except Exception as e:
            logger.error(f"CHECKPOINT解析でエラー: {str(e)}")
            raise

    def _is_statement_end(self) -> bool:
        """文の終了判定"""
        try:
            token = self._peek()
            if not token:
                return True
            
            return token.value.strip().endswith('.')
            
        except Exception as e:
            logger.error(f"文終了判定でエラー: {str(e)}")
            return True

    def _parse_file_control(self) -> Dict[str, Any]:
        """ファイル管理項の解析"""
        try:
            file_info = {}
            
            while self._peek() and not self._is_section_end():
                token = self._consume()
                
                # SELECT文の解析
                match = self._file_patterns.match(token.value)
                if match:
                    file_name, assign_to = match.groups()
                    file_info[file_name] = {
                        'assign_to': assign_to,
                        'organization': self._parse_file_organization(),
                        'access_mode': self._parse_access_mode()
                    }
            
            return file_info
            
        except Exception as e:
            logger.error(f"ファイル管理項解析でエラー: {str(e)}")
            return {} 