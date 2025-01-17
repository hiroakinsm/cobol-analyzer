# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/usecases.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4
import logging
import asyncio

@dataclass
class AnalysisRequest:
    source_id: UUID
    analysis_types: List[AnalysisType]
    options: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    callback_url: Optional[str] = None

@dataclass
class BatchAnalysisRequest:
    source_ids: List[UUID]
    analysis_types: List[AnalysisType]
    options: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    callback_url: Optional[str] = None

class SingleSourceAnalysisUseCase:
    """単一ソース解析のユースケース"""
    def __init__(self, 
                 engine_manager: AnalysisEngineManager,
                 result_integrator: ResultIntegrator,
                 ast_accessor: ASTAccessor):
        self.engine_manager = engine_manager
        self.result_integrator = result_integrator
        self.ast_accessor = ast_accessor
        self.logger = logging.getLogger(__name__)

    async def execute(self, request: AnalysisRequest) -> IntegrationResult:
        """単一ソース解析の実行"""
        try:
            # ASTの取得
            ast = self.ast_accessor.get_ast(request.source_id)
            if not ast:
                raise ValueError(f"AST not found for source_id: {request.source_id}")

            # 解析実行
            integration_id = uuid4()
            integration_result = await self.result_integrator.integrate_results(
                integration_id=integration_id,
                source_ids=[request.source_id],
                analysis_types=request.analysis_types,
                integration_type=ResultIntegrationType.SINGLE_SOURCE
            )

            # コールバック通知
            if request.callback_url:
                await self._notify_completion(request.callback_url, integration_result)

            return integration_result

        except Exception as e:
            self.logger.error(f"Single source analysis failed: {str(e)}")
            raise

class BatchAnalysisUseCase:
    """複数ソース解析のユースケース"""
    def __init__(self, 
                 engine_manager: AnalysisEngineManager,
                 result_integrator: ResultIntegrator,
                 ast_accessor: ASTAccessor):
        self.engine_manager = engine_manager
        self.result_integrator = result_integrator
        self.ast_accessor = ast_accessor
        self.logger = logging.getLogger(__name__)

    async def execute(self, request: BatchAnalysisRequest) -> IntegrationResult:
        """複数ソース解析の実行"""
        try:
            # ASTの一括取得
            asts = await self._fetch_all_asts(request.source_ids)
            if not asts:
                raise ValueError("No ASTs found for the specified sources")

            # 解析実行
            integration_id = uuid4()
            integration_result = await self.result_integrator.integrate_results(
                integration_id=integration_id,
                source_ids=request.source_ids,
                analysis_types=request.analysis_types,
                integration_type=ResultIntegrationType.MULTI_SOURCE
            )

            # コールバック通知
            if request.callback_url:
                await self._notify_completion(request.callback_url, integration_result)

            return integration_result

        except Exception as e:
            self.logger.error(f"Batch analysis failed: {str(e)}")
            raise

    async def _fetch_all_asts(self, source_ids: List[UUID]) -> Dict[UUID, Dict[str, Any]]:
        """複数ASTの一括取得"""
        tasks = [self.ast_accessor.get_ast(source_id) for source_id in source_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            source_id: ast
            for source_id, ast in zip(source_ids, results)
            if not isinstance(ast, Exception) and ast is not None
        }

