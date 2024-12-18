```json
{
    "templates": {
        "analysis_question": {
            "template": """あなたはCOBOLコード解析の専門家です。以下のコンテキストに基づいて、質問に対する詳細な回答を提供してください。

コンテキスト:
{context}

解析結果:
{analysis_results}

質問: {question}

以下の点に注意して回答してください：
- 具体的なメトリクスや数値を含める
- 技術的な根拠を示す
- 必要に応じて改善提案を含める

回答：""",
            "parameters": ["context", "analysis_results", "question"],
            "max_tokens": 1000
        },

        "quality_analysis": {
            "template": """以下のCOBOLプログラムの品質メトリクスを分析し、詳細な評価を提供してください。

品質メトリクス:
{metrics}

評価基準:
{thresholds}

以下の観点から分析してください：
1. コードの複雑さ
2. 保守性
3. 再利用性
4. コーディング規約準拠度
5. 潜在的な問題点

分析結果：""",
            "parameters": ["metrics", "thresholds"],
            "max_tokens": 1500
        },

        "security_analysis": {
            "template": """COBOLプログラムのセキュリティ分析を実施してください。

プログラム情報:
{program_info}

セキュリティチェック結果:
{security_results}

以下の観点から評価してください：
1. データアクセスの安全性
2. 入力検証
3. エラーハンドリング
4. 機密情報の扱い
5. セキュリティ上の推奨事項

分析結果：""",
            "parameters": ["program_info", "security_results"],
            "max_tokens": 1200
        },

        "improvement_suggestions": {
            "template": """以下の解析結果に基づいて、COBOLプログラムの改善提案を生成してください。

解析結果:
{analysis_results}

ベストプラクティス:
{best_practices}

以下の形式で改善提案を提示してください：
1. 重要度（高/中/低）
2. 改善項目
3. 現状の問題点
4. 具体的な改善方法
5. 期待される効果

改善提案：""",
            "parameters": ["analysis_results", "best_practices"],
            "max_tokens": 2000
        },

        "document_summary": {
            "template": """COBOLプログラムの解析結果サマリーを生成してください。

プログラム情報:
{program_info}

解析結果:
{analysis_results}

以下の項目を含めてサマリーを作成してください：
1. プログラムの概要
2. 主要な指標
3. 重要な発見事項
4. 推奨アクション
5. 結論

サマリー：""",
            "parameters": ["program_info", "analysis_results"],
            "max_tokens": 1000
        },

        "technical_documentation": {
            "template": """COBOLプログラムの技術文書を生成してください。

プログラム構造:
{program_structure}

データ定義:
{data_definitions}

処理フロー:
{process_flow}

以下のセクションを含めて文書を作成してください：
1. プログラム構成
2. データ構造
3. 主要な処理ロジック
4. 外部インターフェース
5. 技術的な注意点

技術文書：""",
            "parameters": ["program_structure", "data_definitions", "process_flow"],
            "max_tokens": 2500
        },

        "metrics_explanation": {
            "template": """COBOLプログラムのメトリクスについて詳細な説明を提供してください。

メトリクスデータ:
{metrics_data}

基準値:
{baseline_metrics}

以下の観点から説明してください：
1. 各メトリクスの意味
2. 現在の値の評価
3. 基準値との比較
4. 改善が必要な領域
5. メトリクス改善のための推奨事項

説明：""",
            "parameters": ["metrics_data", "baseline_metrics"],
            "max_tokens": 1500
        }
    },

    "system_prompts": {
        "code_analysis": "You are a COBOL code analysis expert with deep knowledge of legacy systems and modern best practices.",
        "security_review": "You are a security expert specializing in COBOL application security and vulnerability assessment.",
        "documentation": "You are a technical writer specializing in COBOL system documentation and analysis reports.",
        "metrics_analysis": "You are a software metrics expert specializing in COBOL program quality and complexity analysis."
    },

    "response_formats": {
        "structured": {
            "format_type": "json",
            "schema": {
                "analysis": "string",
                "metrics": "object",
                "recommendations": "array",
                "risks": "array"
            }
        },
        "report": {
            "format_type": "markdown",
            "sections": [
                "summary",
                "details",
                "recommendations",
                "conclusions"
            ]
        }
    }
}
```