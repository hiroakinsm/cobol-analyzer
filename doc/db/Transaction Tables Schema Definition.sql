-- 解析タスク管理
CREATE TABLE analysis_tasks (
    task_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_type VARCHAR(50) NOT NULL,       -- 'single', 'summary', 'security', 'benchmark'
    status VARCHAR(20) NOT NULL,          -- 'pending', 'running', 'completed', 'failed'
    priority INTEGER DEFAULT 0,
    source_path TEXT NOT NULL,
    analysis_config JSONB NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 解析対象ソースファイル
CREATE TABLE analysis_sources (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES analysis_tasks(task_id),
    file_path TEXT NOT NULL,
    file_type VARCHAR(20) NOT NULL,       -- 'COBOL', 'JCL', 'ASM'
    file_hash VARCHAR(64) NOT NULL,       -- SHA-256
    file_size BIGINT NOT NULL,
    encoding VARCHAR(20),
    line_count INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 解析ログ
CREATE TABLE analysis_logs (
    log_id BIGSERIAL PRIMARY KEY,
    task_id UUID REFERENCES analysis_tasks(task_id),
    source_id UUID REFERENCES analysis_sources(source_id),
    log_level VARCHAR(10) NOT NULL,       -- 'INFO', 'WARN', 'ERROR'
    component VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 解析結果メタデータ
CREATE TABLE analysis_results (
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES analysis_tasks(task_id),
    source_id UUID REFERENCES analysis_sources(source_id),
    result_type VARCHAR(50) NOT NULL,     -- 'ast', 'metrics', 'security', 'benchmark'
    status VARCHAR(20) NOT NULL,          -- 'success', 'partial', 'failed'
    mongodb_collection VARCHAR(100),       -- MongoDB内の結果格納コレクション名
    mongodb_document_id VARCHAR(100),      -- MongoDB内のドキュメントID
    summary_data JSONB,                   -- 主要な結果サマリ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ベンチマーク結果
CREATE TABLE benchmark_results (
    benchmark_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES analysis_tasks(task_id),
    source_id UUID REFERENCES analysis_sources(source_id),
    benchmark_id INTEGER REFERENCES benchmark_master(benchmark_id),
    measured_value NUMERIC,
    evaluation_result VARCHAR(20),        -- 'good', 'warning', 'error'
    score NUMERIC,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- セキュリティ評価結果
CREATE TABLE security_results (
    security_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES analysis_tasks(task_id),
    source_id UUID REFERENCES analysis_sources(source_id),
    vulnerability_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,        -- 'critical', 'high', 'medium', 'low'
    cvss_score NUMERIC,
    cve_ids TEXT[],
    description TEXT,
    recommendation TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 解析タスク依存関係
CREATE TABLE task_dependencies (
    dependency_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES analysis_tasks(task_id),
    dependent_task_id UUID REFERENCES analysis_tasks(task_id),
    dependency_type VARCHAR(50) NOT NULL,  -- 'requires', 'triggers', 'blocks'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, dependent_task_id)
);

-- インデックス作成
CREATE INDEX idx_analysis_tasks_status ON analysis_tasks(status);
CREATE INDEX idx_analysis_tasks_type ON analysis_tasks(task_type);
CREATE INDEX idx_analysis_sources_task ON analysis_sources(task_id);
CREATE INDEX idx_analysis_logs_task ON analysis_logs(task_id);
CREATE INDEX idx_analysis_logs_level ON analysis_logs(log_level);
CREATE INDEX idx_analysis_results_task ON analysis_results(task_id);
CREATE INDEX idx_analysis_results_type ON analysis_results(result_type);
CREATE INDEX idx_benchmark_results_task ON benchmark_results(task_id);
CREATE INDEX idx_security_results_task ON security_results(task_id);
CREATE INDEX idx_security_results_severity ON security_results(severity);