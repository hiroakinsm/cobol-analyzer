import pytest
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

class TestDataValidation:
    def setup_method(self):
        connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
        self.ast_repo = ASTRepository(connection_string=connection_string)
        self.metadata_repo = MetadataRepository(connection_string=connection_string)

    def test_ast_data_structure(self):
        # ASTデータの構造検証
        program_id = "PROG001"
        ast_data = self.ast_repo.get_ast(program_id)
        
        # データ構造の検証
        for node in ast_data:
            assert 'id' in node
            assert 'program_id' in node
            assert 'node_type' in node
            assert 'node_value' in node
            assert 'parent_id' in node

    def test_call_statement_content(self):
        # CALL文の内容検証
        program_id = "PROG001"
        call_statements = self.ast_repo.get_call_statements(program_id)
        
        for stmt in call_statements:
            assert stmt['node_type'] == 'CALL'
            assert stmt['program_id'] == program_id
            assert stmt['node_value'] is not None

    def test_copy_statement_content(self):
        # COPY文の内容検証
        program_id = "PROG001"
        copy_statements = self.ast_repo.get_copy_statements(program_id)
        
        for stmt in copy_statements:
            assert stmt['node_type'] == 'COPY'
            assert stmt['program_id'] == program_id
            assert stmt['node_value'] is not None

    def test_metadata_content(self):
        # メタデータの内容検証
        program_id = "PROG001"
        metadata = self.metadata_repo.get_metadata(program_id)
        
        assert metadata is not None
        assert metadata['program_id'] == program_id
        assert 'source_path' in metadata
        assert 'last_analyzed' in metadata 

    def test_ast_data_types(self):
        # ASTデータの型検証
        program_id = "PROG001"
        ast_data = self.ast_repo.get_ast(program_id)
        
        for node in ast_data:
            assert isinstance(node['id'], int)
            assert isinstance(node['program_id'], str)
            assert isinstance(node['node_type'], str)
            assert isinstance(node['node_value'], str)
            assert isinstance(node['parent_id'], (int, type(None)))  # NULLの場合もある

    def test_call_statement_values(self):
        # CALL文の値検証
        program_id = "PROG001"
        call_statements = self.ast_repo.get_call_statements(program_id)
        
        for stmt in call_statements:
            # 呼び出し先プログラム名の形式チェック
            called_program = stmt['node_value']
            assert called_program.isalnum()  # 英数字のみ
            assert len(called_program) <= 8  # COBOL標準の制限

    def test_ast_hierarchy(self):
        # AST階層構造の整合性検証
        program_id = "PROG001"
        ast_data = self.ast_repo.get_ast(program_id)
        
        # 親子関係の検証
        node_ids = {node['id'] for node in ast_data}
        for node in ast_data:
            if node['parent_id'] is not None:
                assert node['parent_id'] in node_ids

    def test_metadata_timestamps(self):
        # メタデータの日時検証
        program_id = "PROG001"
        metadata = self.metadata_repo.get_metadata(program_id)
        
        from datetime import datetime
        assert isinstance(metadata['last_analyzed'], datetime)
        assert metadata['last_analyzed'] <= datetime.now()

    def test_source_path_format(self):
        # ソースパスの形式検証
        program_id = "PROG001"
        metadata = self.metadata_repo.get_metadata(program_id)
        
        source_path = metadata['source_path']
        assert source_path.endswith(('.cbl', '.cob', '.CBL', '.COB'))
        assert '/' in source_path  # パス区切り文字の存在確認 