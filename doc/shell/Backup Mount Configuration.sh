#!/bin/bash

# Windows共有フォルダマウント用の設定とスクリプト

# 必要なパッケージのインストール
sudo apt-get update
sudo apt-get install -y cifs-utils

# 認証情報の保存
sudo mkdir -p /etc/backup-credentials
cat << EOF | sudo tee /etc/backup-credentials/backup.conf
username=administrator
password=DXpress2022
EOF

# 認証情報ファイルのセキュリティ設定
sudo chmod 600 /etc/backup-credentials/backup.conf

# マウントポイントの作成
sudo mkdir -p /mnt/backup
sudo chown administrator:administrator /mnt/backup

# fstabエントリの追加
# エスケープされたスペースを使用
FSTAB_ENTRY="//192.168.101.8/backup /mnt/backup cifs credentials=/etc/backup-credentials/backup.conf,iocharset=utf8,file_mode=0660,dir_mode=0770,vers=3.0,noperm 0 0"
echo "${FSTAB_ENTRY}" | sudo tee -a /etc/fstab

# マウントの実行
sudo mount /mnt/backup

# マウント状態の確認スクリプト
cat << EOF > ${BACKUP_ROOT}/scripts/check_mount.sh
#!/bin/bash

# マウント状態の確認
if ! mountpoint -q /mnt/backup; then
    echo "Backup share is not mounted. Attempting to mount..."
    sudo mount /mnt/backup
    if [ $? -eq 0 ]; then
        echo "Successfully mounted backup share."
    else
        echo "Failed to mount backup share. Check network and credentials."
        exit 1
    fi
fi

# 書き込みテスト
TEST_FILE="/mnt/backup/write_test_\$(date +%s)"
if ! touch "\${TEST_FILE}" 2>/dev/null; then
    echo "Cannot write to backup share. Check permissions."
    exit 1
fi
rm "\${TEST_FILE}"

echo "Backup share is mounted and writable."
EOF

chmod +x ${BACKUP_ROOT}/scripts/check_mount.sh

# バックアップ前のマウント確認を追加
sed -i '1a\
# マウント状態の確認\
${BACKUP_ROOT}/scripts/check_mount.sh || exit 1' ${BACKUP_ROOT}/scripts/backup_postgresql.sh

sed -i '1a\
# マウント状態の確認\
${BACKUP_ROOT}/scripts/check_mount.sh || exit 1' ${BACKUP_ROOT}/scripts/backup_mongodb.sh

sed -i '1a\
# マウント状態の確認\
${BACKUP_ROOT}/scripts/check_mount.sh || exit 1' ${BACKUP_ROOT}/scripts/backup_files.sh

# リモートバックアップ先の作成
sudo mkdir -p /mnt/backup/{postgresql,mongodb,files}
sudo chown -R administrator:administrator /mnt/backup/