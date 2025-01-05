from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
import re
from .base_parser import Parser, Token, ASTNode
from .dialect_master import DialectMasterManager

logger = logging.getLogger(__name__)

@dataclass
class DialectStatement:
    """メーカー依存文の構造"""
    vendor: str
    type: str
    statement: str
    parameters: Dict[str, Any]
    line_number: int

class DialectParser(Parser):
    """メーカー依存構文解析器"""
    
    def __init__(self):
        super().__init__()
        self._master_manager = DialectMasterManager()
        # メーカー固有のパターン定義
        self._vendor_patterns = {
            'IBM': {
                'patterns': [
                    r'^\s*>>CALLINTERFACE',  # IBM固有インターフェース
                    r'^\s*>>DLLINTERFACE',   # DLLインターフェース
                    r'^\s*EXEC\s+CICS',      # CICS
                    r'^\s*EXEC\s+DLI',       # IMS DLI
                    r'^\s*\*CBL\s+',         # IBMコンパイラ指示子
                    r'^\s*\/\/\*CONTROL'     # JCL制御文
                ],
                'parser': self._parse_ibm_dialect
            },
            'HITACHI': {
                'patterns': [
                    r'^\s*>>XCTL',           # 日立固有制御
                    r'^\s*>>TPS',            # TPSシステム
                    r'^\s*\$\$BLDL',         # BLDLマクロ
                    r'^\s*\$\$LOAD',         # LOADマクロ
                    r'^\s*\*HI-OPT'          # 最適化指示子
                ],
                'parser': self._parse_hitachi_dialect
            },
            'FUJITSU': {
                'patterns': [
                    r'^\s*>>AIM',            # AIM制御
                    r'^\s*>>MCS',            # MCS制御
                    r'^\s*\@\@MGMT',         # 管理制御
                    r'^\s*\*OPT',            # 最適化指示子
                    r'^\s*PROGRAM-STATUS'     # プログラム状態
                ],
                'parser': self._parse_fujitsu_dialect
            },
            'NEC': {
                'patterns': [
                    r'^\s*>>ACOS',           # ACOS制御
                    r'^\s*>>RDB',            # RDB制御
                    r'^\s*\*N90',            # N9000シリーズ指示子
                    r'^\s*DAEMON\s+',        # デーモン制御
                    r'^\s*MCF\s+'            # MCF制御
                ],
                'parser': self._parse_nec_dialect
            },
            'UNISYS': {
                'patterns': [
                    r'^\s*>>DMSII',          # DMS-II制御
                    r'^\s*>>TIP',            # TIP/TC制御
                    r'^\s*\*UNISYS',         # Unisys指示子
                    r'^\s*PROCEDURE\s+DIVISION\s+USING\s+DB',  # DB固有構文
                    r'^\s*ECL\s+'            # ECL制御
                ],
                'parser': self._parse_unisys_dialect
            }
        }

    def parse(self, tokens: List[Token]) -> ASTNode:
        """メーカー依存コードの構文解析"""
        try:
            self._tokens = tokens
            self._current_pos = 0
            
            root = ASTNode(
                type="DIALECT_ROOT",
                value=None,
                children=[],
                metadata={'source_type': 'DIALECT'}
            )
            
            while self._peek():
                vendor = self._detect_vendor()
                if vendor:
                    dialect = self._parse_vendor_dialect(vendor)
                    if dialect:
                        root.children.append(dialect)
                else:
                    self._consume()
            
            return root
            
        except Exception as e:
            logger.error(f"メーカー依存解析でエラー: {str(e)}")
            raise

    def _detect_vendor(self) -> Optional[str]:
        """メーカーの検出"""
        try:
            token = self._peek()
            if not token:
                return None
                
            for vendor, config in self._vendor_patterns.items():
                if any(re.match(pattern, token.value) for pattern in config['patterns']):
                    return vendor
            
            return None
            
        except Exception as e:
            logger.error(f"メーカー検出でエラー: {str(e)}")
            return None

    def _parse_vendor_dialect(self, vendor: str) -> Optional[ASTNode]:
        """メーカー固有構文の解析（マスタ連携版）"""
        try:
            token = self._peek()
            statement = token.value.strip()
            
            # マスタによる構文検証
            if not self._master_manager.validate_statement(vendor, statement):
                logger.warning(f"未定義の{vendor}構文: {statement}")
                return None
            
            # 構文情報の取得
            statement_info = self._master_manager.get_statement_info(vendor, statement)
            
            parser = self._vendor_patterns[vendor]['parser']
            node = parser()
            
            if node:
                # マスタ情報の付加
                node.metadata.update({
                    'statement_info': statement_info,
                    'master_version': self._master_manager.get_master(vendor).version
                })
            
            return node
            
        except Exception as e:
            logger.error(f"メーカー固有構文解析でエラー: {str(e)}")
            return None

    def _parse_ibm_dialect(self) -> ASTNode:
        """IBM固有構文の解析"""
        try:
            token = self._peek()
            statement_type = self._detect_ibm_statement_type(token.value)
            parameters = self._parse_ibm_parameters()
            
            return ASTNode(
                type="IBM_DIALECT",
                value=statement_type,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': token.line,
                    'statement': token.value
                }
            )
            
        except Exception as e:
            logger.error(f"IBM構文解析でエラー: {str(e)}")
            raise

    def _parse_hitachi_dialect(self) -> ASTNode:
        """日立固有構文の解析"""
        try:
            token = self._peek()
            statement_type = self._detect_hitachi_statement_type(token.value)
            parameters = self._parse_hitachi_parameters()
            
            return ASTNode(
                type="HITACHI_DIALECT",
                value=statement_type,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': token.line,
                    'statement': token.value
                }
            )
            
        except Exception as e:
            logger.error(f"日立構文解析でエラー: {str(e)}")
            raise

    def _parse_fujitsu_dialect(self) -> ASTNode:
        """富士通固有構文の解析"""
        try:
            token = self._peek()
            statement_type = self._detect_fujitsu_statement_type(token.value)
            parameters = self._parse_fujitsu_parameters()
            
            return ASTNode(
                type="FUJITSU_DIALECT",
                value=statement_type,
                children=[],
                metadata={
                    'parameters': parameters,
                    'line': token.line,
                    'statement': token.value
                }
            )
            
        except Exception as e:
            logger.error(f"富士通構文解析でエラー: {str(e)}")
            raise

    # 各メーカー固有のパラメータ解析メソッド
    def _parse_ibm_parameters(self) -> Dict[str, Any]:
        """IBMパラメータの解析"""
        parameters = {}
        while self._peek() and not self._is_statement_end():
            token = self._consume()
            if '=' in token.value:
                key, value = token.value.split('=', 1)
                parameters[key.strip()] = value.strip()
        return parameters

    def _parse_hitachi_parameters(self) -> Dict[str, Any]:
        """日立パラメータの解析"""
        parameters = {}
        while self._peek() and not self._is_statement_end():
            token = self._consume()
            if token.value.startswith('$'):
                key = token.value[1:]
                value = self._consume().value if self._peek() else None
                parameters[key] = value
        return parameters

    def _parse_fujitsu_parameters(self) -> Dict[str, Any]:
        """富士通パラメータの解析"""
        parameters = {}
        while self._peek() and not self._is_statement_end():
            token = self._consume()
            if token.value.startswith('@'):
                key = token.value[1:]
                value = self._consume().value if self._peek() else None
                parameters[key] = value
        return parameters

    # メーカー固有の文タイプ検出メソッド
    def _detect_ibm_statement_type(self, statement: str) -> str:
        if 'CICS' in statement:
            return 'CICS'
        elif 'DLI' in statement:
            return 'IMS_DLI'
        elif 'CALLINTERFACE' in statement:
            return 'CALL_INTERFACE'
        return 'OTHER'

    def _detect_hitachi_statement_type(self, statement: str) -> str:
        if 'XCTL' in statement:
            return 'XCTL'
        elif 'TPS' in statement:
            return 'TPS'
        elif 'BLDL' in statement:
            return 'BLDL'
        return 'OTHER'

    def _detect_fujitsu_statement_type(self, statement: str) -> str:
        if 'AIM' in statement:
            return 'AIM'
        elif 'MCS' in statement:
            return 'MCS'
        elif 'MGMT' in statement:
            return 'MANAGEMENT'
        return 'OTHER'

    def _parse_parameters(self, vendor: str) -> Dict[str, Any]:
        """パラメータ解析（マスタ連携版）"""
        try:
            parameters = {}
            
            while self._peek() and not self._is_statement_end():
                token = self._consume()
                param_name = token.value.strip()
                
                # パラメータ情報の取得
                param_info = self._master_manager.get_parameter_info(vendor, param_name)
                
                if param_info:
                    param_type = param_info.get('type', 'string')
                    required = param_info.get('required', False)
                    
                    if '=' in token.value:
                        name, value = token.value.split('=', 1)
                        parameters[name.strip()] = {
                            'value': value.strip(),
                            'type': param_type,
                            'valid': self._validate_parameter(value.strip(), param_info)
                        }
                    elif required:
                        logger.warning(f"必須パラメータ {param_name} の値が未指定です")
                
            return parameters
            
        except Exception as e:
            logger.error(f"パラメータ解析でエラー: {str(e)}")
            return {}

    def _validate_parameter(self, value: str, param_info: Dict[str, Any]) -> bool:
        """パラメータ値の検証"""
        try:
            param_type = param_info.get('type', 'string')
            allowed_values = param_info.get('allowed_values', [])
            
            if allowed_values and value not in allowed_values:
                return False
                
            if param_type == 'number':
                return value.isdigit()
            elif param_type == 'boolean':
                return value.upper() in ['TRUE', 'FALSE', 'YES', 'NO']
                
            return True
            
        except Exception:
            return False 