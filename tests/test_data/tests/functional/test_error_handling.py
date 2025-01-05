import pytest
from src.db.error_handler import DatabaseError, RetryableError
from src.db.ast_repository import ASTRepository

class TestErrorHandling:
    def setup_method(self):
        self.connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.ast_repo = ASTRepository(connection_string=self.connection_string)

    def test_retry_mechanism(self):
        # 接続エラーが発生した場合のリトライ
        bad_connection = "postgresql://invalid:invalid@localhost/invalid"
        repo = ASTRepository(connection_string=bad_connection)
        
        with pytest.raises(RetryableError) as exc_info:
            repo.get_ast("PROG001")
        assert "Failed after 3 attempts" in str(exc_info.value)

    def test_error_logging(self, caplog):
        # エラーログの出力テスト
        bad_connection = "postgresql://invalid:invalid@localhost/invalid"
        repo = ASTRepository(connection_string=bad_connection)
        
        with pytest.raises(RetryableError):
            repo.get_ast("PROG001")
        
        assert "Database connection error" in caplog.text
        assert "Failed after 3 attempts" in caplog.text 

    def test_copy_statements_error(self):
        # COPY文取得時のエラー処理テスト
        bad_connection = "postgresql://invalid:invalid@localhost/invalid"
        repo = ASTRepository(connection_string=bad_connection)
        
        with pytest.raises(RetryableError) as exc_info:
            repo.get_copy_statements("PROG001")
        assert "Failed after 3 attempts" in str(exc_info.value)

    def test_validation_error_handling(self):
        # バリデーションエラーのテスト
        invalid_node = {}  # 必須フィールドが欠落
        
        with pytest.raises(DatabaseError) as exc_info:
            self.ast_repo.validate_node_data(invalid_node)
        assert "Required field" in str(exc_info.value)

    def test_invalid_node_type_handling(self):
        # 不正なノードタイプのテスト
        with pytest.raises(DatabaseError) as exc_info:
            self.ast_repo.get_ast_nodes_by_type("PROG001", "INVALID_TYPE")
        assert "Query failed" in str(exc_info.value) 