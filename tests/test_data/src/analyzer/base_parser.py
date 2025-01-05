from typing import Dict, Any, List, Optional
import logging
from dataclasses import dataclass
from abc import ABC, abstractmethod
import re

logger = logging.getLogger(__name__)

@dataclass
class Token:
    """トークン情報"""
    type: str
    value: str
    line: int
    column: int

@dataclass
class ASTNode:
    """AST(抽象構文木)ノード"""
    type: str
    value: Any
    children: List['ASTNode'] = None
    metadata: Dict[str, Any] = None

class LexicalAnalyzer:
    """字句解析器"""
    
    def __init__(self):
        self._rules: Dict[str, str] = {}
        self._skip_patterns: List[str] = []
        self._current_line = 1
        self._current_column = 1

    def add_rule(self, token_type: str, pattern: str):
        """トークン規則の追加"""
        self._rules[token_type] = pattern

    def add_skip_pattern(self, pattern: str):
        """スキップするパターンの追加"""
        self._skip_patterns.append(pattern)

    def tokenize(self, source: str) -> List[Token]:
        """ソースコードのトークン化"""
        try:
            tokens = []
            position = 0
            
            while position < len(source):
                match = None
                
                # スキップパターンのチェック
                for pattern in self._skip_patterns:
                    regex = re.compile(pattern)
                    match = regex.match(source, position)
                    if match:
                        skipped = match.group(0)
                        position += len(skipped)
                        self._update_position(skipped)
                        break
                
                if match:
                    continue
                
                # トークンのマッチング
                for token_type, pattern in self._rules.items():
                    regex = re.compile(pattern)
                    match = regex.match(source, position)
                    if match:
                        value = match.group(0)
                        token = Token(
                            type=token_type,
                            value=value,
                            line=self._current_line,
                            column=self._current_column
                        )
                        tokens.append(token)
                        position += len(value)
                        self._update_position(value)
                        break
                
                if not match:
                    raise SyntaxError(
                        f"不正な文字: {source[position]} at line {self._current_line}, column {self._current_column}"
                    )
            
            return tokens
            
        except Exception as e:
            logger.error(f"トークン化でエラー: {str(e)}")
            raise

    def _update_position(self, text: str):
        """位置情報の更新"""
        newlines = text.count('\n')
        if newlines > 0:
            self._current_line += newlines
            self._current_column = len(text.split('\n')[-1]) + 1
        else:
            self._current_column += len(text)

class Parser(ABC):
    """構文解析器の基底クラス"""
    
    def __init__(self):
        self._tokens: List[Token] = []
        self._current_pos = 0

    @abstractmethod
    def parse(self, tokens: List[Token]) -> ASTNode:
        """トークンの構文解析"""
        pass

    def _peek(self) -> Optional[Token]:
        """次のトークンを参照"""
        if self._current_pos < len(self._tokens):
            return self._tokens[self._current_pos]
        return None

    def _consume(self) -> Optional[Token]:
        """トークンを消費"""
        if self._current_pos < len(self._tokens):
            token = self._tokens[self._current_pos]
            self._current_pos += 1
            return token
        return None

    def _expect(self, token_type: str) -> Token:
        """期待するトークンの確認"""
        token = self._peek()
        if token and token.type == token_type:
            return self._consume()
        raise SyntaxError(
            f"期待するトークン {token_type} が見つかりません。代わりに {token.type if token else 'EOF'} が見つかりました"
        )

class ASTGenerator:
    """抽象構文木生成器"""
    
    def __init__(self):
        self._parsers: Dict[str, Parser] = {}
        self._current_ast: Optional[ASTNode] = None

    def register_parser(self, source_type: str, parser: Parser):
        """パーサーの登録"""
        self._parsers[source_type] = parser

    def generate(self, source_type: str, tokens: List[Token]) -> ASTNode:
        """ASTの生成"""
        try:
            parser = self._parsers.get(source_type)
            if not parser:
                raise ValueError(f"パーサーが見つかりません: {source_type}")
            
            ast = parser.parse(tokens)
            self._current_ast = ast
            return ast
            
        except Exception as e:
            logger.error(f"AST生成でエラー: {str(e)}")
            raise

class SyntaxValidator:
    """構文検証器"""
    
    def __init__(self):
        self._rules: List[Dict[str, Any]] = []

    def add_rule(self, rule: Dict[str, Any]):
        """検証ルールの追加"""
        self._rules.append(rule)

    def validate(self, ast: ASTNode) -> List[Dict[str, Any]]:
        """ASTの検証"""
        try:
            errors = []
            self._validate_node(ast, errors)
            return errors
        except Exception as e:
            logger.error(f"構文検証でエラー: {str(e)}")
            raise

    def _validate_node(self, node: ASTNode, errors: List[Dict[str, Any]]):
        """ノードの検証"""
        for rule in self._rules:
            if rule['type'] == node.type:
                if not self._check_rule(node, rule):
                    errors.append({
                        'node': node,
                        'rule': rule,
                        'message': rule.get('message', '構文エラー')
                    })
        
        if node.children:
            for child in node.children:
                self._validate_node(child, errors)

    def _check_rule(self, node: ASTNode, rule: Dict[str, Any]) -> bool:
        """ルールのチェック"""
        try:
            condition = rule.get('condition')
            if condition:
                return eval(condition, {'node': node})
            return True
        except Exception:
            return False 