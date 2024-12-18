```python
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import json
import re
from enum import Enum
import logging
from pydantic import BaseModel, Field, validator
from abc import ABC, abstractmethod

class ResponseFormat(Enum):
    """レスポンスフォーマット"""
    JSON = "json"
    MARKDOWN = "markdown"
    TEXT = "text"

class PromptType(Enum):
    """プロンプトタイプ"""
    ANALYSIS = "analysis"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    METRICS = "metrics"

@dataclass
class TemplateConfig:
    """テンプレート設定"""
    template: str
    parameters: List[str]
    max_tokens: int
    system_prompt: Optional[str] = None
    format: Optional[ResponseFormat] = None

class PromptValidationError(Exception):
    """プロンプトバリデーションエラー"""
    pass

class TemplateParameter(BaseModel):
    """テンプレートパラメータ"""
    name: str
    value: Any
    required: bool = True
    validator: Optional[str] = None

    @validator('value')
    def validate_value(cls, v, values):
        """値の検証"""
        if values.get('required') and v is None:
            raise ValueError(f"Required parameter {values.get('name')} is missing")
        return v

class PromptManager:
    """プロンプト管理"""
    def __init__(self, template_path: Path):
        self.templates = self._load_templates(template_path)
        self.logger = logging.getLogger(__name__)
        self._parameter_validators = self._init_validators()

    def _load_templates(self, template_path: Path) -> Dict[str, TemplateConfig]:
        """テンプレートの読み込み"""
        try:
            with open(template_path) as f:
                data = json.load(f)
                return {
                    name: TemplateConfig(**config)
                    for name, config in data["templates"].items()
                }
        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")
            raise

    def _init_validators(self) -> Dict[str, callable]:
        """バリデータの初期化"""
        return {
            "metrics": self._validate_metrics,
            "code": self._validate_code,
            "analysis": self._validate_analysis,
            "security": self._validate_security
        }

    async def generate_prompt(self,
                            template_name: str,
                            parameters: Dict[str, Any],
                            prompt_type: PromptType,
                            format: Optional[ResponseFormat] = None) -> str:
        """プロンプトの生成"""
        try:
            # テンプレートの取得
            template_config = self.templates.get(template_name)
            if not template_config:
                raise PromptValidationError(f"Template not found: {template_name}")

            # パラメータの検証
            validated_params = await self._validate_parameters(
                template_config.parameters,
                parameters
            )

            # システムプロンプトの取得
            system_prompt = self._get_system_prompt(prompt_type)

            # プロンプトの構築
            prompt = self._build_prompt(
                template_config.template,
                validated_params,
                system_prompt,
                format or template_config.format
            )

            return prompt

        except Exception as e:
            self.logger.error(f"Failed to generate prompt: {str(e)}")
            raise

    async def _validate_parameters(self,
                                 required_params: List[str],
                                 provided_params: Dict[str, Any]) -> Dict[str, Any]:
        """パラメータの検証"""
        validated = {}
        for param in required_params:
            if param not in provided_params:
                raise PromptValidationError(f"Missing required parameter: {param}")
            
            value = provided_params[param]
            validator = self._parameter_validators.get(param)
            if validator:
                value = await validator(value)
            validated[param] = value

        return validated

    def _build_prompt(self,
                     template: str,
                     parameters: Dict[str, Any],
                     system_prompt: str,
                     format: Optional[ResponseFormat]) -> str:
        """プロンプトの構築"""
        prompt_parts = []

        # システムプロンプトの追加
        if system_prompt:
            prompt_parts.append(system_prompt)

        # テンプレートの適用
        prompt_parts.append(template.format(**parameters))

        # フォーマット指定の追加
        if format:
            prompt_parts.append(self._get_format_instruction(format))

        return "\n\n".join(prompt_parts)

    async def _validate_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスの検証"""
        required_fields = ["complexity", "maintainability", "security"]
        for field in required_fields:
            if field not in metrics:
                raise PromptValidationError(f"Missing required metrics field: {field}")
        return metrics

    async def _validate_code(self, code: str) -> str:
        """コードの検証"""
        if not code.strip():
            raise PromptValidationError("Empty code content")
        return code

    async def _validate_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """解析結果の検証"""
        if not isinstance(analysis, dict):
            raise PromptValidationError("Analysis must be a dictionary")
        return analysis

    async def _validate_security(self, security: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ結果の検証"""
        required_fields = ["vulnerabilities", "risk_level"]
        for field in required_fields:
            if field not in security:
                raise PromptValidationError(f"Missing required security field: {field}")
        return security

    def _get_system_prompt(self, prompt_type: PromptType) -> str:
        """システムプロンプトの取得"""
        system_prompts = {
            PromptType.ANALYSIS: "あなたはCOBOLコード解析の専門家として、詳細な技術分析を提供します。",
            PromptType.SECURITY: "あなたはCOBOLアプリケーションのセキュリティ専門家として、包括的なセキュリティ評価を提供します。",
            PromptType.DOCUMENTATION: "あなたは技術文書作成の専門家として、明確で構造化された文書を作成します。",
            PromptType.METRICS: "あなたはソフトウェアメトリクスの専門家として、定量的な品質評価を提供します。"
        }
        return system_prompts.get(prompt_type, "")

    def _get_format_instruction(self, format: ResponseFormat) -> str:
        """フォーマット指示の取得"""
        format_instructions = {
            ResponseFormat.JSON: "以下の形式のJSONで回答してください：\n{schema}",
            ResponseFormat.MARKDOWN: "マークダウン形式で、以下のセクションを含めて回答してください：\n{sections}",
            ResponseFormat.TEXT: "明確で構造化された文章で回答してください。"
        }
        return format_instructions.get(format, "")

class PromptTemplateManager:
    """プロンプトテンプレート管理"""
    def __init__(self, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.template_cache: Dict[str, str] = {}

    async def get_template(self,
                         template_name: str,
                         cache: bool = True) -> str:
        """テンプレートの取得"""
        if cache and template_name in self.template_cache:
            return self.template_cache[template_name]

        template = self.prompt_manager.templates.get(template_name)
        if not template:
            raise PromptValidationError(f"Template not found: {template_name}")

        if cache:
            self.template_cache[template_name] = template
        return template

    async def create_template(self,
                            template_name: str,
                            template: str,
                            parameters: List[str],
                            max_tokens: int) -> None:
        """新しいテンプレートの作成"""
        self.prompt_manager.templates[template_name] = TemplateConfig(
            template=template,
            parameters=parameters,
            max_tokens=max_tokens
        )

# 使用例
async def prompt_management_example():
    # プロンプトマネージャーの初期化
    prompt_manager = PromptManager(Path("templates/prompts.json"))
    template_manager = PromptTemplateManager(prompt_manager)

    # メトリクス解析用のパラメータ
    metrics_params = {
        "metrics_data": {
            "complexity": 15,
            "maintainability": 75,
            "security": "medium"
        },
        "baseline_metrics": {
            "complexity": 10,
            "maintainability": 80,
            "security": "high"
        }
    }

    # メトリクス解析プロンプトの生成
    metrics_prompt = await prompt_manager.generate_prompt(
        "metrics_explanation",
        metrics_params,
        PromptType.METRICS,
        ResponseFormat.MARKDOWN
    )
    print("Generated metrics prompt:", metrics_prompt)

    # セキュリティ解析用のパラメータ
    security_params = {
        "program_info": {
            "name": "EXAMPLE",
            "type": "batch"
        },
        "security_results": {
            "vulnerabilities": ["SQL injection risk"],
            "risk_level": "high"
        }
    }

    # セキュリティ解析プロンプトの生成
    security_prompt = await prompt_manager.generate_prompt(
        "security_analysis",
        security_params,
        PromptType.SECURITY,
        ResponseFormat.JSON
    )
    print("Generated security prompt:", security_prompt)
```