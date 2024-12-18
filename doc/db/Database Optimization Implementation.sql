-- PostgreSQL最適化（172.16.0.13）

-- パーティションテーブルの作成
-- analysis_tasksテーブルを日付でパーティション化
CREATE TABLE analysis_tasks_partitioned (
    task_id UUID PRIMARY KEY,
    source_id UUID,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 0,
    source_path TEXT NOT NULL,
    analysis_config JSONB NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
) PARTITION BY RANGE (created_at);

-- 月次パーティションの作成
CREATE TABLE analysis_tasks_y2024m01 PARTITION OF analysis_tasks_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE analysis_tasks_y2024m02 PARTITION OF analysis_tasks_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- 以降の月次パーティションも同様に作成

-- インデックスの最適化
CREATE INDEX idx_analysis_tasks_status_priority ON analysis_tasks_partitioned (status, priority DESC);
CREATE INDEX idx_analysis_tasks_source_id ON analysis_tasks_partitioned (source_id);
CREATE INDEX idx_analysis_tasks_created_at ON analysis_tasks_partitioned (created_at);

-- 解析結果テーブルの最適化
CREATE TABLE analysis_results_partitioned (
    result_id UUID PRIMARY KEY,
    task_id UUID REFERENCES analysis_tasks_partitioned(task_id),
    source_id UUID NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    mongodb_collection VARCHAR(100),
    mongodb_document_id VARCHAR(100),
    summary_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL
) PARTITION BY RANGE (created_at);

-- 月次パーティションの作成
CREATE TABLE analysis_results_y2024m01 PARTITION OF analysis_results_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE analysis_results_y2024m02 PARTITION OF analysis_results_partitioned
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- インデックスの作成
CREATE INDEX idx_analysis_results_source_id ON analysis_results_partitioned (source_id);
CREATE INDEX idx_analysis_results_type_status ON analysis_results_partitioned (analysis_type, status);
CREATE INDEX idx_analysis_results_created_at ON analysis_results_partitioned (created_at);

-- PostgreSQLパフォーマンスチューニング
ALTER SYSTEM SET 
    shared_buffers = '4GB',
    effective_cache_size = '12GB',
    maintenance_work_mem = '1GB',
    work_mem = '64MB',
    max_worker_processes = '8',
    max_parallel_workers_per_gather = '4',
    max_parallel_workers = '8',
    random_page_cost = '1.1',
    effective_io_concurrency = '200';

-- MongoDB最適化（172.16.0.17）

-- ASTコレクションのインデックス作成
db.ast_collection.createIndex({ "source_id": 1 });
db.ast_collection.createIndex({ "task_id": 1 });
db.ast_collection.createIndex({ "ast_type": 1 });
db.ast_collection.createIndex({ "created_at": 1 });

-- ソース情報コレクションのインデックス作成
db.source_info.createIndex({ "source_id": 1 });
db.source_info.createIndex({ "file_path": 1 });
db.source_info.createIndex({ "created_at": 1 });

-- MongoDBパフォーマンスチューニング
db.adminCommand({
    setParameter: 1,
    wiredTigerConcurrentReadTransactions: 128,
    wiredTigerConcurrentWriteTransactions: 128
});

-- シャーディングの設定（必要に応じて）
sh.enableSharding("cobol_ast_db");
sh.shardCollection("cobol_ast_db.ast_collection", { "source_id": "hashed" });
sh.shardCollection("cobol_ast_db.source_info", { "source_id": "hashed" });

-- コレクションの最適化スクリプト
db.runCommand({
    compact: "ast_collection",
    force: true
});

db.runCommand({
    compact: "source_info",
    force: true
});

-- 定期的なメンテナンス設定
cat << EOF > /etc/cron.daily/db_maintenance
#!/bin/bash

# PostgreSQL VACUUM
psql -h 172.16.0.13 -U cobana_admin -d cobol_analysis_db -c "VACUUM ANALYZE;"

# MongoDB インデックス再構築
mongo --host 172.16.0.17 cobol_ast_db --eval '
db.ast_collection.reIndex();
db.source_info.reIndex();
'
EOF

chmod +x /etc/cron.daily/db_maintenance