```python
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID
import asyncio
from collections import defaultdict

class ResultIntegrationType(Enum):
    SINGLE_SOURCE = "single_source"
    MULTI_SOURCE = "multi_source"
    SUMMARY = "summary"

@dataclass
class IntegrationResult:
    integration_id: UUID
    integration_type: ResultIntegrationType
    source_ids: List[UUID]
    analysis_results: Dict[AnalysisType, AnalysisResult]
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    created_at: datetime = datetime.utcnow()

class ResultIntegrator:
    """解析結果の統合処理"""
    def __init__(self, engine_manager: AnalysisEngineManager, 
                 cache_manager: CacheManager,
                 mongo_client: Any, 
                 postgres_client: Any):
        self.engine_manager = engine_manager
        self.cache_manager = cache_manager
        self.mongo_client = mongo_client
        self.postgres_client = postgres_client
        self.result_validators: Dict[AnalysisType, ResultValidator] = {}

    async def integrate_results(self, integration_id: UUID, 
                              source_ids: List[UUID],
                              analysis_types: List[AnalysisType],
                              integration_type: ResultIntegrationType) -> IntegrationResult:
        """結果の統合実行"""
        try:
            # キャッシュチェック
            cached_result = self.cache_manager.get_integration_result(
                integration_id, integration_type
            )
            if cached_result:
                return cached_result

            # 結果の収集
            analysis_results = await self._collect_analysis_results(
                source_ids, analysis_types
            )

            # 結果の検証
            self._validate_results(analysis_results)

            # 結果の統合
            integration_result = await self._integrate_analysis_results(
                integration_id,
                integration_type,
                source_ids,
                analysis_results
            )

            # 結果の保存
            await self._save_integration_result(integration_result)

            # キャッシュの更新
            self.cache_manager.cache_integration_result(
                integration_result
            )

            return integration_result

        except Exception as e:
            logging.error(f"Integration failed: {str(e)}")
            raise

    async def _collect_analysis_results(self, 
                                      source_ids: List[UUID],
                                      analysis_types: List[AnalysisType]
                                      ) -> Dict[AnalysisType, List[AnalysisResult]]:
        """各解析結果の収集"""
        results = defaultdict(list)
        tasks = []

        for source_id in source_ids:
            for analysis_type in analysis_types:
                tasks.append(self._get_analysis_result(source_id, analysis_type))

        completed_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in completed_results:
            if isinstance(result, Exception):
                logging.error(f"Analysis failed: {str(result)}")
                continue
            if result:
                results[result.analysis_type].append(result)

        return results

    async def _integrate_analysis_results(self,
                                        integration_id: UUID,
                                        integration_type: ResultIntegrationType,
                                        source_ids: List[UUID],
                                        analysis_results: Dict[AnalysisType, List[AnalysisResult]]
                                        ) -> IntegrationResult:
        """解析結果の統合処理"""
        summary = {}
        metrics = {}

        # 解析タイプごとの結果を統合
        for analysis_type, results in analysis_results.items():
            summary[analysis_type.value] = self._create_type_summary(results)
            metrics[analysis_type.value] = self._aggregate_metrics(results)

        return IntegrationResult(
            integration_id=integration_id,
            integration_type=integration_type,
            source_ids=source_ids,
            analysis_results=analysis_results,
            summary=summary,
            metrics=metrics
        )

    def _create_type_summary(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """解析タイプごとのサマリー作成"""
        return {
            "total_count": len(results),
            "success_count": len([r for r in results if r.status == AnalysisStatus.SUCCESS]),
            "error_count": len([r for r in results if r.status == AnalysisStatus.FAILED]),
            "average_execution_time": sum(r.execution_time for r in results) / len(results)
        }

    def _aggregate_metrics(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """メトリクスの集約"""
        aggregated_metrics = defaultdict(list)
        
        for result in results:
            for metric_name, value in result.results.get("metrics", {}).items():
                aggregated_metrics[metric_name].append(value)

        return {
            metric_name: {
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values)
            }
            for metric_name, values in aggregated_metrics.items()
        }

class CacheManager:
    """キャッシュ管理"""
    def __init__(self, cache_ttl: timedelta = timedelta(hours=1)):
        self.cache: Dict[UUID, IntegrationResult] = {}
        self.cache_ttl = cache_ttl
        self.cache_timestamps: Dict[UUID, datetime] = {}

    def get_integration_result(self, 
                             integration_id: UUID,
                             integration_type: ResultIntegrationType
                             ) -> Optional[IntegrationResult]:
        """キャッシュされた結果の取得"""
        if integration_id in self.cache:
            if self._is_cache_valid(integration_id):
                return self.cache[integration_id]
            else:
                self._remove_from_cache(integration_id)
        return None

    def cache_integration_result(self, result: IntegrationResult) -> None:
        """結果のキャッシュ"""
        self.cache[result.integration_id] = result
        self.cache_timestamps[result.integration_id] = datetime.utcnow()

    def _is_cache_valid(self, integration_id: UUID) -> bool:
        """キャッシュの有効性チェック"""
        if integration_id not in self.cache_timestamps:
            return False
        cache_age = datetime.utcnow() - self.cache_timestamps[integration_id]
        return cache_age < self.cache_ttl

class ResultValidator:
    """結果の検証"""
    def validate_results(self, results: Dict[AnalysisType, List[AnalysisResult]]) -> bool:
        """結果の妥当性検証"""
        all_valid = True
        for analysis_type, type_results in results.items():
            for result in type_results:
                if not self._validate_single_result(result):
                    all_valid = False
                    logging.error(f"Invalid result found for {analysis_type}: {result.analysis_id}")
        return all_valid

    def _validate_single_result(self, result: AnalysisResult) -> bool:
        """個別結果の検証"""
        return (
            self._validate_structure(result) and
            self._validate_metrics(result) and
            self._validate_consistency(result)
        )

    def _validate_structure(self, result: AnalysisResult) -> bool:
        """結果構造の検証"""
        required_fields = {"analysis_id", "source_id", "results", "status"}
        return all(hasattr(result, field) for field in required_fields)

    def _validate_metrics(self, result: AnalysisResult) -> bool:
        """メトリクスの検証"""
        if "metrics" not in result.results:
            return True
        return all(
            isinstance(value, (int, float))
            for value in result.results["metrics"].values()
        )

    def _validate_consistency(self, result: AnalysisResult) -> bool:
        """結果の整合性検証"""
        if result.status == AnalysisStatus.SUCCESS:
            return len(result.errors) == 0
        return len(result.errors) > 0
```