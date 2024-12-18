#!/bin/bash

# AI/RAG/MLサーバー (172.16.0.19) 用セットアップスクリプト

# 基本パッケージのインストール
sudo apt-get update
sudo apt-get install -y python3.9 python3.9-dev python3.9-venv python3-pip \
    build-essential cmake git

# GPUドライバーとCUDAのインストール（必要に応じて）
# ... GPU関連のセットアップコード ...

# アプリケーション用ディレクトリの作成
AI_SERVER_ROOT="/home/administrator/ai-server"
mkdir -p ${AI_SERVER_ROOT}
cd ${AI_SERVER_ROOT}

# Python仮想環境の作成
python3.9 -m venv venv
source venv/bin/activate

# 必要なパッケージのインストール
pip install --upgrade pip
pip install wheel setuptools

# AI/ML関連パッケージのインストール
pip install torch==2.0.1  # GPUサポート版が必要な場合は適宜変更
pip install transformers==4.33.1
pip install sentence-transformers==2.2.2
pip install llama-cpp-python==0.2.6
pip install optimum==1.12.0
pip install accelerate==0.23.0
pip install bitsandbytes==0.41.1

# RAG関連パッケージのインストール
pip install faiss-cpu==1.7.4  # GPUバージョンが必要な場合は faiss-gpu
pip install chromadb==0.4.6
pip install langchain==0.0.286

# その他の依存パッケージ
pip install fastapi==0.103.1
pip install uvicorn==0.23.2
pip install pydantic==2.3.0
pip install python-multipart==0.0.6

# パッケージリストの保存
pip freeze > requirements.txt

# ディレクトリ構造の作成
mkdir -p ${AI_SERVER_ROOT}/{models,cache,logs,config}
mkdir -p ${AI_SERVER_ROOT}/models/{llm,embeddings}

# LlamaモデルのダウンロードとQuantization
cat << EOF > ${AI_SERVER_ROOT}/scripts/setup_llm.py
from transformers import AutoModelForCausalLM, AutoTokenizer
from optimum.gptq import GPTQQuantizer
import torch

def download_and_quantize_model():
    # モデルとトークナイザーのダウンロード
    model_name = "meta-llama/Llama-2-7b-chat-hf"
    model = AutoModelForCausalLM.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # 量子化設定
    quantizer = GPTQQuantizer(
        bits=4,
        dataset="c4",
        block_size=128,
        max_samples=400
    )

    # モデルの量子化
    quantized_model = quantizer.quantize_model(
        model,
        tokenizer,
        save_dir="${AI_SERVER_ROOT}/models/llm/llama-2-7b-4bit"
    )

    print("Model quantization completed")

if __name__ == "__main__":
    download_and_quantize_model()
EOF

# RAGシステムのキャッシュ設定
cat << EOF > ${AI_SERVER_ROOT}/config/rag_config.yaml
rag:
  cache:
    enabled: true
    type: "chromadb"
    path: "${AI_SERVER_ROOT}/cache/vector_store"
    max_size: 10GB
    ttl: 86400  # 24 hours
    cleanup_interval: 3600  # 1 hour

  embeddings:
    model: "sentence-transformers/all-mpnet-base-v2"
    cache_enabled: true
    batch_size: 32
    max_length: 512

  retrieval:
    top_k: 5
    min_similarity: 0.7
    reranking_enabled: true

  model:
    type: "llama"
    path: "${AI_SERVER_ROOT}/models/llm/llama-2-7b-4bit"
    max_tokens: 2048
    temperature: 0.7
    top_p: 0.9
EOF

# ログ設定
cat << EOF > ${AI_SERVER_ROOT}/config/logging_config.yaml
logging:
  version: 1
  formatters:
    standard:
      format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  handlers:
    console:
      class: logging.StreamHandler
      formatter: standard
      level: INFO
    file:
      class: logging.FileHandler
      filename: ${AI_SERVER_ROOT}/logs/rag_system.log
      formatter: standard
      level: INFO
  root:
    level: INFO
    handlers: [console, file]
EOF

# システムサービスの作成
cat << EOF > /etc/systemd/system/rag-service.service
[Unit]
Description=RAG System Service
After=network.target

[Service]
User=administrator
Group=administrator
WorkingDirectory=${AI_SERVER_ROOT}
Environment="PATH=${AI_SERVER_ROOT}/venv/bin"
ExecStart=${AI_SERVER_ROOT}/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# サービスの有効化
sudo systemctl daemon-reload
sudo systemctl enable rag-service

# キャッシュクリーニングスクリプト
cat << EOF > ${AI_SERVER_ROOT}/scripts/clean_cache.sh
#!/bin/bash

# ベクトルストアキャッシュのクリーニング
clean_vector_store() {
    find ${AI_SERVER_ROOT}/cache/vector_store -type f -mtime +1 -delete
}

# 埋め込みキャッシュのクリーニング
clean_embeddings_cache() {
    find ${AI_SERVER_ROOT}/cache/embeddings -type f -mtime +1 -delete
}

# メイン実行
main() {
    echo "Starting cache cleanup..."
    clean_vector_store
    clean_embeddings_cache
    echo "Cache cleanup completed"
}

main
EOF

chmod +x ${AI_SERVER_ROOT}/scripts/clean_cache.sh

# キャッシュクリーニングのcronジョブ設定
(crontab -l 2>/dev/null; echo "0 */6 * * * ${AI_SERVER_ROOT}/scripts/clean_cache.sh") | crontab -