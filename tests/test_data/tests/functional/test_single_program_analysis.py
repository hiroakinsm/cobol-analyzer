from src.analyzer.program_analyzer import ProgramAnalyzer
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

class TestSingleProgramAnalysis:
    def setup_method(self):
        # テスト用DBへの接続設定
        self.ast_repo = ASTRepository(connection_string="postgresql://test_db")
        self.metadata_repo = MetadataRepository(connection_string="postgresql://test_db")
        self.analyzer = ProgramAnalyzer(self.ast_repo, self.metadata_repo)

    def test_program_id_extraction(self):
        # 単一プログラムのID抽出テスト
        program_id = "PROG001"
        result = self.analyzer.extract_program_id(program_id)
        assert result.program_id == "PROG001"
        assert result.is_valid == True

    def test_call_statement_analysis(self):
        # CALL文解析テスト
        program_id = "PROG001"
        call_statements = self.analyzer.analyze_call_statements(program_id)
        assert len(call_statements) > 0
        assert all(stmt.calling_program == "PROG001" for stmt in call_statements)

    def test_copy_statement_analysis(self):
        # COPY文解析テスト
        program_id = "PROG001"
        copy_statements = self.analyzer.analyze_copy_statements(program_id)
        assert len(copy_statements) > 0
        assert all(stmt.program_id == "PROG001" for stmt in copy_statements) 