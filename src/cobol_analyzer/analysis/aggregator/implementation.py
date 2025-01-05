# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/aggregator/implementation.py

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
import logging
from pathlib import Path

@dataclass
class AggregationConfig:
    """集約設定"""
    report_templates_path: Path
    output_path: Path
    rag_enabled: bool = True
    cache_results: bool = True

class AnalysisResultAggregator:
    """解析結果の集約処理"""
    def __init__(self,
                 config: AggregationConfig,
                 rag_system: RAGSystem,
                 response_pipeline: ResponseProcessingPipeline):
        self.config = config
        self.rag = rag_system
        self.pipeline = response_pipeline
        self.logger = logging.getLogger(__name__)

    async def aggregate_results(self,
                              source_id: UUID,
                              analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """解析結果の集約"""
        try:
            # 各種解析結果の処理
            processed_results = {}
            
            # メトリクス解析結果の処理
            if 'metrics' in analysis_results:
                metrics = await self.pipeline.process(
                    analysis_results['metrics'],
                    ResponseType.METRICS
                )
                processed_results['metrics'] = metrics.content

            # セキュリティ解析結果の処理
            if 'security' in analysis_results:
                security = await self.pipeline.process(
                    analysis_results['security'],
                    ResponseType.SECURITY
                )
                processed_results['security'] = security.content

            # RAGによる分析の追加
            if self.config.rag_enabled:
                rag_analysis = await self._generate_rag_analysis(
                    processed_results
                )
                processed_results['rag_analysis'] = rag_analysis

            return processed_results

        except Exception as e:
            self.logger.error(f"Failed to aggregate results: {str(e)}")
            raise

    async def generate_report(self,
                            source_id: UUID,
                            aggregated_results: Dict[str, Any]) -> str:
        """報告書の生成"""
        try:
            # レポートテンプレートの取得
            template = await self._get_report_template()

            # RAGを使用したレポート生成
            report_content = await self.rag.generate_response(
                template,
                {"results": aggregated_results}
            )

            # レポートの処理と検証
            processed_report = await self.pipeline.process(
                report_content,
                ResponseType.DOCUMENTATION
            )

            # レポートの保存
            report_path = await self._save_report(
                source_id,
                processed_report.content
            )

            return report_path

        except Exception as e:
            self.logger.error(f"Failed to generate report: {str(e)}")
            raise

    async def _generate_rag_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """RAGによる追加分析の生成"""
        try:
            # 分析プロンプトの生成
            prompt = self._build_analysis_prompt(results)

            # RAGによる分析の実行
            analysis_response = await self.rag.generate_response(
                prompt,
                {"context": results}
            )

            # 分析結果の処理
            processed_analysis = await self.pipeline.process(
                analysis_response,
                ResponseType.ANALYSIS
            )

            return processed_analysis.content

        except Exception as e:
            self.logger.error(f"Failed to generate RAG analysis: {str(e)}")
            raise

    def _build_analysis_prompt(self, results: Dict[str, Any]) -> str:
        """分析プロンプトの構築"""
        return f"""以下の解析結果に基づいて、包括的な分析を提供してください：

メトリクス分析結果:
{results.get('metrics', {})}

セキュリティ分析結果:
{results.get('security', {})}

以下の観点から分析を行ってください：
1. 主要な発見事項
2. リスクと問題点
3. 改善提案
4. 優先度の提案
"""

    async def _get_report_template(self) -> str:
        """レポートテンプレートの取得"""
        template_path = self.config.report_templates_path / "analysis_report.md"
        with open(template_path) as f:
            return f.read()

    async def _save_report(self, source_id: UUID, content: str) -> str:
        """レポートの保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.config.output_path / f"report_{source_id}_{timestamp}.md"
        
        with open(report_path, "w") as f:
            f.write(content)

        return str(report_path)

class ReportGenerator:
    """報告書生成"""
    def __init__(self, aggregator: AnalysisResultAggregator):
        self.aggregator = aggregator
        self.logger = logging.getLogger(__name__)

    async def generate_comprehensive_report(self,
                                         source_id: UUID,
                                         analysis_results: Dict[str, Any]) -> str:
        """包括的な報告書の生成"""
        try:
            # 結果の集約
            aggregated_results = await self.aggregator.aggregate_results(
                source_id,
                analysis_results
            )

            # 報告書の生成
            report_path = await self.aggregator.generate_report(
                source_id,
                aggregated_results
            )

            return report_path

        except Exception as e:
            self.logger.error(f"Failed to generate comprehensive report: {str(e)}")
            raise

    async def generate_summary_report(self,
                                    source_ids: List[UUID],
                                    analysis_results: Dict[UUID, Dict[str, Any]]) -> str:
        """サマリーレポートの生成"""
        try:
            # 各ソースの結果を集約
            aggregated_results = {}
            for source_id in source_ids:
                if source_id in analysis_results:
                    result = await self.aggregator.aggregate_results(
                        source_id,
                        analysis_results[source_id]
                    )
                    aggregated_results[str(source_id)] = result

            # サマリーレポートの生成
            summary_template = await self._get_summary_template()
            summary_content = await self.aggregator.rag.generate_response(
                summary_template,
                {"results": aggregated_results}
            )

            # レポートの処理と保存
            processed_summary = await self.aggregator.pipeline.process(
                summary_content,
                ResponseType.DOCUMENTATION
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_path = self.aggregator.config.output_path / f"summary_{timestamp}.md"
            
            with open(summary_path, "w") as f:
                f.write(processed_summary.content)

            return str(summary_path)

        except Exception as e:
            self.logger.error(f"Failed to generate summary report: {str(e)}")
            raise

    async def _get_summary_template(self) -> str:
        """サマリーテンプレートの取得"""
        template_path = self.aggregator.config.report_templates_path / "summary_report.md"
        with open(template_path) as f:
            return f.read()
