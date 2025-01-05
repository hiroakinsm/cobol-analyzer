from tests.functional.mock_main import analyze_cobol_program

def test_main_analysis():
    # テスト用のプログラムID
    program_id = "PROG001"
    
    # 解析実行
    result = analyze_cobol_program(program_id)
    
    # 結果の検証
    assert result is not None
    assert hasattr(result, 'program_info')
    assert hasattr(result, 'call_statements')
    assert hasattr(result, 'copy_statements') 