```python
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
        self.output_dir = self.context.output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def run_analysis(self):
        """解析の実行"""
        pass

    async def process_results(self):
        """結果の処理"""
        pass

    async def generate_reports(self):
        """レポートの生成"""
        pass

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
```