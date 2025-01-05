# /home/administrator/cobol-analyzer/src/documents/enhanced_document_generator.py
# /srv/cobol-analyzer/src/report/enhanced_report_generator.py

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
import logging
from pathlib import Path
from abc import ABC, abstractmethod
import json
import yaml

@dataclass
class ReportingConfig:
    """レポート生成設定"""
    templates_path: Path
    output_path: Path
    chart_templates_path: Path
    comparison_base_path: Path
    format_config_path: Path
    formats: List[str] = field(default_factory=lambda: ["markdown", "pdf", "html", "docx"])
    enable_charts: bool = True
    enable_comparisons: bool = True
    chart_library: str = "chartjs"

class ReportFormatManager:
    """レポートフォーマット管理"""
    def __init__(self, config: ReportingConfig):
        self.config = config
        self.format_config = self._load_format_config()
        self.custom_formats: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)

    def _load_format_config(self) -> Dict[str, Any]:
        """フォーマット設定の読み込み"""
        with open(self.config.format_config_path) as f:
            return yaml.safe_load(f)

    def register_custom_format(self, name: str, format_config: Dict[str, Any]):
        """カスタムフォーマットの登録"""
        self.custom_formats[name] = format_config

    def get_format_config(self, format_name: str) -> Dict[str, Any]:
        """フォーマット設定の取得"""
        if format_name in self.custom_formats:
            return self.custom_formats[format_name]
        return self.format_config.get(format_name, {})

class ChartGenerator:
    """チャート生成"""
    def __init__(self, config: ReportingConfig):
        self.config = config
        self.templates = self._load_chart_templates()

    def _load_chart_templates(self) -> Dict[str, str]:
        """チャートテンプレートの読み込み"""
        templates = {}
        template_files = self.config.chart_templates_path.glob("*.json")
        for template_file in template_files:
            with open(template_file) as f:
                templates[template_file.stem] = json.load(f)
        return templates

    async def generate_chart(self, 
                           chart_type: str, 
                           data: Dict[str, Any],
                           custom_config: Optional[Dict[str, Any]] = None) -> str:
        """チャートの生成"""
        template = self.templates.get(chart_type)
        if not template:
            raise ValueError(f"Chart template not found: {chart_type}")

        config = {**template, **(custom_config or {})}
        return self._render_chart(config, data)

    def _render_chart(self, config: Dict[str, Any], data: Dict[str, Any]) -> str:
        """チャートのレンダリング"""
        if self.config.chart_library == "chartjs":
            return self._render_chartjs(config, data)
        elif self.config.chart_library == "plotly":
            return self._render_plotly(config, data)
        else:
            raise ValueError(f"Unsupported chart library: {self.config.chart_library}")

class ReportGenerator:
    """レポート生成"""
    def __init__(self,
                 config: ReportingConfig,
                 rag_system: Optional[Any] = None,
                 response_pipeline: Optional[Any] = None):
        self.config = config
        self.rag = rag_system
        self.pipeline = response_pipeline
        self.format_manager = ReportFormatManager(config)
        self.chart_generator = ChartGenerator(config)
        self.logger = logging.getLogger(__name__)

    async def generate_report(self,
                            analysis_results: Dict[str, Any],
                            format_name: str,
                            custom_config: Optional[Dict[str, Any]] = None) -> str:
        """レポートの生成"""
        try:
            format_config = self.format_manager.get_format_config(format_name)
            if custom_config:
                format_config.update(custom_config)

            # セクションの生成
            sections = await self._generate_sections(
                analysis_results,
                format_config
            )

            # チャートの生成
            if self.config.enable_charts:
                charts = await self._generate_charts(analysis_results)
                sections['visualizations'] = charts

            # 比較分析
            if self.config.enable_comparisons:
                comparison = await self._generate_comparison(analysis_results)
                sections['comparison'] = comparison

            # レポートの生成
            report_content = await self._format_report(
                sections,
                format_name,
                format_config
            )

            # レポートの保存
            output_path = await self._save_report(
                report_content,
                format_name
            )

            return output_path

        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise

    async def _generate_sections(self,
                               analysis_results: Dict[str, Any],
                               format_config: Dict[str, Any]) -> Dict[str, Any]:
        """レポートセクションの生成"""
        sections = {
            'summary': await self._generate_summary(analysis_results),
            'details': await self._generate_details(
                analysis_results,
                format_config.get('detail_level', 'full')
            ),
            'metrics': await self._generate_metrics(
                analysis_results,
                format_config.get('metrics_config', {})
            ),
            'recommendations': await self._generate_recommendations(analysis_results)
        }

        if format_config.get('include_appendix', True):
            sections['appendix'] = await self._generate_appendix(analysis_results)

        return sections

    async def _generate_charts(self,
                             analysis_results: Dict[str, Any]) -> Dict[str, str]:
        """チャートの生成"""
        charts = {}

        # 複雑度チャート
        if complexity_data := analysis_results.get('complexity'):
            charts['complexity'] = await self.chart_generator.generate_chart(
                'complexity_radar',
                complexity_data
            )

        # 品質メトリクスチャート
        if quality_data := analysis_results.get('quality'):
            charts['quality'] = await self.chart_generator.generate_chart(
                'quality_bar',
                quality_data
            )

        # トレンドチャート
        if trend_data := analysis_results.get('trends'):
            charts['trends'] = await self.chart_generator.generate_chart(
                'trend_line',
                trend_data
            )

        return charts

    async def _generate_comparison(self,
                                 analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """比較分析の生成"""
        comparison_base = await self._load_comparison_base()
        
        return {
            'metrics_comparison': self._compare_metrics(
                analysis_results.get('metrics', {}),
                comparison_base.get('metrics', {})
            ),
            'quality_comparison': self._compare_quality(
                analysis_results.get('quality', {}),
                comparison_base.get('quality', {})
            ),
            'trend_analysis': self._analyze_trends(
                analysis_results.get('trends', []),
                comparison_base.get('trends', [])
            )
        }

    async def _format_report(self,
                           sections: Dict[str, Any],
                           format_name: str,
                           format_config: Dict[str, Any]) -> str:
        """レポートのフォーマット"""
        if format_name == 'markdown':
            return self._format_markdown(sections, format_config)
        elif format_name == 'html':
            return self._format_html(sections, format_config)
        elif format_name == 'pdf':
            return await self._format_pdf(sections, format_config)
        elif format_name == 'docx':
            return await self._format_docx(sections, format_config)
        else:
            raise ValueError(f"Unsupported format: {format_name}")

    async def _save_report(self,
                          content: str,
                          format_name: str) -> str:
        """レポートの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.{format_name}"
        output_path = self.config.output_path / filename

        with open(output_path, 'w' if format_name in ['markdown', 'html'] else 'wb') as f:
            f.write(content)

        return str(output_path)

    def _load_comparison_base(self) -> Dict[str, Any]:
        """比較基準データの読み込み"""
        with open(self.config.comparison_base_path) as f:
            return json.load(f)

    def _compare_metrics(self, current: Dict[str, Any], base: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスの比較"""
        return {
            metric: {
                'current': current_value,
                'base': base.get(metric),
                'change': self._calculate_change(
                    current_value,
                    base.get(metric)
                )
            }
            for metric, current_value in current.items()
        }

    def _calculate_change(self,
                         current: Union[int, float],
                         base: Union[int, float]) -> float:
        """変化率の計算"""
        if not base:
            return 0.0
        return ((current - base) / base) * 100