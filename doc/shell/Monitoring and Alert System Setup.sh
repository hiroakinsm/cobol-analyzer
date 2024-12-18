#!/bin/bash

# モニタリングシステムのセットアップスクリプト

# 基本設定
MONITOR_ROOT="/home/administrator/monitoring"
mkdir -p ${MONITOR_ROOT}/{config,scripts,logs,data}

# Prometheusの設定
cat << EOF > ${MONITOR_ROOT}/config/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'cobol-analyzer'
    static_configs:
      - targets: ['172.16.0.27:9090']  # アプリケーションサーバー
        labels:
          service: 'app_server'
          
  - job_name: 'rag-system'
    static_configs:
      - targets: ['172.16.0.19:9090']  # AI/RAGサーバー
        labels:
          service: 'ai_server'
          
  - job_name: 'databases'
    static_configs:
      - targets: ['172.16.0.13:9090']  # PostgreSQL
        labels:
          service: 'postgresql'
      - targets: ['172.16.0.17:9090']  # MongoDB
        labels:
          service: 'mongodb'
EOF

# アプリケーションメトリクス収集設定
cat << EOF > ${MONITOR_ROOT}/config/metrics_config.py
from prometheus_client import Counter, Gauge, Histogram, Summary

# 処理メトリクス
ANALYSIS_REQUESTS = Counter(
    'cobol_analysis_requests_total',
    'Total number of analysis requests',
    ['type', 'status']
)

ANALYSIS_DURATION = Histogram(
    'cobol_analysis_duration_seconds',
    'Time spent on analysis',
    ['type'],
    buckets=[10, 30, 60, 120, 300, 600]
)

# リソースメトリクス
MEMORY_USAGE = Gauge(
    'cobol_memory_usage_bytes',
    'Current memory usage',
    ['component']
)

CPU_USAGE = Gauge(
    'cobol_cpu_usage_percent',
    'Current CPU usage',
    ['component']
)

# RAGシステムメトリクス
RAG_REQUESTS = Counter(
    'rag_requests_total',
    'Total number of RAG requests',
    ['operation']
)

RAG_LATENCY = Summary(
    'rag_operation_latency_seconds',
    'RAG operation latency',
    ['operation']
)

# データベースメトリクス
DB_CONNECTIONS = Gauge(
    'database_connections',
    'Number of active database connections',
    ['database']
)

DB_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['database', 'operation']
)
EOF

# アラートルールの設定
cat << EOF > ${MONITOR_ROOT}/config/alert_rules.yml
groups:
- name: cobol_analyzer_alerts
  rules:
  # システムリソース
  - alert: HighMemoryUsage
    expr: cobol_memory_usage_bytes / 1024 / 1024 / 1024 > 28  # 28GB
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      description: "Memory usage is above 28GB"

  - alert: HighCPUUsage
    expr: cobol_cpu_usage_percent > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
      description: "CPU usage is above 80%"

  # 処理パフォーマンス
  - alert: SlowAnalysis
    expr: rate(cobol_analysis_duration_seconds_bucket[5m]) > 300
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Slow analysis detected"
      description: "Analysis taking longer than 5 minutes"

  # RAGシステム
  - alert: HighRAGLatency
    expr: rag_operation_latency_seconds_count > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High RAG latency detected"
      description: "RAG operations are taking too long"

  # データベース
  - alert: HighDBConnections
    expr: database_connections > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High number of DB connections"
      description: "Database connection count is high"
EOF

# アラート通知設定
cat << EOF > ${MONITOR_ROOT}/config/alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'team-email'

receivers:
- name: 'team-email'
  email_configs:
  - to: 'team@example.com'
    from: 'alertmanager@example.com'
    smarthost: 'smtp.example.com:587'
    auth_username: 'alertmanager'
    auth_identity: 'alertmanager@example.com'
    auth_password: 'password'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname']
EOF

# メトリクス収集スクリプト
cat << EOF > ${MONITOR_ROOT}/scripts/collect_metrics.py
import psutil
import time
from prometheus_client import start_http_server, REGISTRY
import logging
from config.metrics_config import *

def collect_system_metrics():
    while True:
        # メモリ使用量
        memory = psutil.virtual_memory()
        MEMORY_USAGE.labels(component='system').set(memory.used)

        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        CPU_USAGE.labels(component='system').set(cpu_percent)

        time.sleep(15)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_http_server(9090)
    collect_system_metrics()
EOF

# アラートテストスクリプト
cat << EOF > ${MONITOR_ROOT}/scripts/test_alerts.sh
#!/bin/bash

# メモリ使用量アラートのテスト
stress-ng --vm 1 --vm-bytes 29G --timeout 300s &

# CPU使用率アラートのテスト
stress-ng --cpu 8 --timeout 300s &

# 処理時間アラートのテスト
curl -X POST "http://localhost:8000/api/v1/analysis/single" \
     -H "Content-Type: application/json" \
     -d '{"source_id": "test", "delay": 360}'
EOF

chmod +x ${MONITOR_ROOT}/scripts/test_alerts.sh

# Grafanaダッシュボード設定
cat << EOF > ${MONITOR_ROOT}/config/dashboards/overview.json
{
  "dashboard": {
    "title": "COBOL Analyzer Overview",
    "panels": [
      {
        "title": "System Resources",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "cobol_memory_usage_bytes",
            "legendFormat": "Memory Usage"
          },
          {
            "expr": "cobol_cpu_usage_percent",
            "legendFormat": "CPU Usage"
          }
        ]
      },
      {
        "title": "Analysis Performance",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "rate(cobol_analysis_duration_seconds_count[5m])",
            "legendFormat": "Analysis Rate"
          }
        ]
      }
    ]
  }
}
EOF

# システムサービスの設定
cat << EOF > /etc/systemd/system/metrics-collector.service
[Unit]
Description=Metrics Collector Service
After=network.target

[Service]
Type=simple
User=administrator
ExecStart=${MONITOR_ROOT}/scripts/collect_metrics.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable metrics-collector
sudo systemctl start metrics-collector