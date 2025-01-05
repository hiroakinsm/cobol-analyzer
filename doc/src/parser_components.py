# /home/administrator/cobol-analyzer/src/parser/parser_components.py
# Complete COBOL Parser Components.py
# このコードは以下の主要機能を提供します：
# 1. 完全なCOBOLプログラムの構文解析
# 2. 各DIVISIONおよびSECTIONの詳細なパース
# 3. データ項目の階層構造解析
# 4. 手続き部の制御フロー解析
# 5. エラー処理と詳細なエラーレポート
# 6. 構文規則の検証
# 7. コンテキスト付きのエラー情報
# 8. データ参照の検証
# 9. 手続き参照の検証
# 10. 完全なASTの生成

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
import re
import logging
from abc import ABC, abstractmethod

class COBOLValueType(Enum):
    NUMERIC = "numeric"
    ALPHANUMERIC = "alphanumeric"
    ALPHABETIC = "alphabetic"
    GROUP = "group"
    INDEX = "index"
    POINTER = "pointer"
    PROCEDURE_POINTER = "procedure-pointer"
    FUNCTION_POINTER = "function-pointer"
    OBJECT_REFERENCE = "object-reference"

class UsageType(Enum):
    DISPLAY = "display"
    COMP = "comp"
    COMP_1 = "comp-1"
    COMP_2 = "comp-2"
    COMP_3 = "comp-3"
    COMP_4 = "comp-4"
    COMP_5 = "comp-5"
    POINTER = "pointer"
    FUNCTION_POINTER = "function-pointer"
    PROCEDURE_POINTER = "procedure-pointer"
    OBJECT_REFERENCE = "object-reference"

class SynchronizationType(Enum):
    LEFT = "left"
    RIGHT = "right"

class ParserError(Exception):
    """パーサーエラー"""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"{message} at line {line}, column {column}")

class TokenType(Enum):
    """トークンタイプ"""
    KEYWORD = "keyword"
    IDENTIFIER = "identifier"
    LITERAL = "literal"
    NUMBER = "number"
    PERIOD = "period"
    SEPARATOR = "separator"
    OPERATOR = "operator"
    SPECIAL = "special"

@dataclass
class Token:
    """トークン"""
    type: TokenType
    value: str
    line: int
    column: int
    original_text: str

