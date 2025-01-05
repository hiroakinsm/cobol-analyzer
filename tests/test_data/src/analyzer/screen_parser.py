from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import re
from .base_parser import Parser, Token, ASTNode

logger = logging.getLogger(__name__)

@dataclass
class ScreenStatement:
    """画面制御文の構造"""
    type: str
    name: str
    parameters: Dict[str, Any]
    line_number: int

class ScreenParser(Parser):
    """画面制御構文解析器"""
    
    def __init__(self):
        super().__init__()
        self._screen_patterns = {
            'SEND': self._parse_send,
            'RECEIVE': self._parse_receive,
            'HANDLE': self._parse_handle,
            'IGNORE': self._parse_ignore,
            'DISPLAY': self._parse_display,
            'ACCEPT': self._parse_accept
        }
        self._cics_patterns = {
            'EXEC CICS SEND': self._parse_cics_send,
            'EXEC CICS RECEIVE': self._parse_cics_receive,
            'EXEC CICS HANDLE': self._parse_cics_handle,
            'EXEC CICS RETURN': self._parse_cics_return
        }
        self._screen_def_pattern = re.compile(
            r'^\s*SCREEN\s+SECTION|^\s*01\s+.*\s+SCREEN'
        )

    def parse(self, tokens: List[Token]) -> ASTNode:
        """画面制御コードの構文解析"""
        try:
            self._tokens = tokens
            self._current_pos = 0
            
            # ルートノードの作成
            root = ASTNode(
                type="SCREEN_ROOT",
                value=None,
                children=[],
                metadata={'source_type': 'SCREEN'}
            )
            
            # 画面制御セクションの検出
            while self._peek():
                if self._is_screen_section():
                    section = self._parse_screen_section()
                    if section:
                        root.children.append(section)
                else:
                    self._consume()
            
            return root
            
        except Exception as e:
            logger.error(f"画面制御解析でエラー: {str(e)}")
            raise

    def _is_screen_section(self) -> bool:
        """画面制御セクションの開始判定"""
        try:
            token = self._peek()
            if not token:
                return False
                
            patterns = [
                r'^\s*EXEC\s+CICS\s+',  # CICS制御
                r'^\s*SCREEN\s+SECTION',  # 画面セクション
                r'^\s*01\s+.*\s+SCREEN',  # 画面定義
                r'^\s*DISPLAY\s+',        # 画面表示
                r'^\s*ACCEPT\s+',         # 画面入力
                r'^\s*COPY\s+.*DFHAID',   # CICS定義
                r'^\s*COPY\s+.*DFHBMSCA'  # BMS定義
            ]
            
            return any(re.match(pattern, token.value) for pattern in patterns)
            
        except Exception as e:
            logger.error(f"画面セクション判定でエラー: {str(e)}")
            return False

    def _parse_screen_section(self) -> Optional[ASTNode]:
        """画面制御セクションの解析"""
        try:
            token = self._peek()
            
            if token.value.startswith('EXEC CICS'):
                return self._parse_cics_command()
            elif self._screen_def_pattern.match(token.value):
                return self._parse_screen_definition()
            else:
                return self._parse_screen_io()
            
        except Exception as e:
            logger.error(f"画面セクション解析でエラー: {str(e)}")
            return None

    def _parse_cics_command(self) -> ASTNode:
        """CICS命令の解析"""
        try:
            self._consume()  # 'EXEC CICS'を消費
            command = self._consume().value.upper()
            
            if command in self._cics_patterns:
                return self._cics_patterns[command]()
            
            # その他のCICS命令の解析
            parameters = self._parse_cics_parameters()
            
            return ASTNode(
                type="CICS_COMMAND",
                value=command,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
            
        except Exception as e:
            logger.error(f"CICS命令解析でエラー: {str(e)}")
            raise

    def _parse_screen_definition(self) -> ASTNode:
        """画面定義の解析"""
        try:
            screen_node = ASTNode(
                type="SCREEN_DEFINITION",
                value=None,
                children=[],
                metadata={'fields': []}
            )
            
            while self._peek() and not self._is_section_end():
                field = self._parse_screen_field()
                if field:
                    screen_node.metadata['fields'].append(field)
            
            return screen_node
            
        except Exception as e:
            logger.error(f"画面定義解析でエラー: {str(e)}")
            return None

    def _parse_screen_field(self) -> Optional[Dict[str, Any]]:
        """画面フィールドの解析"""
        try:
            token = self._peek()
            if not token:
                return None

            field_info = {
                'level': None,
                'name': None,
                'type': None,
                'position': None,
                'length': None,
                'attributes': []
            }

            # レベル番号の解析
            if token.value.isdigit():
                field_info['level'] = int(self._consume().value)
                
                # フィールド名の解析
                if self._peek():
                    field_info['name'] = self._consume().value

            # 属性の解析
            while self._peek() and not self._is_statement_end():
                attr = self._consume().value.upper()
                if attr in ['PIC', 'PICTURE']:
                    field_info['type'] = self._consume().value
                elif attr in ['LINE', 'COLUMN']:
                    self._consume()  # IS を消費
                    pos = self._consume().value
                    field_info['position'] = field_info.get('position', {})
                    field_info['position'][attr.lower()] = int(pos)
                elif attr in ['HIGHLIGHT', 'LOWLIGHT', 'PROTECTED', 'NUMERIC']:
                    field_info['attributes'].append(attr)

            return field_info
            
        except Exception as e:
            logger.error(f"画面フィールド解析でエラー: {str(e)}")
            return None

    def _parse_cics_parameters(self) -> Dict[str, Any]:
        """CICSパラメータの解析"""
        try:
            parameters = {}
            
            while self._peek() and not self._peek().value.endswith('END-EXEC'):
                token = self._consume()
                
                if token.value == '(':
                    # パラメータ値の解析
                    value = ""
                    while self._peek() and self._peek().value != ')':
                        value += self._consume().value
                    self._consume()  # ')'を消費
                    
                    if value:
                        parameters[token.value] = value
                
            self._consume()  # 'END-EXEC'を消費
            return parameters
            
        except Exception as e:
            logger.error(f"CICSパラメータ解析でエラー: {str(e)}")
            return {} 