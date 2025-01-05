from src.analyzer.models import ProgramInfo, DependencySummary, UsageSummary

class ProgramAnalyzer:
    def __init__(self, ast_repo, metadata_repo):
        self.ast_repo = ast_repo
        self.metadata_repo = metadata_repo

    def extract_program_id(self, program_id):
        # プログラムIDの抽出と検証
        return ProgramInfo(program_id=program_id, is_valid=True)

    def analyze_call_statements(self, program_id):
        # CALL文の解析
        return self.ast_repo.get_call_statements(program_id)

    def analyze_copy_statements(self, program_id):
        # COPY文の解析
        return self.ast_repo.get_copy_statements(program_id)

    def analyze_program_dependencies(self, program_ids):
        # プログラム間依存関係の解析
        return DependencySummary(programs=[])

    def analyze_data_item_usage(self, program_ids):
        # データ項目使用状況の解析
        return UsageSummary(data_items=[], total_items=0) 