# /home/administrator/cobol-analyzer/src/documents/document_generation.py
# /srv/cobol-analyzer/src/document/document_generation.py

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import UUID
from fpdf import FPDF
import json
import os
from pathlib import Path
import jinja2
from dataclasses import dataclass
import yaml
from abc import ABC, abstractmethod

@dataclass
class DocumentConfig:
    """ドキュメント生成設定"""
    template_path: Path
    output_path: Path
    custom_templates_path: Optional[Path] = None
    style_config_path: Optional[Path] = None
    language: str = "ja"
    default_font: str = "Gothic"
    enable_custom_styles: bool = True

class DocumentTemplateManager:
    """テンプレート管理"""
    def __init__(self, config: DocumentConfig):
        self.config = config
        self.env = self._create_jinja_env()
        self.custom_templates: Dict[str, str] = {}
        self.style_config = self._load_style_config()

    def _create_jinja_env(self) -> jinja2.Environment:
        """Jinja2環境の作成"""
        template_paths = [self.config.template_path]
        if self.config.custom_templates_path:
            template_paths.append(self.config.custom_templates_path)

        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_paths),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def _load_style_config(self) -> Dict[str, Any]:
        """スタイル設定の読み込み"""
        if not self.config.style_config_path:
            return {}

        with open(self.config.style_config_path) as f:
            return yaml.safe_load(f)

    def register_custom_template(self, name: str, template: str):
        """カスタムテンプレートの登録"""
        self.custom_templates[name] = template
        self.env.globals[f"custom_{name}"] = template

    def get_template(self, name: str) -> jinja2.Template:
        """テンプレートの取得"""
        if name in self.custom_templates:
            return self.env.from_string(self.custom_templates[name])
        return self.env.get_template(f"{name}.jinja2")

class DocumentStyleManager:
    """ドキュメントスタイル管理"""
    def __init__(self, style_config: Dict[str, Any]):
        self.style_config = style_config
        self.custom_styles: Dict[str, Dict[str, Any]] = {}

    def register_custom_style(self, name: str, style: Dict[str, Any]):
        """カスタムスタイルの登録"""
        self.custom_styles[name] = style

    def get_style(self, name: str) -> Dict[str, Any]:
        """スタイルの取得"""
        if name in self.custom_styles:
            return self.custom_styles[name]
        return self.style_config.get(name, {})

class DocumentGenerator:
    """ドキュメント生成処理"""
    def __init__(self, 
                 db_functions, 
                 config: DocumentConfig):
        self.db = db_functions
        self.config = config
        self.template_manager = DocumentTemplateManager(config)
        self.style_manager = DocumentStyleManager(
            self.template_manager.style_config
        )
        self.logger = logging.getLogger(__name__)

    async def generate_analysis_document(self, 
                                      source_id: UUID,
                                      template_name: str = "analysis_report",
                                      custom_style: Optional[Dict[str, Any]] = None) -> str:
        """解析ドキュメントの生成"""
        try:
            # 解析結果の取得
            analysis_results = await self.db.get_analysis_results(source_id)
            if not analysis_results:
                raise ValueError(f"Analysis results not found for source {source_id}")

            # プログラム情報の取得
            program_info = await self.db.get_source_info(source_id)

            # カスタムスタイルの適用
            if custom_style and self.config.enable_custom_styles:
                style_name = f"custom_{source_id}"
                self.style_manager.register_custom_style(style_name, custom_style)
            else:
                style_name = "default"

            # テンプレートの取得と適用
            template = self.template_manager.get_template(template_name)
            content = template.render(
                program_info=program_info,
                analysis_results=analysis_results,
                style=self.style_manager.get_style(style_name),
                timestamp=datetime.utcnow(),
                language=self.config.language
            )

            # PDFの生成
            pdf = self._create_pdf_document(content, style_name)
            
            # ドキュメントの保存
            output_path = await self._save_document(source_id, pdf)
            
            return output_path

        except Exception as e:
            self.logger.error(f"Document generation failed: {str(e)}")
            raise

    def _create_pdf_document(self, content: str, style_name: str) -> FPDF:
        """PDFドキュメントの作成"""
        pdf = CustomPDF()
        style = self.style_manager.get_style(style_name)
        
        # スタイルの適用
        pdf.set_font(self.config.default_font, size=style.get("font_size", 10))
        pdf.set_margins(
            style.get("margin_left", 15),
            style.get("margin_top", 15),
            style.get("margin_right", 15)
        )

        # コンテンツの追加
        pdf.add_page()
        pdf.write_html(content)
        
        return pdf

    async def _save_document(self, source_id: UUID, pdf: FPDF) -> str:
        """ドキュメントの保存"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = self.config.output_path / f"analysis_report_{source_id}_{timestamp}.pdf"
        
        # 出力ディレクトリの作成
        os.makedirs(self.config.output_path, exist_ok=True)
        
        # PDFの保存
        pdf.output(str(output_path))
        
        return str(output_path)

class CustomPDF(FPDF):
    """カスタムPDFクラス"""
    def __init__(self):
        super().__init__()
        self.add_font('Gothic', '', 'fonts/msgothic.ttc', uni=True)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        """ヘッダーの描画"""
        self.set_font('Gothic', size=8)
        self.cell(0, 10, f'生成日時: {datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S")}', 
                 align='R')
        self.ln(20)

    def footer(self):
        """フッターの描画"""
        self.set_y(-15)
        self.set_font('Gothic', size=8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

class DocumentTemplateCustomizer:
    """テンプレートカスタマイザ"""
    def __init__(self, template_manager: DocumentTemplateManager):
        self.template_manager = template_manager

    def create_custom_template(self, 
                             base_template: str,
                             modifications: Dict[str, Any]) -> str:
        """カスタムテンプレートの作成"""
        template = self.template_manager.get_template(base_template)
        custom_template = template.render(**modifications)
        return custom_template

    def register_template(self, name: str, template: str):
        """テンプレートの登録"""
        self.template_manager.register_custom_template(name, template)