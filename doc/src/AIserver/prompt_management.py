# /home/administrator/ai-server/src/prompts/prompt_management.py
# /srv/cobol-analyzer/src/prompt/prompt_management.py

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import json
import re
import logging
from pydantic import BaseModel, Field, validator
from enum import Enum
from datetime import datetime
import hashlib
import semver

@dataclass
class PromptVersion:
    """プロンプトバージョン情報"""
    version: str
    created_at: datetime
    author: str
    description: str
    changes: List[str]
    hash: str

class PromptVersionManager:
    """プロンプトバージョン管理"""
    def __init__(self, version_db_path: Path):
        self.version_db_path = version_db_path
        self.versions: Dict[str, Dict[str, PromptVersion]] = {}
        self.current_versions: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        self._load_versions()

    def _load_versions(self):
        """バージョン情報の読み込み"""
        try:
            with open(self.version_db_path) as f:
                data = json.load(f)
                for template_name, versions in data.items():
                    self.versions[template_name] = {
                        ver_str: PromptVersion(**ver_data)
                        for ver_str, ver_data in versions.items()
                    }
                    # 最新バージョンを設定
                    self.current_versions[template_name] = max(
                        versions.keys(),
                        key=lambda v: semver.VersionInfo.parse(v)
                    )
        except FileNotFoundError:
            self.logger.warning("Version database not found, creating new one")
            self._save_versions()

    def _save_versions(self):
        """バージョン情報の保存"""
        data = {
            template_name: {
                ver_str: {
                    "version": ver.version,
                    "created_at": ver.created_at.isoformat(),
                    "author": ver.author,
                    "description": ver.description,
                    "changes": ver.changes,
                    "hash": ver.hash
                }
                for ver_str, ver in versions.items()
            }
            for template_name, versions in self.versions.items()
        }
        with open(self.version_db_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_version(self,
                      template_name: str,
                      template_content: str,
                      author: str,
                      description: str,
                      changes: List[str]) -> PromptVersion:
        """新しいバージョンの作成"""
        if template_name not in self.versions:
            self.versions[template_name] = {}
            new_version = "1.0.0"
        else:
            current = self.current_versions[template_name]
            new_version = str(semver.VersionInfo.parse(current).bump_minor())

        version = PromptVersion(
            version=new_version,
            created_at=datetime.utcnow(),
            author=author,
            description=description,
            changes=changes,
            hash=self._calculate_hash(template_content)
        )

        self.versions[template_name][new_version] = version
        self.current_versions[template_name] = new_version
        self._save_versions()
        return version

    def _calculate_hash(self, content: str) -> str:
        """コンテンツのハッシュ計算"""
        return hashlib.sha256(content.encode()).hexdigest()

    def get_version(self,
                   template_name: str,
                   version: Optional[str] = None) -> Optional[PromptVersion]:
        """バージョン情報の取得"""
        if template_name not in self.versions:
            return None

        if version is None:
            version = self.current_versions[template_name]

        return self.versions[template_name].get(version)

    def get_version_history(self,
                          template_name: str) -> List[PromptVersion]:
        """バージョン履歴の取得"""
        if template_name not in self.versions:
            return []

        return sorted(
            self.versions[template_name].values(),
            key=lambda v: semver.VersionInfo.parse(v.version)
        )

class PromptManager:
    """プロンプト管理"""
    def __init__(self, 
                 template_path: Path,
                 version_db_path: Optional[Path] = None):
        self.templates = self._load_templates(template_path)
        self.logger = logging.getLogger(__name__)
        self.version_manager = PromptVersionManager(
            version_db_path or template_path.parent / "versions.json"
        )
        self._parameter_validators = self._init_validators()

    def _load_templates(self, template_path: Path) -> Dict[str, Dict[str, Any]]:
        """テンプレートの読み込み"""
        try:
            with open(template_path) as f:
                data = json.load(f)
                templates = {}
                for name, template in data["templates"].items():
                    version = self.version_manager.get_version(name)
                    if version:
                        template["version"] = version
                    templates[name] = template
                return templates
        except Exception as e:
            self.logger.error(f"Failed to load templates: {str(e)}")
            raise

    async def create_template_version(self,
                                    template_name: str,
                                    template_content: str,
                                    author: str,
                                    description: str,
                                    changes: List[str]) -> PromptVersion:
        """テンプレートの新バージョン作成"""
        version = self.version_manager.create_version(
            template_name,
            template_content,
            author,
            description,
            changes
        )
        
        # テンプレートの更新
        if template_name in self.templates:
            self.templates[template_name]["version"] = version
            self.templates[template_name]["content"] = template_content
            
        return version

    async def get_template_history(self,
                                 template_name: str) -> List[PromptVersion]:
        """テンプレートの変更履歴取得"""
        return self.version_manager.get_version_history(template_name)

    async def rollback_template(self,
                              template_name: str,
                              version: str) -> bool:
        """テンプレートのロールバック"""
        if template_name not in self.templates:
            return False

        target_version = self.version_manager.get_version(template_name, version)
        if not target_version:
            return False

        # ロールバックバージョンの作成
        await self.create_template_version(
            template_name,
            self.templates[template_name]["content"],
            "system",
            f"Rollback to version {version}",
            [f"Rolled back to version {version}"]
        )
        return True

    def _init_validators(self) -> Dict[str, callable]:
        """バリデータの初期化"""
        return {
            "metrics": self._validate_metrics_params,
            "code": self._validate_code_params,
            "analysis": self._validate_analysis_params,
            "security": self._validate_security_params
        }

    async def generate_prompt(self,
                           template_name: str,
                           parameters: Dict[str, Any],
                           prompt_type: PromptType,
                           version: Optional[str] = None) -> str:
        """プロンプトの生成"""
        try:
            # テンプレートの取得
            template_config = self.templates.get(template_name)
            if not template_config:
                raise ValueError(f"Template not found: {template_name}")

            # バージョン検証
            if version:
                template_version = self.version_manager.get_version(template_name, version)
                if not template_version:
                    raise ValueError(f"Version {version} not found for template {template_name}")
            else:
                template_version = self.version_manager.get_version(template_name)

            # パラメータの検証
            validated_params = await self._validate_parameters(
                template_config["parameters"],
                parameters
            )

            # プロンプトの構築
            prompt = self._build_prompt(
                template_config["template"],
                validated_params,
                prompt_type,
                template_version
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
                raise ValueError(f"Missing required parameter: {param}")
            
            value = provided_params[param]
            validator = self._parameter_validators.get(param)
            if validator:
                value = await validator(value)
            validated[param] = value

        return validated

    async def _validate_metrics_params(self, value: Any) -> Dict[str, Any]:
        """メトリクスパラメータの検証"""
        if not isinstance(value, dict):
            raise ValueError("Metrics must be a dictionary")
        required_fields = ["complexity", "maintainability", "security"]
        for field in required_fields:
            if field not in value:
                raise ValueError(f"Missing required metrics field: {field}")
        return value

    async def _validate_code_params(self, value: str) -> str:
        """コードパラメータの検証"""
        if not value.strip():
            raise ValueError("Empty code content")
        return value

    async def _validate_analysis_params(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """解析パラメータの検証"""
        if not isinstance(value, dict):
            raise ValueError("Analysis must be a dictionary")
        return value

    async def _validate_security_params(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティパラメータの検証"""
        if not isinstance(value, dict):
            raise ValueError("Security parameters must be a dictionary")
        required_fields = ["vulnerabilities", "risk_level"]
        for field in required_fields:
            if field not in value:
                raise ValueError(f"Missing required security field: {field}")
        return value

    def _build_prompt(self,
                     template: str,
                     parameters: Dict[str, Any],
                     prompt_type: PromptType,
                     version: PromptVersion) -> str:
        """プロンプトの構築"""
        # システムプロンプトの取得
        system_prompt = self._get_system_prompt(prompt_type)

        # テンプレートの適用
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(system_prompt)

        formatted_template = template.format(**parameters)
        prompt_parts.append(formatted_template)

        # バージョン情報の追加
        prompt_parts.append(f"\nTemplate Version: {version.version}")
        prompt_parts.append(f"Generated at: {datetime.utcnow().isoformat()}")

        return "\n\n".join(prompt_parts)

    def _get_system_prompt(self, prompt_type: PromptType) -> Optional[str]:
        """システムプロンプトの取得"""
        system_prompts = {
            PromptType.ANALYSIS: "You are a COBOL code analysis expert.",
            PromptType.SECURITY: "You are a COBOL security analysis expert.",
            PromptType.DOCUMENTATION: "You are a technical documentation expert.",
            PromptType.METRICS: "You are a software metrics analysis expert."
        }
        return system_prompts.get(prompt_type)

    async def cleanup(self):
        """リソースのクリーンアップ"""
        # バージョン情報の保存
        self.version_manager._save_versions()
        # テンプレートのクリーンアップ
        self.templates.clear()
