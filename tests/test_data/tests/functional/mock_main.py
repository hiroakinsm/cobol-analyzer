from src.analyzer.program_analyzer import ProgramAnalyzer
from src.db.ast_repository import ASTRepository
from src.db.metadata_repository import MetadataRepository

def analyze_cobol_program(program_id):
    # テスト用のデータベース接続設定
    connection_string = "postgresql://cobana_admin:Kanami1001!@172.16.0.13/cobol_analysis_db"
    
    # リポジトリの初期化
    ast_repo = ASTRepository(connection_string=connection_string)
    metadata_repo = MetadataRepository(connection_string=connection_string)
    
    # アナライザーの初期化
    analyzer = ProgramAnalyzer(ast_repo, metadata_repo)
    
    # 解析結果を格納する構造体
    class AnalysisResult:
        def __init__(self):
            self.program_info = None
            self.call_statements = None
            self.copy_statements = None
    
    # 解析の実行
    result = AnalysisResult()
    result.program_info = analyzer.extract_program_id(program_id)
    result.call_statements = analyzer.analyze_call_statements(program_id)
    result.copy_statements = analyzer.analyze_copy_statements(program_id)
    
    return result 