# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/aggregator/implementation.py
# Analysis Result Aggregator Implementation.py

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
import logging
from pathlib import Path
from cachetools import TTLCache, LRUCache
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np

@dataclass
class AggregationConfig:
    """集約設定"""
    report_templates_path: Path
    output_path: Path
    rag_enabled: bool = True
    cache_results: bool = True
    max_workers: int = 4
    cache_ttl: int = 3600
    cache_size: int = 1000
    batch_size: int = 100

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
        
        # キャッシュの初期化
        self.result_cache = TTLCache(
            maxsize=self.config.cache_size,
            ttl=self.config.cache_ttl
        )
        self.computation_cache = LRUCache(maxsize=1000)
        
        # 並列処理用のリソース
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.semaphore = asyncio.Semaphore(10)

    async def aggregate_results(self,
                              source_id: UUID,
                              analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """解析結果の集約 - パフォーマンス最適化"""
        cache_key = f"{source_id}:{hash(str(analysis_results))}"
        
        # キャッシュチェック
        if self.config.cache_results:
            cached_result = self.result_cache.get(cache_key)
            if cached_result:
                self.logger.info(f"Cache hit for {source_id}")
                return cached_result

        try:
            # 並列処理による結果の処理
            processed_results = await self._process_results_parallel(
                analysis_results
            )
            
            # RAG分析の追加
            if self.config.rag_enabled:
                rag_analysis = await self._generate_rag_analysis(
                    processed_results
                )
                processed_results['rag_analysis'] = rag_analysis

            # キャッシュの更新
            if self.config.cache_results:
                self.result_cache[cache_key] = processed_results

            return processed_results

        except Exception as e:
            self.logger.error(f"Failed to aggregate results: {str(e)}")
            raise

    async def _process_results_parallel(self, 
                                      results: Dict[str, Any]) -> Dict[str, Any]:
        """並列処理による結果の処理"""
        async with self.semaphore:
            tasks = []
            for category, data in results.items():
                task = asyncio.create_task(
                    self._process_category(category, data)
                )
                tasks.append(task)
            
            processed_results = await asyncio.gather(*tasks)
            return self._combine_results(processed_results)

    async def _process_category(self, 
                              category: str, 
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """カテゴリ別の処理"""
        # 計算キャッシュのチェック
        cache_key = f"{category}:{hash(str(data))}"
        cached_result = self.computation_cache.get(cache_key)
        if cached_result:
            return cached_result

        # バッチ処理の実装
        if isinstance(data, list) and len(data) > self.config.batch_size:
            return await self._process_in_batches(category, data)

        # 重い計算は ThreadPoolExecutor で実行
        if self._is_heavy_computation(category):
            result = await self._run_in_thread(
                self._compute_category,
                category,
                data
            )
        else:
            result = await self._compute_category(category, data)

        # 結果をキャッシュ
        self.computation_cache[cache_key] = result
        return result

    async def _process_in_batches(self, 
                                category: str, 
                                data: List[Any]) -> List[Dict[str, Any]]:
        """バッチ処理の実装"""
        results = []
        for i in range(0, len(data), self.config.batch_size):
            batch = data[i:i + self.config.batch_size]
            batch_result = await self._process_category(category, batch)
            results.extend(batch_result)
        return results

    async def _run_in_thread(self, func, *args):
        """ThreadPoolExecutorでの実行"""
        return await asyncio.get_event_loop().run_in_executor(
            self.executor, func, *args
        )

    def _is_heavy_computation(self, category: str) -> bool:
        """重い計算かどうかの判定"""
        heavy_categories = {'metrics', 'security', 'complexity'}
        return category in heavy_categories

    async def _compute_category(self, 
                              category: str, 
                              data: Dict[str, Any]) -> Dict[str, Any]:
        """カテゴリ別の計算処理"""
        if category == 'metrics':
            return await self._compute_metrics(data)
        elif category == 'quality':
            return await self._compute_quality_metrics(data)
        elif category == 'security':
            return await self._compute_security_metrics(data)
        else:
            return await self._compute_general_metrics(data)

    async def _compute_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス計算の最適化実装"""
        try:
            # 数値計算の並列処理
            metrics_tasks = [
                self._calculate_complexity_metrics(data),
                self._calculate_maintainability_metrics(data),
                self._calculate_reliability_metrics(data)
            ]
            results = await asyncio.gather(*metrics_tasks)
            
            return {
                'complexity': results[0],
                'maintainability': results[1],
                'reliability': results[2],
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Metrics computation failed: {str(e)}")
            raise

    async def _calculate_complexity_metrics(self, 
                                         data: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度メトリクスの計算"""
        return await self._run_in_thread(
            self._compute_complexity,
            data
        )

    def _compute_complexity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """スレッドプール内での複雑度計算"""
        metrics = {}
        if 'statements' in data:
            metrics['cyclomatic'] = self._calculate_cyclomatic_complexity(
                data['statements']
            )
        if 'nesting' in data:
            metrics['nesting'] = self._calculate_nesting_depth(
                data['nesting']
            )
        return metrics

    async def generate_report(self,
                            source_id: UUID,
                            aggregated_results: Dict[str, Any]) -> str:
        """レポート生成の最適化実装"""
        try:
            # テンプレートの取得
            template = await self._get_report_template()
            
            # RAGを使用したレポート生成（非同期）
            report_content = await self.rag.generate_response(
                template,
                {"results": aggregated_results},
                max_tokens=2000
            )

            # レポートの処理と検証
            processed_report = await self.pipeline.process(
                report_content,
                ResponseType.DOCUMENTATION
            )

            # 非同期でレポートを保存
            report_path = await self._save_report(
                source_id,
                processed_report.content
            )

            return report_path

        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise

    async def _generate_rag_analysis(self, 
                                   results: Dict[str, Any]) -> Dict[str, Any]:
        """RAG分析の最適化実装"""
        try:
            # 分析用プロンプトの生成
            prompt = self._build_analysis_prompt(results)

            # 非同期でRAG分析を実行
            analysis_response = await self.rag.generate_response(
                prompt,
                {"context": results},
                max_tokens=1500
            )

            # 分析結果の処理
            processed_analysis = await self.pipeline.process(
                analysis_response,
                ResponseType.ANALYSIS
            )

            return processed_analysis.content

        except Exception as e:
            self.logger.error(f"RAG analysis failed: {str(e)}")
            return {"error": str(e)}

    def _build_analysis_prompt(self, results: Dict[str, Any]) -> str:
        """分析プロンプトの最適化"""
        metrics_summary = self._get_metrics_summary(results)
        security_summary = self._get_security_summary(results)

        return f"""以下の解析結果に基づいて、包括的な分析を提供してください：

メトリクス分析:
{metrics_summary}

セキュリティ分析:
{security_summary}

以下の観点から分析を行ってください：
1. 主要な発見事項と重要度
2. 具体的なリスクと問題点
3. 優先度を考慮した改善提案
4. 長期的な保守性への影響
5. セキュリティ対策の推奨事項
"""

    def _get_metrics_summary(self, results: Dict[str, Any]) -> str:
        """メトリクスサマリーの生成"""
        metrics = results.get('metrics', {})
        return '\n'.join([
            f"- 複雑度: {metrics.get('complexity', 'N/A')}",
            f"- 保守性: {metrics.get('maintainability', 'N/A')}",
            f"- 信頼性: {metrics.get('reliability', 'N/A')}"
        ])

    def _get_security_summary(self, results: Dict[str, Any]) -> str:
        """セキュリティサマリーの生成"""
        security = results.get('security', {})
        return '\n'.join([
            f"- リスクレベル: {security.get('risk_level', 'N/A')}",
            f"- 脆弱性数: {security.get('vulnerability_count', 'N/A')}",
            f"- 重要度: {security.get('severity', 'N/A')}"
        ])

    async def _save_report(self, 
                          source_id: UUID, 
                          content: str) -> str:
        """レポート保存の最適化"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.config.output_path / f"report_{source_id}_{timestamp}.md"
        
        async with aiofiles.open(report_path, "w") as f:
            await f.write(content)

        return str(report_path)

    def __del__(self):
        """リソースの適切なクリーンアップ"""
        self.executor.shutdown(wait=True)
