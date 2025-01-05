from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import re
from .base_parser import Parser, Token, ASTNode

logger = logging.getLogger(__name__)

@dataclass
class JCLStatement:
    """JCL文の構造"""
    type: str
    name: str
    parameters: Dict[str, str]
    line_number: int

class JCLParser(Parser):
    """JCL構文解析器"""
    
    def __init__(self):
        super().__init__()
        self._statement_types = {
            'JOB': self._parse_job_statement,
            'EXEC': self._parse_exec_statement,
            'DD': self._parse_dd_statement,
            'PROC': self._parse_proc_statement,
            'SET': self._parse_set_statement,
            'IF': self._parse_if_statement,
            'INCLUDE': self._parse_include_statement
        }

    def parse(self, tokens: List[Token]) -> ASTNode:
        """JCLの構文解析"""
        try:
            self._tokens = tokens
            self._current_pos = 0
            
            # ルートノードの作成
            root = ASTNode(
                type="JCL_ROOT",
                value=None,
                children=[],
                metadata={'source_type': 'JCL'}
            )
            
            while self._peek():
                statement = self._parse_statement()
                if statement:
                    root.children.append(statement)
            
            return root
            
        except Exception as e:
            logger.error(f"JCL解析でエラー: {str(e)}")
            raise

    def _parse_statement(self) -> Optional[ASTNode]:
        """JCL文の解析"""
        try:
            token = self._peek()
            if not token:
                return None

            # JCL文の開始を確認
            if token.value.startswith('//'):
                self._consume()  # '//'を消費
                name_token = self._consume()
                
                if not name_token:
                    return None
                
                # 文タイプの判定
                type_token = self._peek()
                if type_token and type_token.value in self._statement_types:
                    self._consume()  # タイプトークンを消費
                    parser = self._statement_types[type_token.value]
                    return parser(name_token.value)
                
                # 継続行の処理
                return self._parse_continuation(name_token.value)
            
            # コメント行の処理
            if token.value.startswith('//*'):
                return self._parse_comment()
            
            # その他の行はスキップ
            self._consume()
            return None
            
        except Exception as e:
            logger.error(f"JCL文解析でエラー: {str(e)}")
            return None

    def _parse_job_statement(self, name: str) -> ASTNode:
        """JOB文の解析"""
        try:
            parameters = self._parse_parameters()
            
            return ASTNode(
                type="JOB",
                value=name,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
        except Exception as e:
            logger.error(f"JOB文解析でエラー: {str(e)}")
            raise

    def _parse_exec_statement(self, name: str) -> ASTNode:
        """EXEC文の解析"""
        try:
            parameters = self._parse_parameters()
            
            # プログラム名またはプロシージャ名の抽出
            program = parameters.get('PGM') or parameters.get('PROC')
            
            return ASTNode(
                type="EXEC",
                value=program,
                children=[],
                metadata={
                    'name': name,
                    'parameters': parameters,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
        except Exception as e:
            logger.error(f"EXEC文解析でエラー: {str(e)}")
            raise

    def _parse_dd_statement(self, name: str) -> ASTNode:
        """DD文の解析"""
        try:
            parameters = self._parse_parameters()
            
            return ASTNode(
                type="DD",
                value=name,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': self._tokens[self._current_pos-1].line,
                    'dataset': parameters.get('DSN') or parameters.get('DSNAME')
                }
            )
        except Exception as e:
            logger.error(f"DD文解析でエラー: {str(e)}")
            raise

    def _parse_parameters(self) -> Dict[str, str]:
        """パラメータの解析"""
        try:
            parameters = {}
            
            while self._peek() and not self._peek().value.startswith('//'):
                token = self._consume()
                
                # パラメータの形式: KEY=VALUE
                match = re.match(r'(\w+)=(.+)', token.value)
                if match:
                    key, value = match.groups()
                    parameters[key] = value
                
                # 継続行の処理
                if self._peek() and self._peek().value == ',':
                    self._consume()  # カンマを消費
                    continue
                    
            return parameters
            
        except Exception as e:
            logger.error(f"パラメータ解析でエラー: {str(e)}")
            return {}

    def _parse_continuation(self, name: str) -> Optional[ASTNode]:
        """継続行の解析"""
        try:
            value = ""
            while self._peek() and not self._peek().value.startswith('//'):
                token = self._consume()
                value += token.value
            
            return ASTNode(
                type="CONTINUATION",
                value=value.strip(),
                children=[],
                metadata={
                    'name': name,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
        except Exception as e:
            logger.error(f"継続行解析でエラー: {str(e)}")
            return None

    def _parse_comment(self) -> ASTNode:
        """コメントの解析"""
        try:
            token = self._consume()
            return ASTNode(
                type="COMMENT",
                value=token.value[3:].strip(),  # '//*'を除去
                children=[],
                metadata={
                    'line': token.line
                }
            )
        except Exception as e:
            logger.error(f"コメント解析でエラー: {str(e)}")
            return None 