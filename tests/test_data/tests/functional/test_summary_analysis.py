from src.analyzer.program_analyzer import ProgramAnalyzer
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

class TestSummaryAnalysis:
    def setup_method(self):
        connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.ast_repo = ASTRepository(connection_string=connection_string)
        self.metadata_repo = MetadataRepository(connection_string=connection_string)
        self.analyzer = ProgramAnalyzer(self.ast_repo, self.metadata_repo)

    def test_program_dependency_summary(self):
        # プログラム間依存関係のサマリテスト
        program_ids = ["PROG001", "PROG002", "PROG003"]
        dependency_summary = self.analyzer.analyze_program_dependencies(program_ids)
        
        assert len(dependency_summary.programs) == 3
        assert all(prog.has_valid_calls for prog in dependency_summary.programs)

    def test_data_item_usage_summary(self):
        # データ項目使用状況のサマリテスト
        program_ids = ["PROG001", "PROG002", "PROG003"]
        usage_summary = self.analyzer.analyze_data_item_usage(program_ids)
        
        assert len(usage_summary.data_items) > 0
        assert usage_summary.total_items > 0 