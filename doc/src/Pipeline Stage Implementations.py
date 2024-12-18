from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import asyncio
import logging
from datetime import datetime

class AnalysisStage(PipelineStage, ABC):
    """解析ステージの基底クラス"""
    def __init__(self, name: str, task_manager: TaskManager):
        super().__init__(name, task_manager)
        self.recovery_handlers: Dict[str, Callable] = {}

    @abstractmethod
    async def analyze(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """解析処理の実装"""
        pass

    async def process(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """ステージの処理を実行"""
        try:
            # 前回の結果をチェック
            cached_result = await self._check_cache(context)
            if cached_result:
                return cached_result

            # 解析を実行
            result = await self.analyze(context, data)

            # 結果をキャッシュ
            await self._cache_result(context, result)

            return result

        except Exception as e:
            # エラーハンドリング
            await self.handle_error(context, e)
            # リカバリーハンドラーがあれば実行
            if handler := self.recovery_handlers.get(type(e).__name__):
                return await handler(context, data, e)
            raise

    async def _check_cache(self, context: TaskContext) -> Optional[Dict[str, Any]]:
        """キャッシュのチェック"""
        return await self.task_manager.db.get_stage_result(
            context.task_id,
            self.name
        )

    async def _cache_result(self, context: TaskContext, 
                           result: Dict[str, Any]) -> None:
        """結果のキャッシュ"""
        await self.task_manager.db.store_stage_result(
            context.task_id,
            self.name,
            result
        )

class ASTParsingStage(AnalysisStage):
    """ASTパース処理ステージ"""
    def __init__(self, task_manager: TaskManager):
        super().__init__("ast_parsing", task_manager)

    async def analyze(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """AST解析の実行"""
        source_code = data.get("source_code")
        if not source_code:
            raise PipelineError("Source code not found", context.task_id)

        try:
            ast_data = await self._parse_ast(source_code)
            return {
                "ast_data": ast_data,
                "source_info": data
            }
        except Exception as e:
            raise PipelineError(
                f"AST parsing failed: {str(e)}",
                context.task_id
            )

    async def _parse_ast(self, source_code: str) -> Dict[str, Any]:
        """AST解析の実装"""
        # 実際のAST解析処理をここに実装
        pass

class MetricsAnalysisStage(AnalysisStage):
    """メトリクス解析ステージ"""
    def __init__(self, task_manager: TaskManager):
        super().__init__("metrics_analysis", task_manager)

    async def analyze(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクス解析の実行"""
        ast_data = data.get("ast_data")
        if not ast_data:
            raise PipelineError("AST data not found", context.task_id)

        try:
            metrics = await self._calculate_metrics(ast_data)
            return {
                **data,
                "metrics": metrics
            }
        except Exception as e:
            raise PipelineError(
                f"Metrics analysis failed: {str(e)}",
                context.task_id
            )

    async def _calculate_metrics(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスの計算"""
        # 実際のメトリクス計算処理をここに実装
        pass

class SecurityAnalysisStage(AnalysisStage):
    """セキュリティ解析ステージ"""
    def __init__(self, task_manager: TaskManager):
        super().__init__("security_analysis", task_manager)

    async def analyze(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ解析の実行"""
        ast_data = data.get("ast_data")
        if not ast_data:
            raise PipelineError("AST data not found", context.task_id)

        try:
            security_results = await self._analyze_security(ast_data)
            return {
                **data,
                "security": security_results
            }
        except Exception as e:
            raise PipelineError(
                f"Security analysis failed: {str(e)}",
                context.task_id
            )

    async def _analyze_security(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ解析の実装"""
        # 実際のセキュリティ解析処理をここに実装
        pass

class ResultAggregationStage(AnalysisStage):
    """結果集約ステージ"""
    def __init__(self, task_manager: TaskManager):
        super().__init__("result_aggregation", task_manager)

    async def analyze(self, context: TaskContext, 
                     data: Dict[str, Any]) -> Dict[str, Any]:
        """結果の集約"""
        required_keys = ["ast_data", "metrics", "security"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            raise PipelineError(
                f"Missing required data: {missing_keys}",
                context.task_id
            )

        try:
            aggregated_results = await self._aggregate_results(data)
            return {
                "task_id": context.task_id,
                "source_id": context.source_id,
                "results": aggregated_results,
                "completed_at": datetime.utcnow()
            }
        except Exception as e:
            raise PipelineError(
                f"Result aggregation failed: {str(e)}",
                context.task_id
            )

    async def _aggregate_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """結果の集約処理"""
        return {
            "summary": {
                "metrics_summary": self._summarize_metrics(data["metrics"]),
                "security_summary": self._summarize_security(data["security"]),
                "overall_quality": self._calculate_overall_quality(data)
            },
            "details": {
                "ast_analysis": data["ast_data"],
                "metrics_analysis": data["metrics"],
                "security_analysis": data["security"]
            },
            "recommendations": await self._generate_recommendations(data)
        }

    def _summarize_metrics(self, metrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスのサマリー生成"""
        return {
            "complexity": metrics_data.get("complexity", {}),
            "maintainability": metrics_data.get("maintainability", {}),
            "quality_score": metrics_data.get("quality_score", 0)
        }

    def _summarize_security(self, security_data: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ結果のサマリー生成"""
        return {
            "risk_level": security_data.get("risk_level", "unknown"),
            "vulnerabilities_count": len(security_data.get("vulnerabilities", [])),
            "critical_issues": len([v for v in security_data.get("vulnerabilities", []) 
                                  if v.get("severity") == "critical"])
        }

    def _calculate_overall_quality(self, data: Dict[str, Any]) -> float:
        """全体的な品質スコアの計算"""
        metrics_score = data["metrics"].get("quality_score", 0)
        security_score = 100 - (len(data["security"].get("vulnerabilities", [])) * 10)
        security_score = max(0, min(100, security_score))
        
        return (metrics_score * 0.6 + security_score * 0.4)

    async def _generate_recommendations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """改善推奨事項の生成"""
        recommendations = []
        
        # メトリクスベースの推奨事項
        if metrics := data.get("metrics"):
            if metrics.get("complexity", {}).get("cyclomatic", 0) > 10:
                recommendations.append({
                    "type": "complexity",
                    "severity": "high",
                    "description": "高い循環的複雑度を検出しました",
                    "suggestion": "メソッドの分割を検討してください"
                })

        # セキュリティベースの推奨事項
        if security := data.get("security"):
            for vuln in security.get("vulnerabilities", []):
                recommendations.append({
                    "type": "security",
                    "severity": vuln.get("severity", "medium"),
                    "description": vuln.get("description"),
                    "suggestion": vuln.get("mitigation")
                })

        return recommendations