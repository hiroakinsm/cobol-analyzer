import pytest
import psycopg2
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

class TestDatabaseErrorCases:
    def setup_method(self):
        self.valid_connection = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.invalid_connection = "postgresql://invalid_user:invalid_pass@172.16.0.13/invalid_db"
        
        self.ast_repo = ASTRepository(connection_string=self.valid_connection)
        self.metadata_repo = MetadataRepository(connection_string=self.valid_connection)

    def test_nonexistent_program_id(self):
        # 存在しないプログラムIDのテスト
        program_id = "NONEXISTENT"
        
        # ASTデータ
        ast_data = self.ast_repo.get_ast(program_id)
        assert len(ast_data) == 0
        
        # メタデータ
        metadata = self.metadata_repo.get_metadata(program_id)
        assert metadata is None

    def test_invalid_program_id_format(self):
        # 不正なプログラムID形式のテスト
        invalid_ids = ["", " ", "あいうえお", "PROG-001", "TOOLONG12"]
        
        for invalid_id in invalid_ids:
            with pytest.raises(ValueError):
                self.ast_repo.validate_program_id(invalid_id)

    def test_database_connection_error(self):
        # DB接続エラーのテスト
        bad_repo = ASTRepository(connection_string=self.invalid_connection)
        
        with pytest.raises(psycopg2.OperationalError):
            bad_repo.get_ast("PROG001")

    def test_malformed_data(self):
        # 不正なデータ形式のテスト
        program_id = "PROG001"
        
        # node_typeが不正な値の場合
        invalid_nodes = self.ast_repo.get_ast_nodes_by_type(program_id, "INVALID_TYPE")
        assert len(invalid_nodes) == 0
        
        # 必須フィールドが欠落している場合
        with pytest.raises(KeyError):
            self.ast_repo.validate_node_data({})

    def test_concurrent_access(self):
        # 同時アクセスのテスト
        program_id = "PROG001"
        
        # 複数のクエリを同時実行
        results = []
        with self.ast_repo._get_connection() as conn:
            with conn.cursor() as cur1, conn.cursor() as cur2:
                cur1.execute("SELECT * FROM ast_nodes WHERE program_id = %s", (program_id,))
                cur2.execute("SELECT * FROM ast_nodes WHERE program_id = %s", (program_id,))
                results.extend([cur1.fetchall(), cur2.fetchall()])
        
        assert len(results) == 2
        assert results[0] == results[1]  # 結果が一致することを確認 