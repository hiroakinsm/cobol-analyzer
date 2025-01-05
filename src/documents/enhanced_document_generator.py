# /home/administrator/cobol-analyzer/src/documents/enhanced_document_generator.py

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
import logging
from pathlib import Path
from abc import ABC, abstractmethod

@dataclass
class ReportingConfig:
    """レポート生成設定"""
    templates_path: Path
    output_path: Path
    chart_templates_path: Path
    comparison_base_path: Path
    group_config: Dict[str, List[str]]  # グループとサブグループの設定
    display_formats: Dict[str, str]     # 表示形式の設定
    filtering_rules: Dict[str, Any]     # 抽出ルールの設定

class AnalysisReportBase(ABC):
    """解析レポートの基底クラス"""
    def __init__(self,
                 config: ReportingConfig,
                 rag_system: RAGSystem,
                 response_pipeline: ResponseProcessingPipeline):
        self.config = config
        self.rag = rag_system
        self.pipeline = response_pipeline
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    async def generate_report(self) -> str:
        """レポート生成の抽象メソッド"""
        pass

    async def _create_mermaid_diagram(self, data: Dict[str, Any], diagram_type: str) -> str:
        """Mermaidダイアグラムの生成"""
        pass

    async def _create_chart(self, data: Dict[str, Any], chart_type: str) -> str:
        """チャートの生成"""
        pass

    async def _format_comparison_table(self, current: Dict[str, Any], base: Dict[str, Any]) -> str:
        """比較表の生成"""
        pass

class SingleSourceReport(AnalysisReportBase):
    """単一ソース解析レポート"""
    async def generate_report(self, source_id: UUID, analysis_results: Dict[str, Any]) -> str:
        """単一ソース解析レポートの生成"""
        try:
            structured_results = await self._structure_results(analysis_results)
            filtered_results = await self._apply_filters(structured_results)
            
            report_sections = []
            
            # 基本情報セクション
            report_sections.append(await self._create_basic_info_section(source_id))
            
            # グループごとの解析結果
            for group, subgroups in self.config.group_config.items():
                group_section = await self._create_group_section(
                    group,
                    subgroups,
                    filtered_results
                )
                report_sections.append(group_section)
            
            # 比較分析セクション
            comparison_section = await self._create_comparison_section(
                filtered_results
            )
            report_sections.append(comparison_section)
            
            # レポートの結合と保存
            report_path = await self._save_report(
                source_id,
                "\n\n".join(report_sections)
            )
            
            return report_path
            
        except Exception as e:
            self.logger.error(f"Failed to generate single source report: {str(e)}")
            raise

    async def _create_group_section(self,
                                  group: str,
                                  subgroups: List[str],
                                  results: Dict[str, Any]) -> str:
        """グループセクションの作成"""
        section_parts = [f"## {group}"]
        
        for subgroup in subgroups:
            if subgroup_data := results.get(subgroup):
                # サブグループの内容生成
                content = await self._generate_subgroup_content(
                    subgroup,
                    subgroup_data
                )
                section_parts.append(content)
                
                # 指定された表示形式でのビジュアル生成
                if display_format := self.config.display_formats.get(subgroup):
                    visual = await self._create_visual(
                        subgroup_data,
                        display_format
                    )
                    section_parts.append(visual)
        
        return "\n\n".join(section_parts)

    async def _create_visual(self,
                           data: Dict[str, Any],
                           format_type: str) -> str:
        """ビジュアル要素の生成"""
        if format_type == "mermaid":
            return await self._create_mermaid_diagram(data, "flowchart")
        elif format_type == "chart":
            return await self._create_chart(data, "bar")
        elif format_type == "table":
            return self._create_markdown_table(data)
        else:
            return ""