class COBOLLexer:
    """COBOLレキサー"""
    def __init__(self):
        self.keywords = {
            'IDENTIFICATION', 'DIVISION', 'PROGRAM-ID', 'ENVIRONMENT',
            'DATA', 'PROCEDURE', 'SECTION', 'CONFIGURATION', 'SOURCE-COMPUTER',
            'OBJECT-COMPUTER', 'SPECIAL-NAMES', 'FILE-CONTROL', 'I-O-CONTROL',
            'WORKING-STORAGE', 'LINKAGE', 'FILE', 'FD', 'COPY', 'REPLACE'
        }
        self.line = 1
        self.column = 1
        self.pos = 0
        self.text = ""
        self.logger = logging.getLogger(__name__)

    def tokenize(self, text: str) -> List[Token]:
        """テキストのトークン化"""
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        tokens = []

        while self.pos < len(self.text):
            char = self.text[self.pos]

            if char.isspace():
                self._skip_whitespace()
                continue

            if char == '*' and self.column == 7:
                # コメント行のスキップ
                self._skip_line()
                continue

            if char.isalpha():
                token = self._tokenize_word()
            elif char.isdigit() or char == '-':
                token = self._tokenize_number()
            elif char == '"' or char == "'":
                token = self._tokenize_literal()
            elif char == '.':
                token = Token(TokenType.PERIOD, ".", self.line, self.column, ".")
                self._advance()
            else:
                token = self._tokenize_special()

            tokens.append(token)

        return tokens

    def _skip_whitespace(self):
        """空白のスキップ"""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            if self.text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1

    def _skip_line(self):
        """行のスキップ"""
        while self.pos < len(self.text) and self.text[self.pos] != '\n':
            self.pos += 1
        self.pos += 1
        self.line += 1
        self.column = 1

    def _tokenize_word(self) -> Token:
        """単語のトークン化"""
        start = self.pos
        start_col = self.column
        
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or 
              self.text[self.pos] in '-_'):
            self._advance()

        value = self.text[start:self.pos].upper()
        original = self.text[start:self.pos]
        
        if value in self.keywords:
            return Token(TokenType.KEYWORD, value, self.line, start_col, original)
        return Token(TokenType.IDENTIFIER, value, self.line, start_col, original)

    def _tokenize_number(self) -> Token:
        """数値のトークン化"""
        start = self.pos
        start_col = self.column
        is_negative = False

        if self.text[self.pos] == '-':
            is_negative = True
            self._advance()

        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or 
              self.text[self.pos] == '.'):
            self._advance()

        value = self.text[start:self.pos]
        original = value
        if is_negative:
            value = f"-{value}"

        return Token(TokenType.NUMBER, value, self.line, start_col, original)

    def _tokenize_literal(self) -> Token:
        """リテラルのトークン化"""
        quote = self.text[self.pos]
        start = self.pos
        start_col = self.column
        self._advance()

        while self.pos < len(self.text) and self.text[self.pos] != quote:
            if self.text[self.pos] == '\n':
                raise ParserError("Unterminated string literal", self.line, start_col)
            self._advance()

        if self.pos >= len(self.text):
            raise ParserError("Unterminated string literal", self.line, start_col)

        self._advance()  # closing quote
        value = self.text[start:self.pos]
        return Token(TokenType.LITERAL, value, self.line, start_col, value)

    def _tokenize_special(self) -> Token:
        """特殊文字のトークン化"""
        char = self.text[self.pos]
        start_col = self.column
        self._advance()

        if char in '+-*/=<>':
            return Token(TokenType.OPERATOR, char, self.line, start_col, char)
        elif char in '(),;':
            return Token(TokenType.SEPARATOR, char, self.line, start_col, char)
        else:
            return Token(TokenType.SPECIAL, char, self.line, start_col, char)

    def _advance(self):
        """位置の進行"""
        self.pos += 1
        self.column += 1

