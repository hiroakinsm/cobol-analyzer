#!/bin/bash

# バックアップシステムのセットアップスクリプト

# 基本設定
BACKUP_ROOT="/home/administrator/backup"
mkdir -p ${BACKUP_ROOT}/{config,scripts,logs,storage}

# バックアップ設定
cat << EOF > ${BACKUP_ROOT}/config/backup_config.yaml
backup:
  schedule:
    # PostgreSQLバックアップ
    postgresql:
      full:
        frequency: "daily"
        retention: 7
        time: "02:00"
      incremental:
        frequency: "hourly"
        retention: 24
        
    # MongoDBバックアップ
    mongodb:
      full:
        frequency: "daily"
        retention: 7
        time: "03:00"
      incremental:
        frequency: "hourly"
        retention: 24
        
    # ファイルシステムバックアップ
    files:
      frequency: "daily"
      retention: 14
      time: "04:00"
      
  storage:
    local:
      path: "${BACKUP_ROOT}/storage"
      max_size: "500GB"
    remote:
      enabled: true
      type: "cifs"
      server: "192.168.101.8"
      share: "backup"
      mount_point: "/mnt/backup"
      credentials:
        username: "administrator"
        password: "DXpress2022"
      
  compression:
    enabled: true
    algorithm: "zstd"
    level: 3
    
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_file: "${BACKUP_ROOT}/config/backup.key"
EOF

# PostgreSQLバックアップスクリプト
cat << EOF > ${BACKUP_ROOT}/scripts/backup_postgresql.sh
#!/bin/bash

# 設定
PG_HOST="172.16.0.13"
PG_PORT="5432"
PG_USER="cobana_admin"
PG_DB="cobol_analysis_db"
BACKUP_DIR="${BACKUP_ROOT}/storage/postgresql"
DATE=\$(date +%Y%m%d_%H%M%S)

# 完全バックアップ
full_backup() {
    pg_dump -h \${PG_HOST} -p \${PG_PORT} -U \${PG_USER} \${PG_DB} | \
    zstd -3 > "\${BACKUP_DIR}/full_\${DATE}.sql.zst"
    
    # 暗号化
    openssl enc -aes-256-gcm -salt -in "\${BACKUP_DIR}/full_\${DATE}.sql.zst" \
    -out "\${BACKUP_DIR}/full_\${DATE}.sql.zst.enc" \
    -pass file:${BACKUP_ROOT}/config/backup.key
    
    rm "\${BACKUP_DIR}/full_\${DATE}.sql.zst"
}

# 増分バックアップ
incremental_backup() {
    pg_dump -h \${PG_HOST} -p \${PG_PORT} -U \${PG_USER} \${PG_DB} \
    --format=custom -F c -Z 3 \
    -f "\${BACKUP_DIR}/incr_\${DATE}.backup"
}

# クリーンアップ
cleanup() {
    # 古い完全バックアップの削除
    find \${BACKUP_DIR} -name "full_*.sql.zst.enc" -mtime +7 -delete
    
    # 古い増分バックアップの削除
    find \${BACKUP_DIR} -name "incr_*.backup" -mtime +1 -delete
}

# メイン処理
main() {
    if [ "\$1" = "full" ]; then
        full_backup
    elif [ "\$1" = "incremental" ]; then
        incremental_backup
    fi
    cleanup
}

main "\$1"
EOF

# MongoDBバックアップスクリプト
cat << EOF > ${BACKUP_ROOT}/scripts/backup_mongodb.sh
#!/bin/bash

# 設定
MONGO_HOST="172.16.0.17"
MONGO_PORT="27017"
MONGO_DB="cobol_ast_db"
BACKUP_DIR="${BACKUP_ROOT}/storage/mongodb"
DATE=\$(date +%Y%m%d_%H%M%S)

# 完全バックアップ
full_backup() {
    mongodump --host \${MONGO_HOST} --port \${MONGO_PORT} \
    --db \${MONGO_DB} --out "\${BACKUP_DIR}/full_\${DATE}"
    
    # 圧縮
    tar cf - -C "\${BACKUP_DIR}" "full_\${DATE}" | \
    zstd -3 > "\${BACKUP_DIR}/full_\${DATE}.tar.zst"
    
    # 暗号化
    openssl enc -aes-256-gcm -salt \
    -in "\${BACKUP_DIR}/full_\${DATE}.tar.zst" \
    -out "\${BACKUP_DIR}/full_\${DATE}.tar.zst.enc" \
    -pass file:${BACKUP_ROOT}/config/backup.key
    
    rm -rf "\${BACKUP_DIR}/full_\${DATE}" "\${BACKUP_DIR}/full_\${DATE}.tar.zst"
}

# 増分バックアップ
incremental_backup() {
    mongodump --host \${MONGO_HOST} --port \${MONGO_PORT} \
    --db \${MONGO_DB} --out "\${BACKUP_DIR}/incr_\${DATE}" \
    --queryFile "${BACKUP_ROOT}/config/incremental_query.json"
}

# クリーンアップ
cleanup() {
    # 古いバックアップの削除
    find ${BACKUP_DIR} -name "full_*.tar.zst.enc" -mtime +7 -delete
    find ${BACKUP_DIR} -name "incr_*" -mtime +1 -delete
}

# メイン処理
main() {
    if [ "$1" = "full" ]; then
        full_backup
    elif [ "$1" = "incremental" ]; then
        incremental_backup
    fi
    cleanup
}

