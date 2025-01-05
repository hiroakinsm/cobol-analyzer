# /home/administrator/cobol-analyzer/src/api/response_handler.py
# /srv/cobol-analyzer/src/handlers/response_handler.py

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
import jsonschema
from jsonschema import validators, ValidationError
import html
from xml.etree import ElementTree
import traceback

@dataclass
class ResponseValidationConfig:
    """レスポンス検証設定"""
    max_length: int = 10000
    required_fields: List[str] = field(default_factory=list)
    allowed_tags: List[str] = field(default_factory=list)
    schema_version: str = "1.0"
    strict_mode: bool = False

class ValidationLevel(Enum):
    """検証レベル"""
    STRICT = "strict"
    NORMAL = "normal"
    LENIENT = "lenient"

class ResponseErrorType(Enum):
    """レスポンスエラータイプ"""
    SCHEMA_ERROR = "schema_error"
    FORMAT_ERROR = "format_error"
    CONTENT_ERROR = "content_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"

@dataclass
class ResponseError:
    """レスポンスエラー情報"""
    error_type: ResponseErrorType
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    stacktrace: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式への変換"""
        return {
            "type": self.error_type.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "stacktrace": self.stacktrace if self.stacktrace else None
        }

class ResponseValidator:
    """レスポンスバリデータ"""
    def __init__(self, config: ResponseValidationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._schema_validators = {}

    def validate(self, response: Any, response_type: ResponseType) -> List[ResponseError]:
        """レスポンスの検証"""
        errors = []
        
        try:
            # 基本的な検証
            if not response:
                errors.append(ResponseError(
                    ResponseErrorType.CONTENT_ERROR,
                    "Empty response"
                ))
                return errors

            # 長さの検証
            if isinstance(response, str) and len(response) > self.config.max_length:
                errors.append(ResponseError(
                    ResponseErrorType.VALIDATION_ERROR,
                    f"Response exceeds maximum length of {self.config.max_length}"
                ))

            # レスポンスタイプ固有の検証
            type_specific_errors = self._validate_by_type(response, response_type)
            errors.extend(type_specific_errors)

            # スキーマ検証（JSON/構造化データの場合）
            if response_type in [ResponseType.ANALYSIS, ResponseType.METRICS]:
                schema_errors = self._validate_schema(response, response_type)
                errors.extend(schema_errors)

        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            errors.append(ResponseError(
                ResponseErrorType.PROCESSING_ERROR,
                str(e),
                {"traceback": traceback.format_exc()}
            ))

        return errors

    def _validate_by_type(self, response: Any, response_type: ResponseType) -> List[ResponseError]:
        """レスポンスタイプ別の検証"""
        validation_funcs = {
            ResponseType.ANALYSIS: self._validate_analysis_response,
            ResponseType.METRICS: self._validate_metrics_response,
            ResponseType.SECURITY: self._validate_security_response,
            ResponseType.DOCUMENTATION: self._validate_documentation_response
        }

        if validator_func := validation_funcs.get(response_type):
            return validator_func(response)
        return []

    def _validate_schema(self, response: Any, response_type: ResponseType) -> List[ResponseError]:
        """スキーマ検証"""
        try:
            schema = self._get_schema(response_type)
            if not schema:
                return []

            jsonschema.validate(response, schema)
            return []

        except ValidationError as e:
            return [ResponseError(
                ResponseErrorType.SCHEMA_ERROR,
                str(e),
                {"schema_path": list(e.schema_path)}
            )]
        except Exception as e:
            return [ResponseError(
                ResponseErrorType.PROCESSING_ERROR,
                f"Schema validation failed: {str(e)}"
            )]

    def _get_schema(self, response_type: ResponseType) -> Optional[Dict[str, Any]]:
        """スキーマの取得"""
        if response_type not in self._schema_validators:
            schema_path = f"schemas/{response_type.value}_schema.json"
            try:
                with open(schema_path) as f:
                    schema = json.load(f)
                self._schema_validators[response_type] = schema
            except FileNotFoundError:
                self.logger.warning(f"Schema not found for {response_type}")
                return None

        return self._schema_validators[response_type]

class ResponseProcessor:
    """レスポンス処理"""
    def __init__(self, validator: ResponseValidator):
        self.validator = validator
        self.logger = logging.getLogger(__name__)
        self._processors = {
            ResponseType.ANALYSIS: self._process_analysis_response,
            ResponseType.METRICS: self._process_metrics_response,
            ResponseType.SECURITY: self._process_security_response,
            ResponseType.DOCUMENTATION: self._process_documentation_response
        }

    async def process_response(self, response: str, response_type: ResponseType) -> ProcessedResponse:
        """レスポンスの処理"""
        try:
            # バリデーション
            errors = self.validator.validate(response, response_type)
            if errors and self.validator.config.strict_mode:
                raise ValidationError(
                    f"Response validation failed: {[e.to_dict() for e in errors]}"
                )

            # レスポンスタイプ別の処理
            processor = self._processors.get(response_type)
            if not processor:
                raise ValueError(f"Unsupported response type: {response_type}")

            processed_result = await processor(response)
            
            return ProcessedResponse(
                content=processed_result,
                format=self._determine_format(response),
                type=response_type,
                metadata={
                    "validation_errors": [e.to_dict() for e in errors],
                    "processing_timestamp": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Response processing failed: {str(e)}")
            raise

    def _determine_format(self, response: str) -> ResponseFormat:
        """レスポンスフォーマットの判定"""
        try:
            json.loads(response)
            return ResponseFormat.JSON
        except json.JSONDecodeError:
            if bool(ElementTree.fromstring(response)):
                return ResponseFormat.HTML
            elif bool(re.search(r'^#|\n#', response)):
                return ResponseFormat.MARKDOWN
            return ResponseFormat.TEXT

    async def _process_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析レスポンスの処理"""
        try:
            result = json.loads(response)
            # 追加の処理（必要に応じて）
            return result
        except json.JSONDecodeError:
            raise ValueError("Invalid analysis response format")

    async def _process_metrics_response(self, response: str) -> Dict[str, Any]:
        """メトリクスレスポンスの処理"""
        try:
            metrics = json.loads(response)
            # メトリクスの正規化や変換
            return self._normalize_metrics(metrics)
        except json.JSONDecodeError:
            raise ValueError("Invalid metrics response format")

    async def _process_security_response(self, response: str) -> Dict[str, Any]:
        """セキュリティレスポンスの処理"""
        try:
            security_data = json.loads(response)
            # セキュリティデータの処理
            return self._process_security_data(security_data)
        except json.JSONDecodeError:
            raise ValueError("Invalid security response format")

    async def _process_documentation_response(self, response: str) -> str:
        """ドキュメントレスポンスの処理"""
        # Markdownの処理とHTMLへの変換
        html_content = markdown.markdown(response)
        # XSS対策
        sanitized_content = html.escape(html_content)
        return sanitized_content

    def _normalize_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスの正規化"""
        normalized = {}
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                normalized[key] = round(float(value), 2)
            elif isinstance(value, dict):
                normalized[key] = self._normalize_metrics(value)
            else:
                normalized[key] = value
        return normalized

    def _process_security_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティデータの処理"""
        processed = {
            "vulnerabilities": [],
            "risk_level": data.get("risk_level", "unknown"),
            "summary": data.get("summary", {})
        }

        for vuln in data.get("vulnerabilities", []):
            processed["vulnerabilities"].append({
                "severity": vuln.get("severity", "unknown"),
                "description": html.escape(vuln.get("description", "")),
                "recommendation": html.escape(vuln.get("recommendation", "")),
                "affected_components": vuln.get("affected_components", [])
            })

        return processed

# ユーティリティ関数
def sanitize_input(input_str: str) -> str:
    """入力の無害化"""
    return html.escape(input_str)

def validate_json_schema(instance: Any, schema: Dict[str, Any]) -> List[str]:
    """JSONスキーマの検証"""
    validator = validators.validator_for(schema)(schema)
    return [error.message for error in validator.iter_errors(instance)]