```python
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import json
import re
import logging
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, validator
import markdown
from datetime import datetime

T = TypeVar('T')

class ResponseFormat(str, Enum):
    """レスポンスフォーマット"""
    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"

class ResponseType(str, Enum):
    """レスポンスタイプ"""
    ANALYSIS = "analysis"
    METRICS = "metrics"
    SECURITY = "security"
    DOCUMENTATION = "documentation"

@dataclass
class ProcessedResponse(Generic[T]):
    """処理済みレスポンス"""
    content: T
    format: ResponseFormat
    type: ResponseType
    metadata: Dict[str, Any]
    processed_at: datetime = Field(default_factory=datetime.utcnow)

class ResponseValidationError(Exception):
    """レスポンス検証エラー"""
    pass

class ResponseHandler(ABC):
    """レスポンスハンドラーの基底クラス"""
    @abstractmethod
    async def process_response(self, response: str) -> ProcessedResponse:
        """レスポンスの処理"""
        pass

    @abstractmethod
    async def validate_response(self, response: Any) -> bool:
        """レスポンスの検証"""
        pass

class JSONResponseHandler(ResponseHandler):
    """JSONレスポンスハンドラー"""
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.logger = logging.getLogger(__name__)

    async def process_response(self, response: str) -> ProcessedResponse[Dict[str, Any]]:
        try:
            # JSONの抽出
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ResponseValidationError("No JSON found in response")
            
            json_str = json_match.group(0)
            content = json.loads(json_str)

            # スキーマ検証
            if not await self.validate_response(content):
                raise ResponseValidationError("Response does not match schema")

            return ProcessedResponse(
                content=content,
                format=ResponseFormat.JSON,
                type=self._determine_response_type(content),
                metadata={"schema_version": "1.0"}
            )

        except Exception as e:
            self.logger.error(f"Failed to process JSON response: {str(e)}")
            raise

    async def validate_response(self, response: Dict[str, Any]) -> bool:
        """JSONスキーマの検証"""
        try:
            self._validate_against_schema(response, self.schema)
            return True
        except Exception as e:
            self.logger.error(f"JSON validation failed: {str(e)}")
            return False

    def _validate_against_schema(self, obj: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """再帰的なスキーマ検証"""
        for key, type_info in schema.items():
            if key not in obj:
                raise ResponseValidationError(f"Missing required field: {key}")
            
            if isinstance(type_info, dict):
                if not isinstance(obj[key], dict):
                    raise ResponseValidationError(f"Field {key} should be an object")
                self._validate_against_schema(obj[key], type_info)
            else:
                self._validate_type(obj[key], type_info)

    def _validate_type(self, value: Any, expected_type: str) -> None:
        """型の検証"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        if not isinstance(value, type_mapping.get(expected_type, object)):
            raise ResponseValidationError(
                f"Type mismatch: expected {expected_type}, got {type(value)}"
            )

class MarkdownResponseHandler(ResponseHandler):
    """Markdownレスポンスハンドラー"""
    def __init__(self, required_sections: List[str]):
        self.required_sections = required_sections
        self.logger = logging.getLogger(__name__)

    async def process_response(self, response: str) -> ProcessedResponse[str]:
        try:
            # Markdownの検証
            if not await self.validate_response(response):
                raise ResponseValidationError("Invalid markdown format")

            # セクションの抽出と構造化
            sections = self._extract_sections(response)

            # HTMLへの変換（オプション）
            html_content = markdown.markdown(response)

            return ProcessedResponse(
                content=response,
                format=ResponseFormat.MARKDOWN,
                type=self._determine_response_type(sections),
                metadata={
                    "sections": list(sections.keys()),
                    "html_content": html_content
                }
            )

        except Exception as e:
            self.logger.error(f"Failed to process Markdown response: {str(e)}")
            raise

    async def validate_response(self, response: str) -> bool:
        """Markdownの検証"""
        try:
            sections = self._extract_sections(response)
            return all(section in sections for section in self.required_sections)
        except Exception as e:
            self.logger.error(f"Markdown validation failed: {str(e)}")
            return False

    def _extract_sections(self, markdown_text: str) -> Dict[str, str]:
        """セクションの抽出"""
        sections = {}
        current_section = None
        current_content = []

        for line in markdown_text.split('\n'):
            if line.startswith('#'):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line.lstrip('#').strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

class AnalysisResponseHandler(ResponseHandler):
    """解析結果レスポンスハンドラー"""
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.json_handler = JSONResponseHandler(self._get_analysis_schema())
        self.markdown_handler = MarkdownResponseHandler(
            ["Summary", "Analysis", "Recommendations"]
        )

    async def process_response(self, response: str) -> ProcessedResponse:
        """レスポンスの処理"""
        try:
            # フォーマットの判定
            if self._is_json(response):
                return await self.json_handler.process_response(response)
            else:
                return await self.markdown_handler.process_response(response)

        except Exception as e:
            self.logger.error(f"Failed to process analysis response: {str(e)}")
            raise

    async def validate_response(self, response: Any) -> bool:
        """レスポンスの検証"""
        try:
            if isinstance(response, dict):
                return await self.json_handler.validate_response(response)
            elif isinstance(response, str):
                return await self.markdown_handler.validate_response(response)
            return False
        except Exception as e:
            self.logger.error(f"Analysis validation failed: {str(e)}")
            return False

    def _get_analysis_schema(self) -> Dict[str, Any]:
        """解析結果のスキーマ定義"""
        return {
            "summary": "string",
            "metrics": {
                "complexity": "number",
                "maintainability": "number",
                "security_score": "number"
            },
            "recommendations": "array",
            "details": "object"
        }

    def _is_json(self, text: str) -> bool:
        """JSON形式かどうかの判定"""
        try:
            json.loads(text)
            return True
        except json.JSONDecodeError:
            return False

class ResponseProcessingPipeline:
    """レスポンス処理パイプライン"""
    def __init__(self):
        self.handlers: Dict[ResponseType, ResponseHandler] = {}
        self.logger = logging.getLogger(__name__)

    def register_handler(self, response_type: ResponseType, handler: ResponseHandler) -> None:
        """ハンドラーの登録"""
        self.handlers[response_type] = handler

    async def process(self, 
                     response: str,
                     response_type: ResponseType) -> ProcessedResponse:
        """レスポンスの処理"""
        try:
            handler = self.handlers.get(response_type)
            if not handler:
                raise ValueError(f"No handler registered for type: {response_type}")

            return await handler.process_response(response)

        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            raise

# 使用例
async def response_handler_example():
    # パイプラインの設定
    pipeline = ResponseProcessingPipeline()
    
    # ハンドラーの登録
    pipeline.register_handler(
        ResponseType.ANALYSIS,
        AnalysisResponseHandler()
    )
    
    # JSONレスポンスの処理
    json_response = """
    {
        "summary": "Code analysis results",
        "metrics": {
            "complexity": 15,
            "maintainability": 75,
            "security_score": 85
        },
        "recommendations": [
            "Reduce complexity in module X",
            "Improve error handling"
        ],
        "details": {
            "critical_sections": 2,
            "optimization_opportunities": 3
        }
    }
    """
    
    processed_json = await pipeline.process(
        json_response,
        ResponseType.ANALYSIS
    )
    print("Processed JSON:", processed_json)
    
    # Markdownレスポンスの処理
    markdown_response = """
    # Summary
    Analysis of COBOL program XYZ
    
    # Analysis
    The program shows high complexity...
    
    # Recommendations
    1. Refactor complex sections
    2. Add error handling
    """
    
    processed_markdown = await pipeline.process(
        markdown_response,
        ResponseType.ANALYSIS
    )
    print("Processed Markdown:", processed_markdown)
```