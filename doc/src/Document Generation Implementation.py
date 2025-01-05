# /home/administrator/cobol-analyzer/src/documents/document_generation.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
from fpdf import FPDF
import json
import os

class DocumentGenerator:
    """ドキュメント生成処理"""

    def __init__(self, db_functions, template_path: str):
        self.db = db_functions
        self.template_path = template_path
        self.logger = logging.getLogger(__name__)

    async def generate_single_analysis_document(self, source_id: UUID) -> str:
        """単一ソース解析レポートの生成"""
        try:
            # 解析結果の取得
            analysis_results = await self.db.get_analysis_results(source_id)
            if not analysis_results:
                raise ValueError(f"Analysis results not found for source {source_id}")

            # プログラム情報の取得
            program_info = await self.db.get_source_info(source_id)

            # PDFドキュメントの生成
            pdf = AnalysisDocument()
            
            # 表紙の生成
            pdf.add_cover_page(
                title="ソースコード解析結果報告書",
                program_name=program_info["name"],
                analysis_date=datetime.utcnow()
            )

            # 目次の生成
            pdf.add_table_of_contents()

            # 各セクションの生成
            pdf.add_overview_section(program_info, analysis_results)
            pdf.add_structural_analysis_section(analysis_results)
            pdf.add_quality_analysis_section(analysis_results)
            pdf.add_security_analysis_section(analysis_results)
            pdf.add_recommendations_section(analysis_results)

            # 付録の生成
            pdf.add_appendix(analysis_results)

            # PDFの保存
            output_path = os.path.join(
                "output",
                f"analysis_report_{source_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            pdf.output(output_path)

            return output_path

        except Exception as e:
            self.logger.error(f"Document generation failed: {str(e)}")
            raise

    async def generate_summary_document(self, source_ids: List[UUID]) -> str:
        """サマリ解析レポートの生成"""
        try:
            # サマリ解析結果の取得
            summary_results = await self.db.get_summary_results(source_ids)
            if not summary_results:
                raise ValueError("Summary results not found")

            # プログラム群の情報取得
            program_infos = await self.db.get_source_infos(source_ids)

            # PDFドキュメントの生成
            pdf = SummaryDocument()
            
            # 表紙の生成
            pdf.add_cover_page(
                title="ソースコード解析サマリーレポート",
                program_count=len(source_ids),
                analysis_date=datetime.utcnow()
            )

            # 目次の生成
            pdf.add_table_of_contents()

            # 各セクションの生成
            pdf.add_summary_overview_section(program_infos, summary_results)
            pdf.add_trend_analysis_section(summary_results)
            pdf.add_pattern_analysis_section(summary_results)
            pdf.add_quality_distribution_section(summary_results)
            pdf.add_recommendations_section(summary_results)

            # 付録の生成
            pdf.add_program_details_appendix(program_infos)
            pdf.add_methodology_appendix()

            # PDFの保存
            output_path = os.path.join(
                "output",
                f"summary_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            pdf.output(output_path)

            return output_path

        except Exception as e:
            self.logger.error(f"Summary document generation failed: {str(e)}")
            raise

class AnalysisDocument(FPDF):
    """単一ソース解析レポートのPDF生成"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('Gothic', '', 'fonts/msgothic.ttc', uni=True)
        self.set_font('Gothic', '', 10)

    def add_cover_page(self, title: str, program_name: str, analysis_date: datetime):
        """表紙の生成"""
        self.add_page()
        self.set_font('Gothic', '', 24)
        self.cell(0, 20, title, 0, 1, 'C')
        self.set_font('Gothic', '', 16)
        self.cell(0, 20, f"対象プログラム: {program_name}", 0, 1, 'C')
        self.cell(0, 20, f"解析日時: {analysis_date.strftime('%Y年%m月%d日')}", 0, 1, 'C')

    def add_table_of_contents(self):
        """目次の生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "目次", 0, 1, 'L')
        self.set_font('Gothic', '', 10)
        
        # 目次項目の追加
        toc_items = [
            "1. 概要",
            "2. 構造解析",
            "3. 品質分析",
            "4. セキュリティ分析",
            "5. 改善提案",
            "付録A. 詳細メトリクス",
            "付録B. 解析手法"
        ]
        
        for item in toc_items:
            self.cell(0, 8, item, 0, 1, 'L')

    def add_overview_section(self, program_info: Dict[str, Any], analysis_results: Dict[str, Any]):
        """概要セクションの生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "1. 概要", 0, 1, 'L')
        self.set_font('Gothic', '', 10)

        # プログラム情報
        self.multi_cell(0, 10, f"""
        プログラム名: {program_info['name']}
        ソースコード行数: {analysis_results['analysis']['structure']['metrics']['total_lines']}
        作成日: {program_info.get('created_date', '不明')}
        最終更新日: {program_info.get('last_modified', '不明')}
        """)

        # 主要メトリクスのサマリー表
        self.create_metrics_table([
            ["メトリクス", "値", "評価"],
            ["複雑度", f"{analysis_results['analysis']['complexity']['metrics']['total_complexity']:.1f}", self._get_evaluation_text(analysis_results['analysis']['complexity']['evaluation'])],
            ["品質スコア", f"{analysis_results['analysis']['quality']['metrics']['overall_score']:.1f}", self._get_evaluation_text(analysis_results['analysis']['quality']['evaluation'])],
            ["セキュリティスコア", f"{analysis_results['analysis']['security']['metrics']['security_score']:.1f}", self._get_evaluation_text(analysis_results['analysis']['security']['evaluation'])]
        ])

    def add_structural_analysis_section(self, analysis_results: Dict[str, Any]):
        """構造解析セクションの生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "2. 構造解析", 0, 1, 'L')
        self.set_font('Gothic', '', 10)

        structure = analysis_results['analysis']['structure']

        # 構造の概要
        self.multi_cell(0, 10, """
        本セクションでは、プログラムの構造に関する解析結果を示します。
        DIVISIONの構成、SECTIONの分布、およびデータ構造の特徴について説明します。
        """)

        # 構造メトリクスの表示
        self.cell(0, 10, "2.1 構造メトリクス", 0, 1, 'L')
        self.create_metrics_table([
            ["指標", "値", "評価"],
            ["セクション数", str(structure['metrics']['total_sections']), self._get_evaluation_text(structure['metrics']['section_evaluation'])],
            ["平均セクションサイズ", f"{structure['metrics']['average_section_size']:.1f}", self._get_evaluation_text(structure['metrics']['size_evaluation'])],
            ["最大ネスト深度", str(structure['metrics']['max_nesting_depth']), self._get_evaluation_text(structure['metrics']['nesting_evaluation'])]
        ])

        # フローチャートの挿入
        if 'flow_chart' in structure:
            self.add_mermaid_diagram(structure['flow_chart'])

    def add_quality_analysis_section(self, analysis_results: Dict[str, Any]):
        """品質分析セクションの生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "3. 品質分析", 0, 1, 'L')
        self.set_font('Gothic', '', 10)

        quality = analysis_results['analysis']['quality']

        # 品質スコアの表示
        self.cell(0, 10, "3.1 品質スコア", 0, 1, 'L')
        self.create_metrics_table([
            ["品質指標", "スコア", "評価"],
            ["保守性", f"{quality['metrics']['maintainability_score']:.1f}", self._get_evaluation_text(quality['metrics']['maintainability_evaluation'])],
            ["信頼性", f"{quality['metrics']['reliability_score']:.1f}", self._get_evaluation_text(quality['metrics']['reliability_evaluation'])],
            ["モジュール性", f"{quality['metrics']['modularity_score']:.1f}", self._get_evaluation_text(quality['metrics']['modularity_evaluation'])]
        ])

        # 品質課題リストの表示
        self.cell(0, 10, "3.2 品質課題", 0, 1, 'L')
        for issue in quality['details']['issues']:
            self.multi_cell(0, 10, f"""
            ・{issue['description']}
              重要度: {issue['severity']}
              推奨対策: {issue['recommendation']}
            """)

    def add_security_analysis_section(self, analysis_results: Dict[str, Any]):
        """セキュリティ分析セクションの生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "4. セキュリティ分析", 0, 1, 'L')
        self.set_font('Gothic', '', 10)

        security = analysis_results['analysis']['security']

        # セキュリティ概要
        self.multi_cell(0, 10, f"""
        セキュリティスコア: {security['metrics']['security_score']:.1f}
        検出された脆弱性: {security['metrics']['total_vulnerabilities']}件
        重要度別内訳:
        - Critical: {security['metrics']['critical_vulnerabilities']}件
        - High: {security['metrics']['high_vulnerabilities']}件
        - Medium: {security['metrics']['medium_vulnerabilities']}件
        - Low: {security['metrics']['low_vulnerabilities']}件
        """)

        # 脆弱性詳細
        self.cell(0, 10, "4.1 検出された脆弱性", 0, 1, 'L')
        for vuln in security['details']['vulnerabilities']:
            self.multi_cell(0, 10, f"""
            ・{vuln['description']}
              重要度: {vuln['severity']}
              影響: {vuln['impact']}
              対策: {vuln['mitigation']}
            """)

    def create_metrics_table(self, data: List[List[str]]):
        """メトリクス表の生成"""
        col_widths = [60, 40, 40]
        for row in data:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 10, str(item), 1, 0, 'C')
            self.ln()

    def _get_evaluation_text(self, evaluation: str) -> str:
        """評価テキストの取得"""
        evaluation_map = {
            "high": "良好",
            "medium": "普通",
            "low": "要改善"
        }
        return evaluation_map.get(evaluation, "不明")

