# /home/administrator/ai-server/src/ai/prompts/templates.py

from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import json
import logging
import jinja2
from dataclasses import dataclass
import hashlib
from enum import Enum
from abc import ABC, abstractmethod

class TemplateType(Enum):
    ANALYSIS = "analysis"
    METRICS = "metrics"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    RECOMMENDATIONS = "recommendations"

@dataclass
class TemplateVersion:
    """テンプレートバージョン情報"""
    version: str
    created_at: datetime
    created_by: str
    description: str
    changes: List[str]
    hash: str

@dataclass
class PromptTemplate:
    """プロンプトテンプレート基本情報"""
    name: str
    template_type: TemplateType
    content: str
    version: TemplateVersion
    variables: List[str]
    required_variables: List[str]
    max_tokens: int
    enabled: bool = True

class TemplateValidator:
    """テンプレート検証クラス"""
    def validate_template(self, template: str, variables: List[str]) -> List[str]:
        """テンプレートの検証"""
        errors = []
        env = jinja2.Environment()

        try:
            # テンプレートの構文チェック
            parsed_template = env.parse(template)
            template_variables = list(self._extract_variables(parsed_template))

            # 未定義変数のチェック
            undefined_vars = set(template_variables) - set(variables)
            if undefined_vars:
                errors.append(f"Undefined variables: {', '.join(undefined_vars)}")

            # テンプレート長の検証
            if len(template.split()) > 2000:  # トークン数の概算
                errors.append("Template exceeds maximum length")

        except jinja2.TemplateSyntaxError as e:
            errors.append(f"Template syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"Template validation error: {str(e)}")

        return errors

    def _extract_variables(self, ast) -> set:
        """テンプレート変数の抽出"""
        variables = set()
        
        def visit(node):
            if isinstance(node, jinja2.nodes.Name):
                variables.add(node.name)
            if isinstance(node, jinja2.nodes.If):
                variables.add(node.test.name)
            for child in node.iter_child_nodes():
                visit(child)
        
        visit(ast)
        return variables

class TemplateRenderer:
    """テンプレートレンダリングクラス"""
    def __init__(self):
        self.env = jinja2.Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.logger = logging.getLogger(__name__)

    def render_template(self, template: str, context: Dict[str, Any]) -> str:
        """テンプレートのレンダリング"""
        try:
            template_obj = self.env.from_string(template)
            return template_obj.render(**context)
        except Exception as e:
            self.logger.error(f"Template rendering failed: {str(e)}")
            raise

class TemplateManager:
    """テンプレート管理クラス"""
    def __init__(self, template_path: Path, version_db: Any):
        self.template_path = template_path
        self.version_db = version_db
        self.validator = TemplateValidator()
        self.renderer = TemplateRenderer()
        self.templates: Dict[str, PromptTemplate] = {}
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """テンプレートの初期化"""
        await self.load_templates()

    async def load_templates(self):
        """テンプレートの読み込み"""
        try:
            with open(self.template_path) as f:
                template_data = json.load(f)

            for name, data in template_data["templates"].items():
                version_info = await self._get_latest_version(name)
                template = PromptTemplate(
                    name=name,
                    template_type=TemplateType(data["type"]),
                    content=data["template"],
                    version=version_info,
                    variables=data["variables"],
                    required_variables=data.get("required_variables", []),
                    max_tokens=data.get("max_tokens", 1000)
                )
                
                # テンプレートの検証
                errors = self.validator.validate_template(
                    template.content,
                    template.variables
                )
                if errors:
                    self.logger.error(f"Template validation failed for {name}: {errors}")
                    continue

                self.templates[name] = template

        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")
            raise

    async def _get_latest_version(self, template_name: str) -> TemplateVersion:
        """最新バージョン情報の取得"""
        version_info = await self.version_db.get_latest_version(template_name)
        return TemplateVersion(
            version=version_info["version"],
            created_at=version_info["created_at"],
            created_by=version_info["created_by"],
            description=version_info["description"],
            changes=version_info["changes"],
            hash=version_info["hash"]
        )

    async def update_template(self, 
                            name: str, 
                            content: str,
                            user: str,
                            description: str,
                            changes: List[str]) -> TemplateVersion:
        """テンプレートの更新"""
        if name not in self.templates:
            raise ValueError(f"Template not found: {name}")

        template = self.templates[name]
        
        # テンプレートの検証
        errors = self.validator.validate_template(content, template.variables)
        if errors:
            raise ValueError(f"Template validation failed: {errors}")

        # バージョン情報の生成
        version_info = TemplateVersion(
            version=self._generate_version(),
            created_at=datetime.utcnow(),
            created_by=user,
            description=description,
            changes=changes,
            hash=self._generate_hash(content)
        )

        # データベースの更新
        await self.version_db.store_version(name, version_info)
        
        # テンプレートの更新
        template.content = content
        template.version = version_info
        self.templates[name] = template

        return version_info

    def _generate_version(self) -> str:
        """バージョン文字列の生成"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"v{timestamp}"

    def _generate_hash(self, content: str) -> str:
        """テンプレートのハッシュ値生成"""
        return hashlib.sha256(content.encode()).hexdigest()

    async def render_prompt(self, 
                          template_name: str, 
                          context: Dict[str, Any]) -> str:
        """プロンプトの生成"""
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        template = self.templates[template_name]
        
        # 必須変数のチェック
        missing_vars = [var for var in template.required_variables 
                       if var not in context]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        try:
            return self.renderer.render_template(template.content, context)
        except Exception as e:
            self.logger.error(f"Prompt generation failed: {str(e)}")
            raise

    async def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """テンプレート情報の取得"""
        if template_name not in self.templates:
            raise ValueError(f"Template not found: {template_name}")

        template = self.templates[template_name]
        version_history = await self.version_db.get_version_history(template_name)

        return {
            "name": template.name,
            "type": template.template_type.value,
            "current_version": template.version,
            "variables": template.variables,
            "required_variables": template.required_variables,
            "max_tokens": template.max_tokens,
            "enabled": template.enabled,
            "version_history": version_history
        }

class TemplateRegistry:
    """テンプレートレジストリ"""
    def __init__(self):
        self.templates: Dict[str, List[PromptTemplate]] = {}
        self.logger = logging.getLogger(__name__)

    async def register_template(self, template: PromptTemplate):
        """テンプレートの登録"""
        if template.template_type not in self.templates:
            self.templates[template.template_type] = []
        
        self.templates[template.template_type].append(template)
        self.logger.info(f"Registered template: {template.name}")

    async def get_templates_by_type(self, template_type: TemplateType) -> List[PromptTemplate]:
        """タイプ別のテンプレート取得"""
        return self.templates.get(template_type, [])

    async def remove_template(self, template_name: str):
        """テンプレートの削除"""
        for templates in self.templates.values():
            templates[:] = [t for t in templates if t.name != template_name]
        self.logger.info(f"Removed template: {template_name}")

# テンプレートのバージョン管理用インターフェース
class TemplateVersionDB(ABC):
    """テンプレートバージョン管理データベース"""
    @abstractmethod
    async def get_latest_version(self, template_name: str) -> Dict[str, Any]:
        """最新バージョンの取得"""
        raise NotImplementedError

    @abstractmethod
    async def store_version(self, template_name: str, version: TemplateVersion):
        """バージョン情報の保存"""
        raise NotImplementedError

    @abstractmethod
    async def get_version_history(self, template_name: str) -> List[Dict[str, Any]]:
        """バージョン履歴の取得"""
        raise NotImplementedError

# 以下は使用例
# async def initialize_template_system(template_path: Path, version_db: TemplateVersionDB):
#    """テンプレートシステムの初期化"""
#    manager = TemplateManager(template_path, version_db)
#    await manager.initialize()
#    return manager
```