-- 環境マスター：システム動作環境の設定
CREATE TABLE environment_master (
    environment_id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,  -- 'server', 'database', 'external_system' etc
    sub_category VARCHAR(50),
    name VARCHAR(100) NOT NULL,
    value TEXT,
    description TEXT,
    is_encrypted BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, name)
);

-- 単一解析マスター：単一ソース解析の制御設定
CREATE TABLE single_analysis_master (
    analysis_id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50) NOT NULL,  -- 'COBOL', 'JCL', 'ASM' etc
    process_type VARCHAR(50) NOT NULL,   -- 'parser', 'metrics', 'security' etc
    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT,
    data_type VARCHAR(20) NOT NULL,      -- 'string', 'number', 'boolean' etc
    default_value TEXT,
    is_required BOOLEAN DEFAULT false,
    validation_rule TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_type, process_type, parameter_name)
);

-- サマリ解析マスター：複数ソース解析の制御設定
CREATE TABLE summary_analysis_master (
    summary_id SERIAL PRIMARY KEY,
    analysis_type VARCHAR(50) NOT NULL,   -- 'cross-reference', 'impact', 'dependency' etc
    process_type VARCHAR(50) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT,
    data_type VARCHAR(20) NOT NULL,
    default_value TEXT,
    is_required BOOLEAN DEFAULT false,
    validation_rule TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(analysis_type, process_type, parameter_name)
);

-- ダッシュボードマスター：ダッシュボード生成の制御設定
CREATE TABLE dashboard_master (
    dashboard_id SERIAL PRIMARY KEY,
    dashboard_type VARCHAR(50) NOT NULL,  -- 'single', 'summary', 'security', 'benchmark' etc
    component_type VARCHAR(50) NOT NULL,  -- 'chart', 'table', 'grid', 'metric' etc
    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT,
    display_order INTEGER,
    is_required BOOLEAN DEFAULT false,
    layout_config JSONB,
    style_config JSONB,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dashboard_type, component_type, parameter_name)
);

-- ドキュメントマスター：ドキュメント生成の制御設定
CREATE TABLE document_master (
    document_id SERIAL PRIMARY KEY,
    document_type VARCHAR(50) NOT NULL,   -- 'single', 'summary', 'security', 'benchmark' etc
    section_type VARCHAR(50) NOT NULL,    -- 'header', 'content', 'chart', 'table' etc
    parameter_name VARCHAR(100) NOT NULL,
    parameter_value TEXT,
    display_order INTEGER,
    template_path TEXT,
    format_config JSONB,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_type, section_type, parameter_name)
);

-- ベンチマークマスター：評価基準の設定
CREATE TABLE benchmark_master (
    benchmark_id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,        -- 'quality', 'security', 'performance' etc
    sub_category VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    description TEXT,
    unit VARCHAR(20),
    min_value NUMERIC,
    max_value NUMERIC,
    target_value NUMERIC,
    warning_threshold NUMERIC,
    error_threshold NUMERIC,
    evaluation_rule TEXT,
    weight NUMERIC DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, sub_category, metric_name)
);

-- ベンチマーク基準値マスター：業界標準値や組織標準値の設定
CREATE TABLE benchmark_standard_master (
    standard_id SERIAL PRIMARY KEY,
    benchmark_id INTEGER REFERENCES benchmark_master(benchmark_id),
    standard_type VARCHAR(50) NOT NULL,   -- 'industry', 'organization', 'project' etc
    standard_name VARCHAR(100) NOT NULL,
    target_value NUMERIC,
    min_value NUMERIC,
    max_value NUMERIC,
    description TEXT,
    source_reference TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(benchmark_id, standard_type, standard_name)
);

-- インデックス作成
CREATE INDEX idx_environment_master_category ON environment_master(category);
CREATE INDEX idx_single_analysis_master_type ON single_analysis_master(analysis_type, process_type);
CREATE INDEX idx_summary_analysis_master_type ON summary_analysis_master(analysis_type, process_type);
CREATE INDEX idx_dashboard_master_type ON dashboard_master(dashboard_type, component_type);
CREATE INDEX idx_document_master_type ON document_master(document_type, section_type);
CREATE INDEX idx_benchmark_master_category ON benchmark_master(category, sub_category);
CREATE INDEX idx_benchmark_standard_master_type ON benchmark_standard_master(standard_type);