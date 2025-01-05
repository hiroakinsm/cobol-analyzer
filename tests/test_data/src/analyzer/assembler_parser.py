from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import re
from .base_parser import Parser, Token, ASTNode

logger = logging.getLogger(__name__)

@dataclass
class AssemblerInstruction:
    """アセンブラ命令の構造"""
    label: Optional[str]
    operation: str
    operands: List[str]
    comment: Optional[str]
    line_number: int

class AssemblerParser(Parser):
    """アセンブラ構文解析器"""
    
    def __init__(self):
        super().__init__()
        self._instruction_patterns = {
            'ENTRY': self._parse_entry,
            'USING': self._parse_using,
            'DROP': self._parse_drop,
            'DC': self._parse_dc,
            'DS': self._parse_ds,
            'EQU': self._parse_equ,
            'CSECT': self._parse_csect,
            'DSECT': self._parse_dsect
        }
        self._register_patterns = re.compile(r'R\d{1,2}')

    def parse(self, tokens: List[Token]) -> ASTNode:
        """アセンブラコードの構文解析"""
        try:
            self._tokens = tokens
            self._current_pos = 0
            
            # ルートノードの作成
            root = ASTNode(
                type="ASSEMBLER_ROOT",
                value=None,
                children=[],
                metadata={'source_type': 'ASSEMBLER'}
            )
            
            # アセンブラセクションの検出
            while self._peek():
                if self._is_assembler_section():
                    section = self._parse_assembler_section()
                    if section:
                        root.children.append(section)
                else:
                    self._consume()  # 非アセンブラコードをスキップ
            
            return root
            
        except Exception as e:
            logger.error(f"アセンブラ解析でエラー: {str(e)}")
            raise

    def _is_assembler_section(self) -> bool:
        """アセンブラセクションの開始判定"""
        try:
            token = self._peek()
            if not token:
                return False
                
            # アセンブラセクションの開始パターン
            patterns = [
                r'^\s*\*ASM',  # アセンブラ開始マーカー
                r'^\s*ENTRY\s+',  # ENTRYステートメント
                r'^\s*USING\s+',  # USINGステートメント
                r'^\s*CSECT\s+'   # CSECTステートメント
            ]
            
            return any(re.match(pattern, token.value) for pattern in patterns)
            
        except Exception as e:
            logger.error(f"アセンブラセクション判定でエラー: {str(e)}")
            return False

    def _parse_assembler_section(self) -> Optional[ASTNode]:
        """アセンブラセクションの解析"""
        try:
            section_node = ASTNode(
                type="ASSEMBLER_SECTION",
                value=None,
                children=[],
                metadata={'start_line': self._tokens[self._current_pos].line}
            )
            
            while self._peek() and not self._is_section_end():
                instruction = self._parse_instruction()
                if instruction:
                    section_node.children.append(instruction)
            
            section_node.metadata['end_line'] = self._tokens[self._current_pos-1].line
            return section_node
            
        except Exception as e:
            logger.error(f"アセンブラセクション解析でエラー: {str(e)}")
            return None

    def _parse_instruction(self) -> Optional[ASTNode]:
        """アセンブラ命令の解析"""
        try:
            token = self._peek()
            if not token:
                return None

            # ラベルの解析
            label = None
            if not token.value.isspace() and not token.value.startswith(' '):
                label = self._consume().value

            # 命令の解析
            operation_token = self._consume()
            operation = operation_token.value.strip()

            # 特殊命令の処理
            if operation in self._instruction_patterns:
                return self._instruction_patterns[operation](label)

            # 通常命令の処理
            operands = self._parse_operands()
            comment = self._parse_comment()

            return ASTNode(
                type="INSTRUCTION",
                value=operation,
                children=[],
                metadata={
                    'label': label,
                    'operands': operands,
                    'comment': comment,
                    'line': operation_token.line
                }
            )
            
        except Exception as e:
            logger.error(f"命令解析でエラー: {str(e)}")
            return None

    def _parse_operands(self) -> List[str]:
        """オペランドの解析"""
        try:
            operands = []
            while self._peek() and not self._peek().value.startswith('*'):
                token = self._consume()
                if token.value == ',':
                    continue
                operands.append(token.value.strip())
            return operands
        except Exception as e:
            logger.error(f"オペランド解析でエラー: {str(e)}")
            return []

    def _parse_comment(self) -> Optional[str]:
        """コメントの解析"""
        try:
            if self._peek() and self._peek().value.startswith('*'):
                return self._consume().value[1:].strip()
            return None
        except Exception as e:
            logger.error(f"コメント解析でエラー: {str(e)}")
            return None

    def _is_section_end(self) -> bool:
        """アセンブラセクション終了の判定"""
        try:
            token = self._peek()
            if not token:
                return True
                
            # セクション終了パターン
            patterns = [
                r'^\s*\*END-ASM',  # アセンブラ終了マーカー
                r'^\s*END\s*$',     # ENDステートメント
                r'^\s*IDENTIFICATION\s+DIVISION'  # COBOL部門の開始
            ]
            
            return any(re.match(pattern, token.value) for pattern in patterns)
            
        except Exception as e:
            logger.error(f"セクション終了判定でエラー: {str(e)}")
            return True

    def _parse_entry(self, label: Optional[str]) -> ASTNode:
        """ENTRY命令の解析"""
        try:
            name = self._consume().value
            return ASTNode(
                type="ENTRY",
                value=name,
                children=[],
                metadata={
                    'label': label,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
        except Exception as e:
            logger.error(f"ENTRY解析でエラー: {str(e)}")
            raise

    def _parse_using(self, label: Optional[str]) -> ASTNode:
        """USING命令の解析"""
        try:
            base_register = self._consume().value
            address = self._consume().value
            
            return ASTNode(
                type="USING",
                value=base_register,
                children=[],
                metadata={
                    'label': label,
                    'address': address,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
        except Exception as e:
            logger.error(f"USING解析でエラー: {str(e)}")
            raise 