class SummaryAnalysisUseCase:
    """サマリ解析のユースケース"""
    def __init__(self, 
                 engine_manager: AnalysisEngineManager,
                 result_integrator: ResultIntegrator,
                 ast_accessor: ASTAccessor):
        self.engine_manager = engine_manager
        self.result_integrator = result_integrator
        self.ast_accessor = ast_accessor
        self.logger = logging.getLogger(__name__)

    async def execute(self, request: BatchAnalysisRequest) -> IntegrationResult:
        """サマリ解析の実行"""
        try:
            # 既存の解析結果の取得
            existing_results = await self._get_existing_results(
                request.source_ids,
                request.analysis_types
            )

            # 不足している解析の実行
            missing_analyses = self._identify_missing_analyses(
                request.source_ids,
                request.analysis_types,
                existing_results
            )

            if missing_analyses:
                await self._execute_missing_analyses(missing_analyses)

            # サマリ結果の統合
            integration_id = uuid4()
            integration_result = await self.result_integrator.integrate_results(
                integration_id=integration_id,
                source_ids=request.source_ids,
                analysis_types=request.analysis_types,
                integration_type=ResultIntegrationType.SUMMARY
            )

            # コールバック通知
            if request.callback_url:
                await self._notify_completion(request.callback_url, integration_result)

            return integration_result

        except Exception as e:
            self.logger.error(f"Summary analysis failed: {str(e)}")
            raise

    async def _get_existing_results(self, 
                              source_ids: List[UUID],
                              analysis_types: List[AnalysisType]
                              ) -> Dict[UUID, Dict[AnalysisType, AnalysisResult]]:
    """既存の解析結果を取得"""
    try:
        existing_results: Dict[UUID, Dict[AnalysisType, AnalysisResult]] = defaultdict(dict)
        
        # 各ソースIDに対する結果を取得
        for source_id in source_ids:
            for analysis_type in analysis_types:
                results = await self.result_integrator.get_results(
                    source_id=source_id,
                    analysis_type=analysis_type
                )
                if results:
                    existing_results[source_id][analysis_type] = results[-1]  # 最新の結果を使用

        self.logger.info(f"Retrieved existing results for {len(existing_results)} sources")
        return existing_results

    except Exception as e:
        self.logger.error(f"Failed to get existing results: {str(e)}")
        raise

    async def _identify_missing_analyses(self,
                                   source_ids: List[UUID],
                                   required_types: List[AnalysisType],
                                   existing_results: Dict[UUID, Dict[AnalysisType, AnalysisResult]]
                                   ) -> Dict[UUID, List[AnalysisType]]:
    """不足している解析を特定"""
    try:
        missing_analyses: Dict[UUID, List[AnalysisType]] = defaultdict(list)
        
        for source_id in source_ids:
            # 各ソースの既存結果を取得
            source_results = existing_results.get(source_id, {})
            
            # 要求された解析タイプと比較して不足を特定
            for required_type in required_types:
                if required_type not in source_results:
                    missing_analyses[source_id].append(required_type)
                else:
                    # 既存の結果が失敗している場合も再解析が必要
                    result = source_results[required_type]
                    if result.status == AnalysisStatus.FAILED:
                        missing_analyses[source_id].append(required_type)

        self.logger.info(f"Identified missing analyses: {dict(missing_analyses)}")
        return missing_analyses

    except Exception as e:
        self.logger.error(f"Failed to identify missing analyses: {str(e)}")
        raise

    async def _execute_missing_analyses(self,
                                  missing_analyses: Dict[UUID, List[AnalysisType]]
                                  ) -> None:
    """不足している解析を実行"""
    try:
        # 解析タスクを生成
        tasks = []
        for source_id, analysis_types in missing_analyses.items():
            for analysis_type in analysis_types:
                task = AnalysisTask(
                    task_id=uuid4(),
                    source_id=source_id,
                    analysis_type=analysis_type,
                    priority=0  # サマリ解析の一部として実行されるため低優先度
                )
                tasks.append(task)

        # タスクを並列実行
        async with asyncio.TaskGroup() as group:
            for task in tasks:
                group.create_task(
                    self._execute_single_analysis(task)
                )

        self.logger.info(f"Completed execution of {len(tasks)} missing analyses")

    except* asyncio.ExceptionGroup as eg:
        # 複数のタスクの例外をまとめて処理
        failed_tasks = [
            ex.task_id for ex in eg.exceptions 
            if isinstance(ex, AnalysisError)
        ]
        self.logger.error(f"Some analyses failed: {failed_tasks}")
        raise AnalysisError(f"Failed to complete missing analyses: {str(eg)}")

    except Exception as e:
        self.logger.error(f"Failed to execute missing analyses: {str(e)}")
        raise

    async def _execute_single_analysis(self, task: AnalysisTask) -> None:
        """単一の解析タスクを実行"""
        try:
            # ASTの取得
            ast = await self.ast_accessor.get_ast(task.source_id)
            if not ast:
                raise ValueError(f"AST not found for source {task.source_id}")

            # 解析エンジンの選択
            engine = self.engine_manager.get_engine(task.analysis_type)
            if not engine:
                raise ValueError(f"No engine found for type {task.analysis_type}")

            # 解析の実行
            result = await engine.analyze(
                ast=ast,
                context={
                    "task_id": task.task_id,
                    "source_id": task.source_id,
                    "type": task.analysis_type
                }
            )

            # 結果の保存
            await self.result_integrator.store_result(result)

            # タスク状態の更新
            await self.engine_manager.update_task_status(
                task.task_id,
                AnalysisStatus.COMPLETED if result.status == AnalysisStatus.SUCCESS
                else AnalysisStatus.FAILED
            )

        except Exception as e:
            self.logger.error(f"Analysis task {task.task_id} failed: {str(e)}")
            await self.engine_manager.update_task_status(
                task.task_id,
                AnalysisStatus.FAILED,
                error_message=str(e)
            )
            raise

class AnalysisUseCaseFactory:
    """解析ユースケースのファクトリ"""
    def __init__(self,
                 engine_manager: AnalysisEngineManager,
                 result_integrator: ResultIntegrator,
                 ast_accessor: ASTAccessor):
        self.engine_manager = engine_manager
        self.result_integrator = result_integrator
        self.ast_accessor = ast_accessor

    def create_single_source_usecase(self) -> SingleSourceAnalysisUseCase:
        return SingleSourceAnalysisUseCase(
            self.engine_manager,
            self.result_integrator,
            self.ast_accessor
        )

    def create_batch_usecase(self) -> BatchAnalysisUseCase:
        return BatchAnalysisUseCase(
            self.engine_manager,
            self.result_integrator,
            self.ast_accessor
        )

    def create_summary_usecase(self) -> SummaryAnalysisUseCase:
        return SummaryAnalysisUseCase(
            self.engine_manager,
            self.result_integrator,
            self.ast_accessor
        )