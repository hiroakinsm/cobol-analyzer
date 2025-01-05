import pytest
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

class TestDatabaseAccess:
    def setup_method(self):
        connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.ast_repo = ASTRepository(connection_string=connection_string)
        self.metadata_repo = MetadataRepository(connection_string=connection_string)

    def test_ast_connection(self):
        # データベース接続テスト
        program_id = "PROG001"
        ast_data = self.ast_repo.get_ast(program_id)
        assert ast_data is not None

    def test_metadata_connection(self):
        # メタデータ接続テスト
        program_id = "PROG001"
        metadata = self.metadata_repo.get_metadata(program_id)
        assert metadata is not None

    def test_call_statement_retrieval(self):
        # CALL文取得テスト
        program_id = "PROG001"
        call_statements = self.ast_repo.get_call_statements(program_id)
        assert isinstance(call_statements, list)

    def test_copy_statement_retrieval(self):
        # COPY文取得テスト
        program_id = "PROG001"
        copy_statements = self.ast_repo.get_copy_statements(program_id)
        assert isinstance(copy_statements, list) 