class SummaryDocument(FPDF):
    """サマリ解析レポートのPDF生成"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_font('Gothic', '', 'fonts/msgothic.ttc', uni=True)
        self.set_font('Gothic', '', 10)

    def add_cover_page(self, title: str, program_count: int, analysis_date: datetime):
        """表紙の生成"""
        self.add_page()
        self.set_font('Gothic', '', 24)
        self.cell(0, 20, title, 0, 1, 'C')
        self.set_font('Gothic', '', 16)
        self.cell(0, 20, f"対象プログラム数: {program_count}", 0, 1, 'C')
        self.cell(0, 20, f"解析日時: {analysis_date.strftime('%Y年%m月%d日')}", 0, 1, 'C')

    def add_summary_overview_section(self, program_infos: List[Dict[str, Any]], summary_results: Dict[str, Any]):
        """サマリ概要セクションの生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "1. 解析サマリー", 0, 1, 'L')
        self.set_font('Gothic', '', 10)

        # 全体サマリー
        overall = summary_results['summary']['overall']
        self.multi_cell(0, 10, f"""
        解析対象プログラム数: {len(program_infos)}
        総コード行数: {overall['size_metrics']['total_lines']:,}行
        平均品質スコア: {overall['quality_metrics']['average_quality']:.1f}
        平均セキュリティスコア: {overall['quality_metrics']['average_security']:.1f}
        """)

    def add_trend_analysis_section(self, summary_results: Dict[str, Any]):
        """トレンド分析セクションの生成"""
        self.add_page()
        self.set_font('Gothic', '', 16)
        self.cell(0, 10, "2. トレンド分析", 0, 1, 'L')
        self.set_font('Gothic', '', 10)

        trends = summary_results['summary']['trends']
        
        # 品質トレンド
        self.cell(0, 10, "2.1 品質指標の傾向", 0, 1, 'L')
        for metric, trend in trends['quality_trends'].items():
            self.multi_cell(0, 10, f"""
            ・{metric}
              傾向: {self._get_trend_text(trend['trend'])}
              平均値: {trend['average']:.1f}
              変動幅: {trend['distribution']['min']:.1f} - {trend['distribution']['max']:.1f}
            """)

    def _get_trend_text(self, trend: str) -> str:
        """トレンドテキストの取得"""
        trend_map = {
            "improving": "改善傾向",
            "stable": "安定",
            "degrading": "悪化傾向"
        }
        return trend_map.get(trend, "不明")