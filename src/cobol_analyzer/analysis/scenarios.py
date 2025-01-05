# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/scenarios.py

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID
import pandas as pd
import json
from dataclasses import dataclass

@dataclass
class AnalysisContext:
    project_name: str
    source_dir: Path
    output_dir: Path
    config: Dict[str, Any]

class COBOLAnalysisScenario:
    """COBOL解析シナリオの基本クラス"""
    def __init__(self, client: AnalysisApiClient, context: AnalysisContext):
        self.client = client
        self.context = context
        self.logger = logging.getLogger(__name__)
        self.results: Dict[str, Any] = {}

    async def execute(self) -> Dict[str, Any]:
        """シナリオの実行"""
        try:
            await self.prepare()
            await self.run_analysis()
            await self.process_results()
            await self.generate_reports()
            return self.results
        except Exception as e:
            self.logger.error(f"Scenario execution failed: {str(e)}")
            raise

    async def prepare(self):
        """前準備"""
        try:
            # 出力ディレクトリの作成
            self.output_dir = self.context.output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # 解析対象のファイル確認
            source_files = list(self.context.source_dir.glob("*.cbl"))
            if not source_files:
                raise ValueError(f"No COBOL source files found in {self.context.source_dir}")

            # 解析設定の検証
            self._validate_analysis_config()

            # 一時ディレクトリのセットアップ
            self.temp_dir = self.output_dir / "temp"
            self.temp_dir.mkdir(exist_ok=True)

            # 出力サブディレクトリの作成
            (self.output_dir / "reports").mkdir(exist_ok=True)
            (self.output_dir / "metrics").mkdir(exist_ok=True)
            (self.output_dir / "visualizations").mkdir(exist_ok=True)

            # 解析対象ファイルのメタデータ収集
            self.source_metadata = {}
            for source_file in source_files:
                metadata = await self._collect_file_metadata(source_file)
                self.source_metadata[source_file.name] = metadata

            # 進捗ログの初期化
            self.logger.info(f"Analysis preparation completed for {len(source_files)} files")
            self.logger.info(f"Output directory: {self.output_dir}")

            return True

        except Exception as e:
            self.logger.error(f"Analysis preparation failed: {str(e)}")
            raise

    async def run_analysis(self):
        """解析の実行"""
        try:
            analysis_tasks = []
        
            # 各ソースファイルの解析タスクを作成
            for source_file, metadata in self.source_metadata.items():
                source_id = metadata['source_id']
            
                # 解析タスクの作成
                task = await self.client.start_single_analysis(
                    source_id=source_id,
                    analysis_types=[
                        "structure",
                        "quality",
                        "security",
                        "metrics"
                    ],
                    options=self.context.config.get("analysis_options", {})
                )
                analysis_tasks.append((source_file, task))

                self.logger.info(f"Started analysis for {source_file}")

            # 全タスクの完了を待機
            for source_file, task in analysis_tasks:
                try:
                    result = await self.client.wait_for_completion(
                        task.task_id,
                        timeout=self.context.config.get("task_timeout", 300)
                    )
                    self.results[source_file] = result
                    self.logger.info(f"Completed analysis for {source_file}")

                except Exception as e:
                    self.logger.error(f"Analysis failed for {source_file}: {str(e)}")
                    self.results[source_file] = {
                        "status": "failed",
                        "error": str(e)
                    }

            # 結果の検証
            successful_analyses = sum(
                1 for result in self.results.values()
                if result.get("status") != "failed"
            )
        
        if successful_analyses == 0:
            raise RuntimeError("All analyses failed")

        self.logger.info(
            f"Analysis completed: {successful_analyses}/{len(analysis_tasks)} successful"
        )

        except Exception as e:
            self.logger.error(f"Analysis execution failed: {str(e)}")
            raise

    async def process_results(self):
        """結果の処理"""
        try:
            # メトリクスの集計
            metrics_summary = self._aggregate_metrics()
            quality_issues = self._collect_quality_issues()
            security_issues = self._collect_security_issues()

            # ベンチマークとの比較
            benchmark_comparisons = await self._compare_with_benchmarks()

            # トレンド分析
            trend_analysis = self._analyze_trends()

            # パターン分析
            pattern_analysis = self._analyze_patterns()

            # 結果をデータベースに保存
            await self._store_analysis_results(
                metrics_summary,
                quality_issues,
                security_issues,
                benchmark_comparisons,
                trend_analysis,
                pattern_analysis
            )

            # 結果の集約
            self.processed_results = {
                "metrics": metrics_summary,
                "quality": {
                    "issues": quality_issues,
                    "benchmarks": benchmark_comparisons.get("quality", {}),
                    "trends": trend_analysis.get("quality", {})
                },
                "security": {
                    "issues": security_issues,
                    "benchmarks": benchmark_comparisons.get("security", {}),
                    "trends": trend_analysis.get("security", {})
                },
                "patterns": pattern_analysis,
                "summary": {
                    "total_files": len(self.results),
                    "processed_date": datetime.utcnow().isoformat(),
                    "overall_quality_score": self._calculate_overall_quality_score(metrics_summary),
                    "risk_level": self._determine_risk_level(security_issues),
                    "improvement_priorities": self._identify_improvement_priorities(quality_issues)
                }
            }

            # キャッシュの更新
            await self._update_result_cache()

            self.logger.info("Results processing completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Results processing failed: {str(e)}")
            raise

        async def _store_analysis_results(self, metrics_summary, quality_issues,
                                        security_issues, benchmark_comparisons,
                                        trend_analysis, pattern_analysis):
            """解析結果のデータベース保存"""
            try:
                # PostgreSQLへの保存
                async with self.context.db_manager.transaction() as conn:
                    await conn.execute("""
                        INSERT INTO analysis_results_partitioned (
                            result_id, task_id, source_id, analysis_type,
                            status, results, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, UUID(), self.context.task_id, self.context.source_id,
                        self.context.analysis_type, "completed",
                        json.dumps(self.processed_results), datetime.utcnow())

                # MongoDBへの保存
                result_document = {
                    "task_id": str(self.context.task_id),
                    "source_id": str(self.context.source_id),
                    "results": self.processed_results,
                    "created_at": datetime.utcnow()
                }
                await self.context.mongo_client.analysis_results.insert_one(result_document)

                self.logger.info("Analysis results stored successfully")

            except Exception as e:
                self.logger.error(f"Failed to store analysis results: {str(e)}")
                raise

        async def _update_result_cache(self):
            """結果キャッシュの更新"""
            try:
                cache_key = f"analysis_result_{self.context.task_id}"
                await self.context.cache_manager.set(
                    cache_key,
                    self.processed_results,
                    expire=3600  # 1時間
                )
                self.logger.info("Result cache updated successfully")

            except Exception as e:
                self.logger.error(f"Failed to update result cache: {str(e)}")
                # キャッシュの失敗は致命的ではないのでログのみ

    async def generate_reports(self):
        """レポートの生成"""
        try:
            # サマリーレポートの生成
            summary = {
                "project_name": self.context.project_name,
                "analysis_date": datetime.now().isoformat(),
                "total_files": len(self.results),
                "successful_analyses": sum(1 for r in self.results.values() 
                                        if r.get("status") != "failed"),
                "metrics_summary": self._calculate_metrics_summary(),
                "quality_summary": self._calculate_quality_summary(),
                "security_summary": self._calculate_security_summary()
            }

            # サマリーレポートの保存
            summary_path = self.output_dir / "reports" / "summary_report.json"
            with open(summary_path, "w") as f:
                json.dump(summary, f, indent=2)

            # 詳細レポートの生成
            for source_file, result in self.results.items():
                if result.get("status") != "failed":
                    # 詳細メトリクスレポート
                    metrics_path = self.output_dir / "metrics" / f"{source_file}_metrics.json"
                    with open(metrics_path, "w") as f:
                        json.dump(result.get("metrics", {}), f, indent=2)

                    # 品質レポート
                    quality_path = self.output_dir / "reports" / f"{source_file}_quality.json"
                    with open(quality_path, "w") as f:
                        json.dump(result.get("quality", {}), f, indent=2)

                    # 可視化の生成
                    self._generate_visualizations(source_file, result)

            # インデックスファイルの生成
            index_path = self.output_dir / "index.html"
            await self._generate_index_page(index_path)

            self.logger.info(f"Report generation completed: {self.output_dir}")

        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            raise

class SingleProjectAnalysis(COBOLAnalysisScenario):
    """単一プロジェクトの解析シナリオ"""
    async def run_analysis(self):
        # ソースファイルの収集
        source_files = list(self.context.source_dir.glob("*.cbl"))
        self.logger.info(f"Found {len(source_files)} COBOL source files")

        # 解析タスクの作成
        tasks = []
        for source_file in source_files:
            source_id = self._get_source_id(source_file)
            task = await self.client.start_single_analysis(
                source_id=source_id,
                analysis_types=[
                    "structure",
                    "quality",
                    "security",
                    "metrics"
                ],
                options=self.context.config.get("analysis_options", {})
            )
            tasks.append((source_file, task))

        # 結果の待機と収集
        for source_file, task in tasks:
            try:
                result = await self.client.wait_for_completion(
                    task.task_id,
                    timeout=300
                )
                self.results[source_file.name] = result
            except Exception as e:
                self.logger.error(f"Analysis failed for {source_file.name}: {str(e)}")

    async def process_results(self):
        # メトリクスの集計
        metrics_summary = self._aggregate_metrics()
        quality_issues = self._collect_quality_issues()
        security_issues = self._collect_security_issues()

        # 結果の保存
        await self._save_results(
            metrics_summary,
            quality_issues,
            security_issues
        )

    async def generate_reports(self):
        # サマリーレポートの生成
        await self._generate_summary_report()
        # 詳細レポートの生成
        await self._generate_detailed_reports()
        # メトリクスレポートの生成
        await self._generate_metrics_report()

    def _aggregate_metrics(self) -> pd.DataFrame:
        """メトリクスの集計"""
        metrics_data = []
        for file_name, result in self.results.items():
            metrics = result.get("metrics", {})
            metrics["file_name"] = file_name
            metrics_data.append(metrics)
        return pd.DataFrame(metrics_data)

    async def _generate_summary_report(self):
        """サマリーレポートの生成"""
        summary = {
            "project_name": self.context.project_name,
            "analysis_date": datetime.now().isoformat(),
            "total_files": len(self.results),
            "metrics_summary": self._calculate_metrics_summary(),
            "quality_summary": self._calculate_quality_summary(),
            "security_summary": self._calculate_security_summary()
        }

        report_path = self.output_dir / "summary_report.json"
        with open(report_path, "w") as f:
            json.dump(summary, f, indent=2)

class BatchProjectAnalysis(COBOLAnalysisScenario):
    """複数プロジェクトの一括解析シナリオ"""
    async def run_analysis(self):
        # プロジェクトごとのソース収集
        project_sources = {}
        for project_dir in self.context.source_dir.iterdir():
            if project_dir.is_dir():
                sources = list(project_dir.glob("*.cbl"))
                if sources:
                    project_sources[project_dir.name] = sources

        # プロジェクトごとのバッチ解析
        for project_name, sources in project_sources.items():
            source_ids = [self._get_source_id(src) for src in sources]
            try:
                task = await self.client.start_batch_analysis(
                    source_ids=source_ids,
                    analysis_types=[
                        "structure",
                        "quality",
                        "security",
                        "metrics"
                    ],
                    options=self.context.config.get("analysis_options", {})
                )
                result = await self.client.wait_for_completion(
                    task.task_id,
                    timeout=600
                )
                self.results[project_name] = result
            except Exception as e:
                self.logger.error(f"Batch analysis failed for {project_name}: {str(e)}")

class ComparisonAnalysis(COBOLAnalysisScenario):
    """プロジェクト間比較分析シナリオ"""
    def __init__(self, client: AnalysisApiClient, context: AnalysisContext, 
                 projects: List[str]):
        super().__init__(client, context)
        self.projects = projects

    async def run_analysis(self):
        # 各プロジェクトの解析
        for project in self.projects:
            project_dir = self.context.source_dir / project
            sources = list(project_dir.glob("*.cbl"))
            source_ids = [self._get_source_id(src) for src in sources]

            try:
                task = await self.client.start_batch_analysis(
                    source_ids=source_ids,
                    analysis_types=[
                        "structure",
                        "quality",
                        "security",
                        "metrics"
                    ]
                )
                result = await self.client.wait_for_completion(task.task_id)
                self.results[project] = result
            except Exception as e:
                self.logger.error(f"Analysis failed for project {project}: {str(e)}")

    async def generate_reports(self):
        # 比較レポートの生成
        await self._generate_comparison_report()
        # プロジェクト別詳細レポートの生成
        await self._generate_project_reports()
        # トレンド分析レポートの生成
        await self._generate_trend_report()

    async def _generate_comparison_report(self):
        """プロジェクト間の比較レポート生成"""
        comparison = {
            "metrics_comparison": self._compare_metrics(),
            "quality_comparison": self._compare_quality_scores(),
            "security_comparison": self._compare_security_levels(),
            "timestamp": datetime.now().isoformat()
        }

        report_path = self.output_dir / "comparison_report.json"
        with open(report_path, "w") as f:
            json.dump(comparison, f, indent=2)

# 使用例
async def main():
    config = AnalysisConfig(
        base_url="http://api.example.com",
        api_key="your-api-key"
    )

    context = AnalysisContext(
        project_name="COBOL-Legacy-System",
        source_dir=Path("/path/to/sources"),
        output_dir=Path("/path/to/output"),
        config={
            "analysis_options": {
                "quality_threshold": 0.8,
                "security_level": "high"
            }
        }
    )

    async with AnalysisApiClient(config) as client:
        # 単一プロジェクト解析
        single_analysis = SingleProjectAnalysis(client, context)
        await single_analysis.execute()

        # 複数プロジェクト解析
        batch_analysis = BatchProjectAnalysis(client, context)
        await batch_analysis.execute()

        # 比較分析
        comparison = ComparisonAnalysis(
            client, 
            context,
            projects=["ProjectA", "ProjectB", "ProjectC"]
        )
        await comparison.execute()

if __name__ == "__main__":
    asyncio.run(main())