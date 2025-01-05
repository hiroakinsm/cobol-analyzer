# 単一ソース解析と複数ソース解析の統合
class IntegratedAnalysisService:
    def __init__(self, db_manager, ai_service):
        self.db_manager = db_manager
        self.ai_service = ai_service

    async def analyze_single_source(self, source_id):
        metadata = await self.db_manager.get_metadata(source_id)
        ast = await self.db_manager.get_ast(source_id)
        # 解析ロジックの実装

    async def analyze_multiple_sources(self, source_ids):
        results = []
        for source_id in source_ids:
            result = await self.analyze_single_source(source_id)
            results.append(result)
        # サマリ解析の実装 