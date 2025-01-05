# /home/administrator/cobol-analyzer/src/web/dashboard/implementation.py
# /srv/cobol-analyzer/src/dashboard/dashboard_generation.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import UUID
import asyncio
import json
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass
from websockets import serve
import aioredis

@dataclass
class DashboardConfig:
    """ダッシュボード設定"""
    db_functions: Any
    template_path: Path
    websocket_host: str = "localhost"
    websocket_port: int = 8765
    update_interval: int = 30  # seconds
    redis_url: str = "redis://localhost"

class DashboardUpdateManager:
    """ダッシュボード更新管理"""
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)
        self.subscribers: Dict[str, List[Any]] = {}
        self.logger = logging.getLogger(__name__)

    async def publish_update(self, dashboard_id: str, data: Dict[str, Any]):
        """更新の配信"""
        try:
            await self.redis.publish(
                f"dashboard:{dashboard_id}",
                json.dumps(data)
            )
        except Exception as e:
            self.logger.error(f"Failed to publish update: {str(e)}")

    async def subscribe(self, dashboard_id: str, websocket):
        """更新の購読"""
        if dashboard_id not in self.subscribers:
            self.subscribers[dashboard_id] = []
        self.subscribers[dashboard_id].append(websocket)

    async def unsubscribe(self, dashboard_id: str, websocket):
        """購読解除"""
        if dashboard_id in self.subscribers:
            self.subscribers[dashboard_id].remove(websocket)

class DashboardGenerator:
    """ダッシュボード生成処理"""
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.db = config.db_functions
        self.update_manager = DashboardUpdateManager(config.redis_url)
        self.logger = logging.getLogger(__name__)
        self.update_tasks: Dict[str, asyncio.Task] = {}

    async def start_websocket_server(self):
        """WebSocketサーバーの起動"""
        async def handler(websocket, path):
            dashboard_id = path.split('/')[-1]
            await self.update_manager.subscribe(dashboard_id, websocket)
            try:
                async for message in websocket:
                    await self.handle_websocket_message(message, dashboard_id)
            finally:
                await self.update_manager.unsubscribe(dashboard_id, websocket)

        server = await serve(
            handler,
            self.config.websocket_host,
            self.config.websocket_port
        )
        return server

    async def handle_websocket_message(self, message: str, dashboard_id: str):
        """WebSocketメッセージの処理"""
        try:
            data = json.loads(message)
            if data.get("type") == "request_update":
                await self.trigger_dashboard_update(dashboard_id)
        except json.JSONDecodeError:
            self.logger.error("Invalid WebSocket message received")

    async def generate_single_source_dashboard(self, source_id: UUID) -> str:
        """単一ソース解析用ダッシュボードの生成"""
        try:
            # 解析結果の取得
            analysis_results = await self.db.get_analysis_results(source_id)
            if not analysis_results:
                raise ValueError(f"Analysis results not found for source {source_id}")

            # プログラム情報の取得
            program_info = await self.db.get_source_info(source_id)

            # ダッシュボードの構築
            dashboard_id = str(UUID())
            dashboard = {
                "id": dashboard_id,
                "type": "single_source",
                "metadata": {
                    "program_name": program_info["name"],
                    "analysis_date": datetime.utcnow().isoformat(),
                    "source_id": str(source_id)
                },
                "sections": await self._generate_dashboard_sections(analysis_results)
            }

            # 更新タスクの開始
            self.start_update_task(dashboard_id, source_id)

            return dashboard

        except Exception as e:
            self.logger.error(f"Dashboard generation failed: {str(e)}")
            raise

    async def _generate_dashboard_sections(self, 
                                        analysis_results: Dict[str, Any]
                                        ) -> Dict[str, Any]:
        """ダッシュボードセクションの生成"""
        return {
            "overview": await self._create_overview_section(analysis_results),
            "structure": await self._create_structure_section(analysis_results),
            "quality": await self._create_quality_section(analysis_results),
            "security": await self._create_security_section(analysis_results)
        }

    def start_update_task(self, dashboard_id: str, source_id: UUID):
        """更新タスクの開始"""
        task = asyncio.create_task(
            self._update_loop(dashboard_id, source_id)
        )
        self.update_tasks[dashboard_id] = task

    async def _update_loop(self, dashboard_id: str, source_id: UUID):
        """更新ループの実行"""
        try:
            while True:
                await asyncio.sleep(self.config.update_interval)
                await self.trigger_dashboard_update(dashboard_id, source_id)
        except asyncio.CancelledError:
            self.logger.info(f"Update loop cancelled for dashboard {dashboard_id}")
        except Exception as e:
            self.logger.error(f"Update loop error: {str(e)}")

    async def trigger_dashboard_update(self, dashboard_id: str, source_id: UUID):
        """ダッシュボード更新のトリガー"""
        try:
            # 最新の解析結果を取得
            analysis_results = await self.db.get_analysis_results(source_id)
            if not analysis_results:
                return

            # 更新されたセクションの生成
            updated_sections = await self._generate_dashboard_sections(
                analysis_results
            )

            # 更新の配信
            await self.update_manager.publish_update(
                dashboard_id,
                {
                    "type": "dashboard_update",
                    "sections": updated_sections,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f"Dashboard update failed: {str(e)}")

    async def _create_overview_section(self, 
                                     analysis_results: Dict[str, Any]
                                     ) -> Dict[str, Any]:
        """概要セクションの生成"""
        metrics = analysis_results.get("analysis", {})
        return {
            "type": "overview",
            "title": "プログラム概要",
            "components": [
                {
                    "type": "metrics_grid",
                    "title": "主要メトリクス",
                    "data": {
                        "総行数": metrics.get("structure", {}).get("metrics", {}).get("total_lines", 0),
                        "複雑度": metrics.get("complexity", {}).get("metrics", {}).get("total_complexity", 0),
                        "品質スコア": metrics.get("quality", {}).get("metrics", {}).get("overall_score", 0),
                        "セキュリティスコア": metrics.get("security", {}).get("metrics", {}).get("security_score", 0)
                    }
                },
                {
                    "type": "radar_chart",
                    "title": "品質指標",
                    "data": self._generate_quality_radar_data(metrics)
                }
            ]
        }

    def _generate_quality_radar_data(self, 
                                   metrics: Dict[str, Any]
                                   ) -> Dict[str, Any]:
        """品質レーダーチャートデータの生成"""
        return {
            "labels": ["複雑度", "保守性", "信頼性", "セキュリティ"],
            "values": [
                metrics.get("complexity", {}).get("metrics", {}).get("normalized_score", 0),
                metrics.get("quality", {}).get("metrics", {}).get("maintainability_score", 0),
                metrics.get("quality", {}).get("metrics", {}).get("reliability_score", 0),
                metrics.get("security", {}).get("metrics", {}).get("security_score", 0)
            ]
        }

    async def cleanup(self):
        """リソースのクリーンアップ"""
        for task in self.update_tasks.values():
            task.cancel()
        await asyncio.gather(*self.update_tasks.values(), return_exceptions=True)
        await self.update_manager.redis.close()