class MultiSourceReport(AnalysisReportBase):
    """複数ソース解析レポート"""
    async def generate_report(self,
                            source_ids: List[UUID],
                            analysis_results: Dict[UUID, Dict[str, Any]]) -> str:
        """複数ソース解析レポートの生成"""
        try:
            # 結果の構造化と集約
            aggregated_results = await self._aggregate_results(
                source_ids,
                analysis_results
            )
            
            report_sections = []
            
            # プロジェクト概要セクション
            report_sections.append(await self._create_project_summary(
                source_ids,
                aggregated_results
            ))
            
            # グループごとのサマリー
            for group, subgroups in self.config.group_config.items():
                group_summary = await self._create_group_summary(
                    group,
                    subgroups,
                    aggregated_results
                )
                report_sections.append(group_summary)
            
            # 全体の傾向分析
            trend_analysis = await self._create_trend_analysis(
                aggregated_results
            )
            report_sections.append(trend_analysis)
            
            # レポートの保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = self.config.output_path / f"summary_report_{timestamp}.md"
            
            with open(report_path, "w") as f:
                f.write("\n\n".join(report_sections))
            
            return str(report_path)
            
        except Exception as e:
            self.logger.error(f"Failed to generate multi-source report: {str(e)}")
            raise

    async def _create_group_summary(self,
                                  group: str,
                                  subgroups: List[str],
                                  results: Dict[str, Any]) -> str:
        """グループサマリーの作成"""
        summary_parts = [f"## {group} Summary"]
        
        for subgroup in subgroups:
            if subgroup_data := results.get(subgroup):
                # 統計情報の生成
                stats = await self._calculate_statistics(
                    subgroup_data
                )
                summary_parts.append(self._format_statistics(stats))
                
                # トレンドの可視化
                if self.config.display_formats.get(subgroup) == "chart":
                    trend_chart = await self._create_chart(
                        subgroup_data,
                        "line"
                    )
                    summary_parts.append(trend_chart)
        
        return "\n\n".join(summary_parts)

    async def _create_trend_analysis(self, results: Dict[str, Any]) -> str:
        """傾向分析セクションの作成"""
        analysis_parts = ["## Trend Analysis"]
        
        # RAGによる傾向分析
        trend_prompt = self._build_trend_analysis_prompt(results)
        trend_analysis = await self.rag.generate_response(
            trend_prompt,
            {"results": results}
        )
        analysis_parts.append(trend_analysis)
        
        # 可視化の追加
        visualizations = await self._create_trend_visualizations(results)
        analysis_parts.append(visualizations)
        
        return "\n\n".join(analysis_parts)

class ReportGenerationService:
    """レポート生成サービス"""
    def __init__(self, config: ReportingConfig):
        self.config = config
        self.single_source_report = SingleSourceReport(
            config,
            rag_system,
            response_pipeline
        )
        self.multi_source_report = MultiSourceReport(
            config,
            rag_system,
            response_pipeline
        )

    async def generate_single_source_report(self,
                                          source_id: UUID,
                                          analysis_results: Dict[str, Any]) -> str:
        """単一ソース解析レポートの生成"""
        return await self.single_source_report.generate_report(
            source_id,
            analysis_results
        )

    async def generate_summary_report(self,
                                    selected_source_ids: List[UUID],
                                    analysis_results: Dict[UUID, Dict[str, Any]]) -> str:
        """選択されたソースのサマリーレポート生成"""
        # 選択されたソースの結果のみを抽出
        selected_results = {
            source_id: results
            for source_id, results in analysis_results.items()
            if source_id in selected_source_ids
        }

        # 選択されたソースが存在しない場合はエラー
        if not selected_results:
            raise ValueError("No analysis results found for selected sources")

        return await self.multi_source_report.generate_report(
            selected_source_ids,
            selected_results
        )
        """解析レポートの生成"""
        if source_id and not source_ids:
            # 単一ソース解析レポート
            return await self.single_source_report.generate_report(
                source_id,
                analysis_results
            )
        elif source_ids:
            # 複数ソース解析レポート
            return await self.multi_source_report.generate_report(
                source_ids,
                analysis_results
            )
        else:
            raise ValueError("Either source_id or source_ids must be provided")
