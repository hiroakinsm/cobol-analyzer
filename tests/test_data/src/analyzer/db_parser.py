from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import re
from .base_parser import Parser, Token, ASTNode

logger = logging.getLogger(__name__)

@dataclass
class DBStatement:
    """データベース操作文の構造"""
    type: str
    operation: str
    table: Optional[str]
    columns: List[str]
    conditions: Optional[str]
    line_number: int

class DBParser(Parser):
    """データベース操作構文解析器"""
    
    def __init__(self):
        super().__init__()
        self._sql_patterns = {
            'SELECT': self._parse_select,
            'INSERT': self._parse_insert,
            'UPDATE': self._parse_update,
            'DELETE': self._parse_delete,
            'DECLARE': self._parse_declare,
            'FETCH': self._parse_fetch,
            'OPEN': self._parse_open,
            'CLOSE': self._parse_close
        }
        self._db_call_pattern = re.compile(r'CALL\s+"?(\w+)"?\s+USING\s+(.*)')
        self._vsam_patterns = {
            'READ': self._parse_vsam_read,
            'WRITE': self._parse_vsam_write,
            'REWRITE': self._parse_vsam_rewrite,
            'DELETE': self._parse_vsam_delete,
            'START': self._parse_vsam_start
        }
        self._isam_patterns = {
            'READ': self._parse_isam_read,
            'WRITE': self._parse_isam_write,
            'REWRITE': self._parse_isam_rewrite,
            'DELETE': self._parse_isam_delete
        }
        self._file_control_pattern = re.compile(
            r'SELECT\s+(\w+)\s+ASSIGN\s+TO\s+(\w+)\s+ORGANIZATION\s+IS\s+(INDEXED|SEQUENTIAL)'
        )

    def parse(self, tokens: List[Token]) -> ASTNode:
        """データベース操作コードの構文解析"""
        try:
            self._tokens = tokens
            self._current_pos = 0
            
            # ルートノードの作成
            root = ASTNode(
                type="DB_ROOT",
                value=None,
                children=[],
                metadata={'source_type': 'DATABASE'}
            )
            
            # DB操作セクションの検出
            while self._peek():
                if self._is_db_section():
                    section = self._parse_db_section()
                    if section:
                        root.children.append(section)
                else:
                    self._consume()
            
            return root
            
        except Exception as e:
            logger.error(f"DB操作解析でエラー: {str(e)}")
            raise

    def _is_db_section(self) -> bool:
        """DB操作セクションの開始判定（VSAM/ISAM含む）"""
        try:
            token = self._peek()
            if not token:
                return False
                
            # 既存のパターンに加えて
            patterns = [
                r'^\s*EXEC\s+SQL',  # 埋め込みSQL
                r'^\s*CALL\s+"?\w+"?\s+USING',  # DBインターフェース呼び出し
                r'^\s*SELECT\s+',  # SQL SELECT
                r'^\s*INSERT\s+',  # SQL INSERT
                r'^\s*UPDATE\s+',  # SQL UPDATE
                r'^\s*DELETE\s+',   # SQL DELETE
                # VSAM操作パターン
                r'^\s*READ\s+(\w+)\s+',
                r'^\s*WRITE\s+(\w+)\s+',
                r'^\s*REWRITE\s+(\w+)\s+',
                r'^\s*DELETE\s+(\w+)\s+',
                r'^\s*START\s+(\w+)\s+',
                # ISAM操作パターン
                r'^\s*ORGANIZATION\s+IS\s+INDEXED',
                r'^\s*ORGANIZATION\s+IS\s+SEQUENTIAL',
                r'^\s*RECORD\s+KEY\s+IS'
            ]
            
            return any(re.match(pattern, token.value) for pattern in patterns)
            
        except Exception as e:
            logger.error(f"DB操作セクション判定でエラー: {str(e)}")
            return False

    def _parse_db_section(self) -> Optional[ASTNode]:
        """DB操作セクションの解析"""
        try:
            token = self._peek()
            if token.value.startswith('EXEC SQL'):
                return self._parse_embedded_sql()
            elif 'CALL' in token.value:
                return self._parse_db_call()
            else:
                return self._parse_sql_statement()
            
        except Exception as e:
            logger.error(f"DB操作セクション解析でエラー: {str(e)}")
            return None

    def _parse_embedded_sql(self) -> ASTNode:
        """埋め込みSQLの解析"""
        try:
            self._consume()  # 'EXEC SQL'を消費
            sql_text = ""
            
            while self._peek() and not self._peek().value.strip().endswith('END-EXEC'):
                token = self._consume()
                sql_text += " " + token.value
            
            self._consume()  # 'END-EXEC'を消費
            
            # SQL文の種類を判定
            sql_type = self._determine_sql_type(sql_text)
            parser = self._sql_patterns.get(sql_type)
            
            if parser:
                return parser(sql_text)
            
            return ASTNode(
                type="EMBEDDED_SQL",
                value=sql_text.strip(),
                children=[],
                metadata={
                    'sql_type': sql_type,
                    'line': self._tokens[self._current_pos-1].line
                }
            )
            
        except Exception as e:
            logger.error(f"埋め込みSQL解析でエラー: {str(e)}")
            raise

    def _parse_select(self, sql_text: str) -> ASTNode:
        """SELECT文の解析"""
        try:
            # SELECT文の構造解析
            match = re.match(
                r'SELECT\s+(.*?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.*))?',
                sql_text,
                re.IGNORECASE | re.DOTALL
            )
            
            if match:
                columns, table, conditions = match.groups()
                columns = [col.strip() for col in columns.split(',')]
                
                return ASTNode(
                    type="SELECT",
                    value=table,
                    children=[],
                    metadata={
                        'columns': columns,
                        'conditions': conditions,
                        'line': self._tokens[self._current_pos-1].line
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"SELECT解析でエラー: {str(e)}")
            raise

    def _parse_db_call(self) -> ASTNode:
        """DBインターフェース呼び出しの解析"""
        try:
            token = self._consume()
            match = self._db_call_pattern.match(token.value)
            
            if match:
                function_name, parameters = match.groups()
                param_list = [p.strip() for p in parameters.split(',')]
                
                return ASTNode(
                    type="DB_CALL",
                    value=function_name,
                    children=[],
                    metadata={
                        'parameters': param_list,
                        'line': token.line
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"DB呼び出し解析でエラー: {str(e)}")
            raise

    def _determine_sql_type(self, sql_text: str) -> str:
        """SQL文の種類を判定"""
        sql_text = sql_text.strip().upper()
        
        if sql_text.startswith('SELECT'):
            return 'SELECT'
        elif sql_text.startswith('INSERT'):
            return 'INSERT'
        elif sql_text.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_text.startswith('DELETE'):
            return 'DELETE'
        elif sql_text.startswith('DECLARE'):
            return 'DECLARE'
        elif sql_text.startswith('FETCH'):
            return 'FETCH'
        elif sql_text.startswith('OPEN'):
            return 'OPEN'
        elif sql_text.startswith('CLOSE'):
            return 'CLOSE'
        else:
            return 'UNKNOWN'

    def _parse_transaction(self) -> Optional[ASTNode]:
        """トランザクション制御の解析"""
        try:
            token = self._peek()
            if not token:
                return None

            if 'COMMIT' in token.value:
                self._consume()
                return ASTNode(
                    type="TRANSACTION",
                    value="COMMIT",
                    children=[],
                    metadata={'line': token.line}
                )
            elif 'ROLLBACK' in token.value:
                self._consume()
                return ASTNode(
                    type="TRANSACTION",
                    value="ROLLBACK",
                    children=[],
                    metadata={'line': token.line}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"トランザクション解析でエラー: {str(e)}")
            return None

    def _parse_vsam_read(self, file_name: str) -> ASTNode:
        """VSAM READ操作の解析"""
        try:
            parameters = self._parse_vsam_parameters()
            
            return ASTNode(
                type="VSAM_READ",
                value=file_name,
                children=[],
                metadata={
                    'parameters': parameters,
                    'key': parameters.get('key'),
                    'into': parameters.get('into'),
                    'line': self._tokens[self._current_pos-1].line,
                    'access_mode': parameters.get('access_mode', 'SEQUENTIAL')
                }
            )
        except Exception as e:
            logger.error(f"VSAM READ解析でエラー: {str(e)}")
            raise

    def _parse_vsam_parameters(self) -> Dict[str, Any]:
        """VSAMパラメータの解析"""
        try:
            parameters = {}
            
            while self._peek() and not self._is_statement_end():
                token = self._consume()
                
                if token.value.upper() == 'KEY':
                    self._consume()  # IS を消費
                    parameters['key'] = self._consume().value
                elif token.value.upper() == 'INTO':
                    parameters['into'] = self._consume().value
                elif token.value.upper() in ['NEXT', 'PREVIOUS', 'FIRST', 'LAST']:
                    parameters['access_mode'] = token.value.upper()
                
            return parameters
            
        except Exception as e:
            logger.error(f"VSAMパラメータ解析でエラー: {str(e)}")
            return {}

    def _parse_file_organization(self) -> Dict[str, Any]:
        """ファイル編成の解析"""
        try:
            organization = {}
            
            while self._peek() and not self._is_section_end():
                token = self._consume()
                
                if 'ORGANIZATION' in token.value.upper():
                    org_type = self._consume().value  # IS を消費
                    org_type = self._consume().value  # INDEXED/SEQUENTIAL を取得
                    organization['type'] = org_type
                    
                    if org_type == 'INDEXED':
                        # キー情報の解析
                        organization['keys'] = self._parse_key_clauses()
                
            return organization
            
        except Exception as e:
            logger.error(f"ファイル編成解析でエラー: {str(e)}")
            return {}

    def _parse_key_clauses(self) -> List[Dict[str, Any]]:
        """キー句の解析"""
        try:
            keys = []
            
            while self._peek() and not self._is_section_end():
                token = self._consume()
                
                if 'RECORD' in token.value.upper() and 'KEY' in self._peek().value.upper():
                    self._consume()  # KEY を消費
                    self._consume()  # IS を消費
                    key_name = self._consume().value
                    keys.append({
                        'type': 'RECORD',
                        'name': key_name
                    })
                elif 'ALTERNATE' in token.value.upper() and 'KEY' in self._peek().value.upper():
                    self._consume()  # KEY を消費
                    self._consume()  # IS を消費
                    key_name = self._consume().value
                    keys.append({
                        'type': 'ALTERNATE',
                        'name': key_name
                    })
            
            return keys
            
        except Exception as e:
            logger.error(f"キー句解析でエラー: {str(e)}")
            return [] 