main "$1"
EOF

# ファイルシステムバックアップスクリプト
cat << EOF > ${BACKUP_ROOT}/scripts/backup_files.sh
#!/bin/bash

# 設定
SOURCE_DIRS=(
    "/home/koopa-cobol-analyzer/completed"
    "/home/administrator/cobol-analyzer"
)
BACKUP_DIR="${BACKUP_ROOT}/storage/files"
DATE=$(date +%Y%m%d_%H%M%S)

# バックアップ実行
backup_files() {
    for src in "${SOURCE_DIRS[@]}"; do
        # ディレクトリ名からバックアップファイル名を生成
        dir_name=$(basename ${src})
        backup_file="${BACKUP_DIR}/${dir_name}_${DATE}.tar"
        
        # 圧縮バックアップの作成
        tar cf - -C $(dirname ${src}) $(basename ${src}) | \
        zstd -3 > "${backup_file}.zst"
        
        # 暗号化
        openssl enc -aes-256-gcm -salt \
        -in "${backup_file}.zst" \
        -out "${backup_file}.zst.enc" \
        -pass file:${BACKUP_ROOT}/config/backup.key
        
        rm "${backup_file}.zst"
    done
}

# クリーンアップ
cleanup() {
    find ${BACKUP_DIR} -name "*.tar.zst.enc" -mtime +14 -delete
}

# メイン処理
main() {
    backup_files
    cleanup
}

main
EOF

# リカバリースクリプト
cat << EOF > ${BACKUP_ROOT}/scripts/restore.sh
#!/bin/bash

# 設定
BACKUP_DIR="${BACKUP_ROOT}/storage"
RESTORE_DIR="${BACKUP_ROOT}/restore"

# PostgreSQLリカバリー
restore_postgresql() {
    local backup_file="$1"
    
    # 復号化
    openssl enc -d -aes-256-gcm -in "${backup_file}" \
    -out "${RESTORE_DIR}/temp.sql.zst" \
    -pass file:${BACKUP_ROOT}/config/backup.key
    
    # 解凍
    zstd -d "${RESTORE_DIR}/temp.sql.zst" -o "${RESTORE_DIR}/restore.sql"
    
    # リストア
    psql -h 172.16.0.13 -U cobana_admin cobol_analysis_db < "${RESTORE_DIR}/restore.sql"
    
    # 一時ファイルの削除
    rm "${RESTORE_DIR}/temp.sql.zst" "${RESTORE_DIR}/restore.sql"
}

# MongoDBリカバリー
restore_mongodb() {
    local backup_file="$1"
    
    # 復号化と解凍
    openssl enc -d -aes-256-gcm -in "${backup_file}" \
    -out "${RESTORE_DIR}/temp.tar.zst" \
    -pass file:${BACKUP_ROOT}/config/backup.key
    
    zstd -d "${RESTORE_DIR}/temp.tar.zst"
    tar xf "${RESTORE_DIR}/temp.tar" -C "${RESTORE_DIR}"
    
    # リストア
    mongorestore --host 172.16.0.17 --port 27017 \
    --db cobol_ast_db "${RESTORE_DIR}/full_"*
    
    # 一時ファイルの削除
    rm -rf "${RESTORE_DIR}/temp.tar.zst" "${RESTORE_DIR}/temp.tar" \
    "${RESTORE_DIR}/full_"*
}

# ファイルシステムリカバリー
restore_files() {
    local backup_file="$1"
    local target_dir="$2"
    
    # 復号化と解凍
    openssl enc -d -aes-256-gcm -in "${backup_file}" \
    -out "${RESTORE_DIR}/temp.tar.zst" \
    -pass file:${BACKUP_ROOT}/config/backup.key
    
    zstd -d "${RESTORE_DIR}/temp.tar.zst"
    tar xf "${RESTORE_DIR}/temp.tar" -C "${target_dir}"
    
    # 一時ファイルの削除
    rm "${RESTORE_DIR}/temp.tar.zst" "${RESTORE_DIR}/temp.tar"
}

# メイン処理
main() {
    local type="$1"
    local backup_file="$2"
    local target_dir="$3"
    
    mkdir -p "${RESTORE_DIR}"
    
    case "${type}" in
        "postgresql")
            restore_postgresql "${backup_file}"
            ;;
        "mongodb")
            restore_mongodb "${backup_file}"
            ;;
        "files")
            if [ -z "${target_dir}" ]; then
                echo "Target directory required for file restore"
                exit 1
            fi
            restore_files "${backup_file}" "${target_dir}"
            ;;
        *)
            echo "Unknown restore type: ${type}"
            exit 1
            ;;
    esac
    
    rm -rf "${RESTORE_DIR}"
}

main "$@"
EOF

# スクリプトの実行権限設定
chmod +x ${BACKUP_ROOT}/scripts/*.sh

# cronジョブの設定
(crontab -l 2>/dev/null; echo "0 2 * * * ${BACKUP_ROOT}/scripts/backup_postgresql.sh full") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * ${BACKUP_ROOT}/scripts/backup_postgresql.sh incremental") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * ${BACKUP_ROOT}/scripts/backup_mongodb.sh full") | crontab -
(crontab -l 2>/dev/null; echo "0 * * * * ${BACKUP_ROOT}/scripts/backup_mongodb.sh incremental") | crontab -
(crontab -l 2>/dev/null; echo "0 4 * * * ${BACKUP_ROOT}/scripts/backup_files.sh") | crontab -