class COBOLParser:
    """COBOLパーサー"""
    def __init__(self):
        self.lexer = COBOLLexer()
        self.tokens: List[Token] = []
        self.current = 0
        self.logger = logging.getLogger(__name__)

    def parse(self, source_code: str) -> Dict[str, Any]:
        """ソースコードのパース"""
        try:
            self.tokens = self.lexer.tokenize(source_code)
            self.current = 0
            
            program = self._parse_program()
            
            # ASTの検証
            self._validate_ast(program)
            
            return program
            
        except ParserError as e:
            self.logger.error(f"Parsing error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during parsing: {str(e)}")
            raise

    def _parse_program(self) -> Dict[str, Any]:
        """プログラム全体のパース"""
        identification_division = self._parse_identification_division()
        environment_division = self._parse_environment_division()
        data_division = self._parse_data_division()
        procedure_division = self._parse_procedure_division()

        return {
            "type": "program",
            "identification": identification_division,
            "environment": environment_division,
            "data": data_division,
            "procedure": procedure_division
        }

    def _parse_identification_division(self) -> Dict[str, Any]:
        """IDENTIFICATION DIVISIONのパース"""
        self._expect(TokenType.KEYWORD, "IDENTIFICATION")
        self._expect(TokenType.KEYWORD, "DIVISION")
        self._expect(TokenType.PERIOD, ".")

        properties = {}
        while self._peek().type == TokenType.KEYWORD:
            keyword = self._advance()
            if keyword.value == "PROGRAM-ID":
                self._expect(TokenType.PERIOD, ".")
                name_token = self._expect(TokenType.IDENTIFIER)
                properties["program_id"] = name_token.value
            elif keyword.value in ["AUTHOR", "INSTALLATION", "DATE-WRITTEN", "DATE-COMPILED"]:
                self._expect(TokenType.PERIOD, ".")
                value_token = self._advance()
                properties[keyword.value.lower().replace("-", "_")] = value_token.value
            else:
                break

        return {
            "type": "identification_division",
            "properties": properties
        }

    def _parse_environment_division(self) -> Dict[str, Any]:
        """ENVIRONMENT DIVISIONのパース"""
        if not self._match(TokenType.KEYWORD, "ENVIRONMENT"):
            return None

        self._expect(TokenType.KEYWORD, "DIVISION")
        self._expect(TokenType.PERIOD, ".")

        configuration_section = self._parse_configuration_section()
        input_output_section = self._parse_input_output_section()

        return {
            "type": "environment_division",
            "configuration": configuration_section,
            "input_output": input_output_section
        }

    def _parse_configuration_section(self) -> Dict[str, Any]:
        """CONFIGURATION SECTIONのパース"""
        if not self._match(TokenType.KEYWORD, "CONFIGURATION"):
            return None

        self._expect(TokenType.KEYWORD, "SECTION")
        self._expect(TokenType.PERIOD, ".")

        source_computer = self._parse_source_computer()
        object_computer = self._parse_object_computer()
        special_names = self._parse_special_names()

        return {
            "type": "configuration_section",
            "source_computer": source_computer,
            "object_computer": object_computer,
            "special_names": special_names
        }

    def _parse_source_computer(self) -> Dict[str, Any]:
        """SOURCE-COMPUTERのパース"""
        if not self._match(TokenType.KEYWORD, "SOURCE-COMPUTER"):
            return None

        self._expect(TokenType.PERIOD, ".")
        name_token = self._expect(TokenType.IDENTIFIER)
        debug_mode = False

        if self._match(TokenType.KEYWORD, "WITH"):
            self._expect(TokenType.KEYWORD, "DEBUGGING")
            self._expect(TokenType.KEYWORD, "MODE")
            debug_mode = True

        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "source_computer",
            "name": name_token.value,
            "debug_mode": debug_mode
        }

    def _parse_object_computer(self) -> Dict[str, Any]:
        """OBJECT-COMPUTERのパース"""
        if not self._match(TokenType.KEYWORD, "OBJECT-COMPUTER"):
            return None

        self._expect(TokenType.PERIOD, ".")
        name_token = self._expect(TokenType.IDENTIFIER)
        properties = {
            "name": name_token.value,
            "memory_size": None,
            "segment_limit": None
        }

        while self._peek().type == TokenType.KEYWORD:
            keyword = self._advance()
            if keyword.value == "MEMORY":
                self._expect(TokenType.KEYWORD, "SIZE")
                size_token = self._expect(TokenType.NUMBER)
                properties["memory_size"] = int(size_token.value)
            elif keyword.value == "SEGMENT-LIMIT":
                self._expect(TokenType.KEYWORD, "IS")
                limit_token = self._expect(TokenType.NUMBER)
                properties["segment_limit"] = int(limit_token.value)
            else:
                break

        self._expect(TokenType.PERIOD, ".")
        return {
            "type": "object_computer",
            **properties
        }

    def _parse_special_names(self) -> Dict[str, Any]:
        """SPECIAL-NAMESのパース"""
        if not self._match(TokenType.KEYWORD, "SPECIAL-NAMES"):
            return None

        self._expect(TokenType.PERIOD, ".")
        special_names = {
            "currency_sign": None,
            "decimal_point": None,
            "symbolic_characters": {},
            "class_definitions": {}
        }

        while self._peek().type == TokenType.KEYWORD:
            keyword = self._advance()
            if keyword.value == "CURRENCY":
                self._expect(TokenType.KEYWORD, "SIGN")
                self._expect(TokenType.KEYWORD, "IS")
                sign_token = self._expect(TokenType.LITERAL)
                special_names["currency_sign"] = sign_token.value.strip("'\"")
            elif keyword.value == "DECIMAL-POINT":
                self._expect(TokenType.KEYWORD, "IS")
                self._expect(TokenType.KEYWORD, "COMMA")
                special_names["decimal_point"] = "COMMA"
            else:
                break

        self._expect(TokenType.PERIOD, ".")
        return {
            "type": "special_names",
            **special_names
        }

    def _parse_data_division(self) -> Dict[str, Any]:
        """DATA DIVISIONのパース"""
        if not self._match(TokenType.KEYWORD, "DATA"):
            return None

        self._expect(TokenType.KEYWORD, "DIVISION")
        self._expect(TokenType.PERIOD, ".")

        file_section = self._parse_file_section()
        working_storage = self._parse_working_storage()
        linkage_section = self._parse_linkage_section()
        communication_section = self._parse_communication_section()

        return {
            "type": "data_division",
            "file_section": file_section,
            "working

    def _parse_working_storage(self) -> Dict[str, Any]:
        """WORKING-STORAGE SECTIONのパース"""
        if not self._match(TokenType.KEYWORD, "WORKING-STORAGE"):
            return None

        self._expect(TokenType.KEYWORD, "SECTION")
        self._expect(TokenType.PERIOD, ".")

        data_items = []
        while self._peek().type in [TokenType.NUMBER, TokenType.IDENTIFIER]:
            data_item = self._parse_data_item()
            data_items.append(data_item)

        return {
            "type": "working_storage_section",
            "data_items": data_items
        }

    def _parse_data_item(self) -> Dict[str, Any]:
        """データ項目のパース"""
        level_token = self._advance()
        name_token = self._expect(TokenType.IDENTIFIER)

        properties = {
            "level": int(level_token.value),
            "name": name_token.value,
            "picture": None,
            "usage": None,
            "value": None,
            "occurs": None,
            "occurs_depending_on": None,
            "indexed_by": [],
            "redefines": None
        }

        while self._peek().type == TokenType.KEYWORD:
            keyword = self._advance()
            
            if keyword.value == "PIC" or keyword.value == "PICTURE":
                picture_token = self._expect(TokenType.IDENTIFIER)
                properties["picture"] = picture_token.value
            
            elif keyword.value == "USAGE":
                self._expect(TokenType.KEYWORD, "IS")
                usage_token = self._expect(TokenType.IDENTIFIER)
                properties["usage"] = usage_token.value
            
            elif keyword.value == "VALUE":
                self._expect(TokenType.KEYWORD, "IS")
                value_token = self._advance()  # NUMBER or LITERAL
                properties["value"] = value_token.value
            
            elif keyword.value == "OCCURS":
                occurs_token = self._expect(TokenType.NUMBER)
                properties["occurs"] = int(occurs_token.value)
                
                if self._match(TokenType.KEYWORD, "DEPENDING"):
                    self._expect(TokenType.KEYWORD, "ON")
                    depending_token = self._expect(TokenType.IDENTIFIER)
                    properties["occurs_depending_on"] = depending_token.value
                
                if self._match(TokenType.KEYWORD, "INDEXED"):
                    self._expect(TokenType.KEYWORD, "BY")
                    while self._peek().type == TokenType.IDENTIFIER:
                        index_token = self._advance()
                        properties["indexed_by"].append(index_token.value)
            
            elif keyword.value == "REDEFINES":
                redefines_token = self._expect(TokenType.IDENTIFIER)
                properties["redefines"] = redefines_token.value

        self._expect(TokenType.PERIOD, ".")
        return {
            "type": "data_item",
            **properties
        }

    def _parse_procedure_division(self) -> Dict[str, Any]:
        """PROCEDURE DIVISIONのパース"""
        if not self._match(TokenType.KEYWORD, "PROCEDURE"):
            return None

        self._expect(TokenType.KEYWORD, "DIVISION")
        
        # USING パラメータの処理
        using_params = []
        if self._match(TokenType.KEYWORD, "USING"):
            while self._peek().type == TokenType.IDENTIFIER:
                param_token = self._advance()
                using_params.append(param_token.value)
        
        self._expect(TokenType.PERIOD, ".")

        # セクションとパラグラフのパース
        sections = []
        while self._peek().type != TokenType.KEYWORD or self._peek().value != "END":
            if self._peek().type == TokenType.IDENTIFIER:
                section = self._parse_section()
                sections.append(section)
            else:
                self._advance()  # 不明なトークンをスキップ

        return {
            "type": "procedure_division",
            "using_parameters": using_params,
            "sections": sections
        }

    def _parse_section(self) -> Dict[str, Any]:
        """セクションのパース"""
        name_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.KEYWORD, "SECTION")
        self._expect(TokenType.PERIOD, ".")

        paragraphs = []
        while self._peek().type == TokenType.IDENTIFIER:
            paragraph = self._parse_paragraph()
            paragraphs.append(paragraph)

        return {
            "type": "section",
            "name": name_token.value,
            "paragraphs": paragraphs
        }

    def _parse_paragraph(self) -> Dict[str, Any]:
        """パラグラフのパース"""
        name_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.PERIOD, ".")

        statements = []
        while self._peek().type != TokenType.IDENTIFIER:
            if self._peek().type == TokenType.KEYWORD and self._peek().value == "END":
                break
            statement = self._parse_statement()
            if statement:
                statements.append(statement)

        return {
            "type": "paragraph",
            "name": name_token.value,
            "statements": statements
        }

    def _parse_statement(self) -> Optional[Dict[str, Any]]:
        """文のパース"""
        if self._peek().type != TokenType.KEYWORD:
            self._advance()  # 不明なトークンをスキップ
            return None

        keyword = self._advance()
        
        if keyword.value == "IF":
            return self._parse_if_statement()
        elif keyword.value == "MOVE":
            return self._parse_move_statement()
        elif keyword.value == "PERFORM":
            return self._parse_perform_statement()
        elif keyword.value == "COMPUTE":
            return self._parse_compute_statement()
        elif keyword.value == "CALL":
            return self._parse_call_statement()
        else:
            return self._parse_generic_statement(keyword.value)

    def _parse_if_statement(self) -> Dict[str, Any]:
        """IF文のパース"""
        condition = self._parse_condition()
        
        # THEN句の処理
        then_statements = []
        while self._peek().type != TokenType.KEYWORD or (
              self._peek().value != "ELSE" and 
              self._peek().value != "END-IF"):
            statement = self._parse_statement()
            if statement:
                then_statements.append(statement)

        # ELSE句の処理
        else_statements = []
        if self._match(TokenType.KEYWORD, "ELSE"):
            while self._peek().type != TokenType.KEYWORD or self._peek().value != "END-IF":
                statement = self._parse_statement()
                if statement:
                    else_statements.append(statement)

        self._expect(TokenType.KEYWORD, "END-IF")
        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "if_statement",
            "condition": condition,
            "then_statements": then_statements,
            "else_statements": else_statements
        }

    def _parse_condition(self) -> Dict[str, Any]:
        """条件式のパース"""
        left = self._advance()  # 左辺
        operator = self._advance()  # 演算子
        right = self._advance()  # 右辺

        condition = {
            "type": "condition",
            "left": left.value,
            "operator": operator.value,
            "right": right.value
        }

        # AND/OR条件の処理
        while self._peek().type == TokenType.KEYWORD and self._peek().value in ["AND", "OR"]:
            logical_op = self._advance()
            next_condition = self._parse_condition()
            condition = {
                "type": "logical_condition",
                "operator": logical_op.value,
                "left": condition,
                "right": next_condition
            }

        return condition

    def _parse_move_statement(self) -> Dict[str, Any]:
        """MOVE文のパース"""
        source = self._advance()  # 移動元
        self._expect(TokenType.KEYWORD, "TO")
        
        targets = []
        while self._peek().type != TokenType.PERIOD:
            target = self._advance()
            targets.append(target.value)

        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "move_statement",
            "source": source.value,
            "targets": targets
        }

    def _parse_perform_statement(self) -> Dict[str, Any]:
        """PERFORM文のパース"""
        target = self._advance()
        
        times = None
        until_condition = None
        
        if self._peek().type == TokenType.NUMBER:
            times_token = self._advance()
            self._expect(TokenType.KEYWORD, "TIMES")
            times = int(times_token.value)
        elif self._match(TokenType.KEYWORD, "UNTIL"):
            until_condition = self._parse_condition()

        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "perform_statement",
            "target": target.value,
            "times": times,
            "until_condition": until_condition
        }

    def _parse_compute_statement(self) -> Dict[str, Any]:
        """COMPUTE文のパース"""
        target = self._advance()
        self._expect(TokenType.OPERATOR, "=")
        
        # 式の解析
        expression = []
        while self._peek().type != TokenType.PERIOD:
            token = self._advance()
            expression.append({
                "type": token.type.value,
                "value": token.value
            })

        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "compute_statement",
            "target": target.value,
            "expression": expression
        }

    def _parse_call_statement(self) -> Dict[str, Any]:
        """CALL文のパース"""
        program = self._advance()
        
        parameters = []
        if self._match(TokenType.KEYWORD, "USING"):
            while self._peek().type != TokenType.PERIOD:
                param = self._advance()
                parameters.append(param.value)

        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "call_statement",
            "program": program.value,
            "parameters": parameters
        }

    def _parse_generic_statement(self, statement_type: str) -> Dict[str, Any]:
        """一般的な文のパース"""
        operands = []
        while self._peek().type != TokenType.PERIOD:
            operand = self._advance()
            operands.append(operand.value)

        self._expect(TokenType.PERIOD, ".")

        return {
            "type": "generic_statement",
            "statement_type": statement_type,
            "operands": operands
        }

    def _expect(self, token_type: TokenType, value: Optional[str] = None) -> Token:
        """期待されるトークンの検証"""
        token = self._advance()
        
        if token.type != token_type:
            raise ParserError(
                f"Expected token type {token_type}, got {token.type}",
                token.line,
                token.column
            )
            
        if value is not None and token.value != value:
            raise ParserError(
                f"Expected token value {value}, got {token.value}",
                token.line,
                token.column
            )
            
        return token

    def _match(self, token_type: TokenType, value: str) -> bool:
        """トークンのマッチング"""
        if self._peek().type == token_type and self._peek().value == value:
            self._advance()
            return True
        return False

    def _peek(self) -> Token:
        """次のトークンの確認"""
        if self.current >= len(self.tokens):
            return Token(TokenType.SPECIAL, "EOF", -1, -1, "EOF")
        return self.tokens[self.current]

    def _advance(self) -> Token:
        """次のトークンへの移動"""
        token = self._peek()
        self.current += 1
        return token

    def _validate_ast(self, ast: Dict[str, Any]) -> None:
        """ASTの検証"""
        if not ast.get("identification"):
            raise ParserError("Missing IDENTIFICATION DIVISION", 0, 0)
        
        if not ast.get("procedure"):
            raise ParserError("Missing PROCEDURE DIVISION", 0, 0)
            
        self._validate_data_references(ast)
        self._validate_procedure_references(ast)

    def _validate_data_references(self, ast: Dict[str, Any]) -> None:
        """データ参照の検証"""
        data_items = set()
        
        # データ項目の収集
        if "data" in ast and "working_storage" in ast["data"]:
            for item in ast["data"]["working_storage"].get("data_items", []):
                data_items.add(item["name"])

        # データ参照の検証
        if "procedure" in ast:
            for section in ast["procedure"].get("sections", []):
                for paragraph in section.get("paragraphs", []):
                    for statement in paragraph.get("statements", []):
                        self._validate_statement_references(statement, data_items)

    def _validate_statement_references(self, 
                                    statement: Dict[str, Any], 
                                    data_items: Set[str]) -> None:
        """文中の参照の検証"""
        if statement["type"] == "move_statement":
            if statement["source"] not in data_items:
                self.logger.warning(f"Undefined data item: {statement['source']}")
            for target in statement["targets"]:
                if target not in data_items:
                    self.logger.warning(f"Undefined data item: {target}")

        elif statement["type"] == "compute_statement":
            if statement["target"] not in data_items:
                self.logger.warning(f"Undefined data item: {statement['target']}")

    def _validate_procedure_references(self, ast: Dict[str, Any]) -> None:
        """手続き参照の検証"""
        procedures = set()
        
        # 手続き名の収集
        if "procedure" in ast:
            for section in ast["procedure"].get("sections", []):
                procedures.add(section["name"])
                for paragraph in section.get("paragraphs", []):
                    procedures.add(paragraph["name"])

        # PERFORM文の参照を検証
        if "procedure" in ast:
            for section in ast["procedure"].get("sections", []):
                for paragraph in section.get("paragraphs", []):
                    for statement in paragraph.get("statements", []):
                        if statement["type"] == "perform_statement":
                            if statement["target"] not in procedures:
                                self.logger.warning(
                                    f"Undefined procedure: {statement['target']}"
                                )

    def _parse_file_section(self) -> Dict[str, Any]:
        """FILE SECTIONのパース"""
        if not self._match(TokenType.KEYWORD, "FILE"):
            return None

        self._expect(TokenType.KEYWORD, "SECTION")
        self._expect(TokenType.PERIOD, ".")

        file_descriptions = []
        while self._peek().type == TokenType.KEYWORD and self._peek().value == "FD":
            fd = self._parse_file_description()
            file_descriptions.append(fd)

        return {
            "type": "file_section",
            "file_descriptions": file_descriptions
        }

    def _parse_file_description(self) -> Dict[str, Any]:
        """ファイル記述のパース"""
        self._expect(TokenType.KEYWORD, "FD")
        name_token = self._expect(TokenType.IDENTIFIER)
        
        properties = {
            "name": name_token.value,
            "record_description": [],
            "block_contains": None,
            "record_contains": None,
            "label_records": None,
            "value_of": {},
            "data_records": []
        }

        while self._peek().type == TokenType.KEYWORD:
            keyword = self._advance()
            
            if keyword.value == "BLOCK":
                self._expect(TokenType.KEYWORD, "CONTAINS")
                size_token = self._expect(TokenType.NUMBER)
                properties["block_contains"] = int(size_token.value)
            
            elif keyword.value == "RECORD":
                if self._match(TokenType.KEYWORD, "CONTAINS"):
                    size_token = self._expect(TokenType.NUMBER)
                    properties["record_contains"] = int(size_token.value)
            
            elif keyword.value == "LABEL":
                self._expect(TokenType.KEYWORD, "RECORDS")
                self._expect(TokenType.KEYWORD, "ARE")
                label_token = self._expect(TokenType.IDENTIFIER)
                properties["label_records"] = label_token.value
            
            elif keyword.value == "VALUE":
                self._expect(TokenType.KEYWORD, "OF")
                name_token = self._expect(TokenType.IDENTIFIER)
                self._expect(TokenType.KEYWORD, "IS")
                value_token = self._expect(TokenType.IDENTIFIER)
                properties["value_of"][name_token.value] = value_token.value
            
            elif keyword.value == "DATA":
                self._expect(TokenType.KEYWORD, "RECORDS")
                self._expect(TokenType.KEYWORD, "ARE")
                while self._peek().type == TokenType.IDENTIFIER:
                    record_token = self._advance()
                    properties["data_records"].append(record_token.value)

        # レコード記述の解析
        while self._peek().type in [TokenType.NUMBER, TokenType.IDENTIFIER]:
            record = self._parse_data_item()
            properties["record_description"].append(record)

        return {
            "type": "file_description",
            **properties
        }

    def _parse_linkage_section(self) -> Dict[str, Any]:
        """LINKAGE SECTIONのパース"""
        if not self._match(TokenType.KEYWORD, "LINKAGE"):
            return None

        self._expect(TokenType.KEYWORD, "SECTION")
        self._expect(TokenType.PERIOD, ".")

        data_items = []
        while self._peek().type in [TokenType.NUMBER, TokenType.IDENTIFIER]:
            data_item = self._parse_data_item()
            data_items.append(data_item)

        return {
            "type": "linkage_section",
            "data_items": data_items
        }

    def _parse_communication_section(self) -> Dict[str, Any]:
        """COMMUNICATION SECTIONのパース"""
        if not self._match(TokenType.KEYWORD, "COMMUNICATION"):
            return None

        self._expect(TokenType.KEYWORD, "SECTION")
        self._expect(TokenType.PERIOD, ".")

        entries = []
        while self._peek().type == TokenType.KEYWORD and (
              self._peek().value in ["CD", "COMMUNICATION"]):
            entry = self._parse_communication_entry()
            entries.append(entry)

        return {
            "type": "communication_section",
            "entries": entries
        }

    def _parse_communication_entry(self) -> Dict[str, Any]:
        """通信記述項目のパース"""
        self._expect(TokenType.KEYWORD, "CD")
        name_token = self._expect(TokenType.IDENTIFIER)
        
        properties = {
            "name": name_token.value,
            "description": [],
            "options": {}
        }

        while self._peek().type == TokenType.KEYWORD:
            keyword = self._advance()
            
            if keyword.value == "FOR":
                mode_token = self._expect(TokenType.IDENTIFIER)
                properties["mode"] = mode_token.value
            
            elif keyword.value in ["INITIAL", "TERMINAL", "ERROR", "END"]:
                properties["options"][keyword.value] = True

        # 記述項目の解析
        while self._peek().type in [TokenType.NUMBER, TokenType.IDENTIFIER]:
            item = self._parse_data_item()
            properties["description"].append(item)

        return {
            "type": "communication_entry",
            **properties
        }

    def _validate_syntax_rules(self, ast: Dict[str, Any]) -> None:
        """構文規則の検証"""
        self._validate_division_order(ast)
        self._validate_section_order(ast)
        self._validate_data_hierarchies(ast)
        self._validate_procedure_structure(ast)

    def _validate_division_order(self, ast: Dict[str, Any]) -> None:
        """DIVISION順序の検証"""
        division_order = [
            "identification",
            "environment",
            "data",
            "procedure"
        ]
        
        current_divisions = list(filter(None, [
            ast.get(div) for div in division_order
        ]))
        
        if len(current_divisions) < 2:  # 最低でもIDENTIFICATIONとPROCEDUREが必要
            raise ParserError(
                "Program must contain at least IDENTIFICATION and PROCEDURE DIVISIONS",
                0, 0
            )

    def _validate_section_order(self, ast: Dict[str, Any]) -> None:
        """SECTION順序の検証"""
        if "data" in ast:
            data_div = ast["data"]
            section_order = ["file_section", "working_storage", "linkage_section"]
            current_sections = []
            
            for section in section_order:
                if section in data_div and data_div[section]:
                    current_sections.append(section)
            
            # セクション順序の検証
            for i in range(len(current_sections) - 1):
                curr_idx = section_order.index(current_sections[i])
                next_idx = section_order.index(current_sections[i + 1])
                if curr_idx > next_idx:
                    self.logger.warning(
                        f"Invalid section order: {current_sections[i]} appears before {current_sections[i + 1]}"
                    )

    def _validate_data_hierarchies(self, ast: Dict[str, Any]) -> None:
        """データ階層構造の検証"""
        if "data" in ast and "working_storage" in ast["data"]:
            items = ast["data"]["working_storage"].get("data_items", [])
            stack = []
            
            for item in items:
                level = item["level"]
                
                while stack and stack[-1]["level"] >= level:
                    stack.pop()
                
                if level != 1 and not stack:
                    self.logger.warning(
                        f"Invalid level number {level} for item {item['name']}"
                    )
                
                stack.append(item)

    def _validate_procedure_structure(self, ast: Dict[str, Any]) -> None:
        """手続き部構造の検証"""
        if "procedure" in ast:
            proc_div = ast["procedure"]
            
            # セクションとパラグラフの構造を検証
            sections = proc_div.get("sections", [])
            for section in sections:
                paragraphs = section.get("paragraphs", [])
                if not paragraphs:
                    self.logger.warning(
                        f"Empty section: {section['name']}"
                    )
                
                # パラグラフ内の文を検証
                for paragraph in paragraphs:
                    statements = paragraph.get("statements", [])
                    if not statements:
                        self.logger.warning(
                            f"Empty paragraph: {paragraph['name']}"
                        )

    def _handle_error(self, error: ParserError) -> None:
        """エラー処理"""
        self.logger.error(
            f"Parser error at line {error.line}, column {error.column}: {error.message}"
        )
        # エラー情報の詳細を収集
        error_context = self._get_error_context(error.line)
        self.logger.error(f"Context:\n{error_context}")

    def _get_error_context(self, line: int, context_lines: int = 3) -> str:
        """エラー周辺のコンテキスト取得"""
        if not hasattr(self, 'source_lines'):
            return "Context not available"
        
        start = max(0, line - context_lines)
        end = min(len(self.source_lines), line + context_lines + 1)
        
        context = []
        for i in range(start, end):
            prefix = "-> " if i == line else "   "
            context.append(f"{prefix}{i+1}: {self.source_lines[i]}")
        
        return "\n".join(context)
