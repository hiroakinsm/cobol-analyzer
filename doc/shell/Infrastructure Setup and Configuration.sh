#!/bin/bash

# アプリケーションサーバー (172.16.0.27) 用セットアップスクリプト

# 基本パッケージのインストール
sudo apt-get update
sudo apt-get install -y python3.9 python3.9-dev python3.9-venv python3-pip

# アプリケーション用ディレクトリの作成
COBOL_ANALYZER_ROOT="/home/administrator/cobol-analyzer"
mkdir -p ${COBOL_ANALYZER_ROOT}
cd ${COBOL_ANALYZER_ROOT}

# Python仮想環境の作成
python3.9 -m venv venv
source venv/bin/activate

# 必要なパッケージのインストール
pip install --upgrade pip
pip install wheel setuptools

# アプリケーション依存パッケージのインストール
pip install aiohttp==3.8.5
pip install asyncpg==0.28.0
pip install motor==3.3.1
pip install pydantic==2.3.0
pip install tenacity==8.2.3
pip install python-multipart==0.0.6
pip install markdown==3.4.4
pip install numpy==1.24.3
pip install pandas==2.0.3

# パッケージリストの保存
pip freeze > requirements.txt

# アプリケーション構造の作成
mkdir -p ${COBOL_ANALYZER_ROOT}/{src,config,logs,data,tests}
mkdir -p ${COBOL_ANALYZER_ROOT}/src/{analysis,database,models,services,utils}

# ログディレクトリのパーミッション設定
sudo chown -R administrator:administrator ${COBOL_ANALYZER_ROOT}/logs
chmod 755 ${COBOL_ANALYZER_ROOT}/logs

# 設定ファイルの作成
cat << EOF > ${COBOL_ANALYZER_ROOT}/config/app_config.yaml
app:
  name: cobol-analyzer
  version: 1.0.0
  environment: production

logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: logs/app.log

database:
  postgresql:
    host: 172.16.0.13
    port: 5432
    database: cobol_analysis_db
    user: cobana_admin
    min_connections: 10
    max_connections: 100
    
  mongodb:
    host: 172.16.0.17
    port: 27017
    database: cobol_ast_db
    user: administrator

directories:
  completed_sources: /home/koopa-cobol-analyzer/completed
  output: /home/administrator/cobol-analyzer/output
  cache: /home/administrator/cobol-analyzer/cache
EOF

# セキュリティ設定
cat << EOF > ${COBOL_ANALYZER_ROOT}/config/security_config.yaml
security:
  allowed_hosts:
    - 172.16.0.19  # AI/RAG/MLサーバー
    - 172.16.0.25  # Webサーバー
  
  ssl:
    enabled: true
    cert_file: config/ssl/cert.pem
    key_file: config/ssl/key.pem

  authentication:
    enabled: true
    token_expiry: 3600
    max_attempts: 3
EOF

# システムサービスの作成
cat << EOF > /etc/systemd/system/cobol-analyzer.service
[Unit]
Description=COBOL Analyzer Service
After=network.target

[Service]
User=administrator
Group=administrator
WorkingDirectory=/home/administrator/cobol-analyzer
Environment="PATH=/home/administrator/cobol-analyzer/venv/bin"
ExecStart=/home/administrator/cobol-analyzer/venv/bin/python src/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# サービスの有効化
sudo systemctl daemon-reload
sudo systemctl enable cobol-analyzer

# AI/RAG/MLサーバー (172.16.0.19) 用セットアップスクリプト
# 別ファイルとして提供：setup_ai_server.sh

# システム状態チェックスクリプトの作成
cat << EOF > ${COBOL_ANALYZER_ROOT}/scripts/health_check.sh
#!/bin/bash

# データベース接続チェック
check_database() {
    psql -h 172.16.0.13 -U cobana_admin -d cobol_analysis_db -c "SELECT 1" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "PostgreSQL connection: OK"
    else
        echo "PostgreSQL connection: FAILED"
    fi

    mongosh --host 172.16.0.17 --eval "db.stats()" &> /dev/null
    if [ $? -eq 0 ]; then
        echo "MongoDB connection: OK"
    else
        echo "MongoDB connection: FAILED"
    fi
}

# サービス状態チェック
check_services() {
    systemctl is-active --quiet cobol-analyzer
    if [ $? -eq 0 ]; then
        echo "COBOL Analyzer service: RUNNING"
    else
        echo "COBOL Analyzer service: STOPPED"
    fi
}

# ディスク使用量チェック
check_disk_usage() {
    echo "Disk usage:"
    df -h ${COBOL_ANALYZER_ROOT}
}

# メイン実行
main() {
    echo "System Health Check Report"
    echo "=========================="
    echo ""
    check_database
    echo ""
    check_services
    echo ""
    check_disk_usage
}

main
EOF

chmod +x ${COBOL_ANALYZER_ROOT}/scripts/health_check.sh