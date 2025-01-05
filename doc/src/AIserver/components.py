# /home/administrator/ai-server/src/rag/components.py
# Advanced RAG Components.py

from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np
from pathlib import Path
import json
import re
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

class ContentType(Enum):
    """コンテンツタイプ"""
    CODE = "code"
    METRICS = "metrics"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    ANALYSIS = "analysis"

@dataclass
class EmbeddingConfig:
    """埋め込み設定"""
    model_name: str
    max_seq_length: int = 512
    normalize_embeddings: bool = True
    batch_size: int = 32
    chunk_size: int = 256
    chunk_overlap: int = 64
    num_gpus: int = 1  # GPU数の設定を追加
    shard_size: int = 1000000  # シャーディングサイズ
    cache_dir: Optional[str] = None  # キャッシュディレクトリ

class TextPreprocessor:
    """テキスト前処理"""
    def __init__(self, content_type: ContentType):
        self.content_type = content_type
        self.preprocessed_cache = {}  # キャッシュの追加

    async def preprocess(self, text: str) -> str:
        """テキストの前処理"""
        cache_key = f"{self.content_type}:{hash(text)}"
        if cache_key in self.preprocessed_cache:
            return self.preprocessed_cache[cache_key]

        result = await self._preprocess_with_type(text)
        self.preprocessed_cache[cache_key] = result
        return result

    async def _preprocess_with_type(self, text: str) -> str:
        """タイプ別の前処理"""
        if self.content_type == ContentType.CODE:
            return await self._preprocess_code(text)
        elif self.content_type == ContentType.METRICS:
            return await self._preprocess_metrics(text)
        else:
            return await self._preprocess_text(text)

    async def _preprocess_code(self, code: str) -> str:
        """コードの前処理 - 並列処理の実装"""
        with ThreadPoolExecutor() as executor:
            comments_future = executor.submit(self._extract_comments, code)
            keywords_future = executor.submit(self._extract_keywords, code)
            data_items_future = executor.submit(self._extract_data_items, code)

            comments = comments_future.result()
            keywords = keywords_future.result()
            data_items = data_items_future.result()

        return " ".join([
            " ".join(comments),
            " ".join(keywords),
            " ".join(data_items)
        ])

    def _extract_comments(self, code: str) -> List[str]:
        """コメントの抽出 - 正規表現の最適化"""
        return re.findall(r'(?:^|\s+)\*>.*?$|(?:^|\s+)\*.*?$', code, re.MULTILINE)

    def _extract_keywords(self, code: str) -> List[str]:
        """キーワードの抽出"""
        pattern = r'\b(PERFORM|IF|MOVE|COMPUTE|CALL)\b'
        return re.findall(pattern, code)

    def _extract_data_items(self, code: str) -> List[str]:
        """データ項目の抽出"""
        return re.findall(r'\d{2}\s+(\w+)\s+PIC', code)

class CustomEmbeddingModel:
    """カスタム埋め込みモデル - GPU対応とスケーリング機能"""
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.devices = self._initialize_devices()
        self.models = self._initialize_models()
        self.preprocessors = self._initialize_preprocessors()
        self.embedding_cache = {}

    def _initialize_devices(self) -> List[torch.device]:
        """利用可能なGPUデバイスの初期化"""
        if torch.cuda.is_available():
            return [torch.device(f"cuda:{i}") 
                   for i in range(min(torch.cuda.device_count(), 
                                   self.config.num_gpus))]
        return [torch.device("cpu")]

    def _initialize_models(self) -> List[SentenceTransformer]:
        """モデルの初期化 - 複数GPU対応"""
        return [
            SentenceTransformer(self.config.model_name).to(device)
            for device in self.devices
        ]

    def _initialize_preprocessors(self) -> Dict[ContentType, TextPreprocessor]:
        """プリプロセッサの初期化"""
        return {
            content_type: TextPreprocessor(content_type)
            for content_type in ContentType
        }

    async def encode(self, 
                    texts: List[str],
                    content_type: ContentType,
                    batch_size: Optional[int] = None) -> np.ndarray:
        """テキストのエンコード - 並列処理とキャッシング"""
        cache_key = f"{content_type}:{hash(str(texts))}"
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]

        preprocessor = self.preprocessors[content_type]
        processed_texts = await asyncio.gather(
            *[preprocessor.preprocess(text) for text in texts]
        )
        
        chunked_texts = await self._chunk_texts_parallel(processed_texts)
        embeddings = await self._encode_chunks(chunked_texts, batch_size)
        combined = await self._combine_chunk_embeddings(embeddings)

        self.embedding_cache[cache_key] = combined
        return combined

    async def _chunk_texts_parallel(self, texts: List[str]) -> List[str]:
        """テキストの並列チャンク分割"""
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._chunk_single_text, text)
                for text in texts
            ]
            results = []
            for future in futures:
                results.extend(future.result())
        return results

    def _chunk_single_text(self, text: str) -> List[str]:
        """単一テキストのチャンク分割"""
        chunks = []
        if len(text) > self.config.chunk_size:
            start = 0
            while start < len(text):
                end = start + self.config.chunk_size
                chunks.append(text[start:end])
                start += self.config.chunk_size - self.config.chunk_overlap
        else:
            chunks.append(text)
        return chunks

    async def _encode_chunks(self, 
                           chunks: List[str], 
                           batch_size: Optional[int] = None) -> List[np.ndarray]:
        """チャンクのエンコード - GPU並列処理"""
        batch_size = batch_size or self.config.batch_size
        num_batches = (len(chunks) + batch_size - 1) // batch_size
        
        results = []
        for i in range(num_batches):
            batch = chunks[i * batch_size:(i + 1) * batch_size]
            # GPUに分散
            device_idx = i % len(self.devices)
            model = self.models[device_idx]
            batch_embeddings = model.encode(
                batch,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=False
            )
            results.extend(batch_embeddings)
        
        return results

    async def _combine_chunk_embeddings(self, 
                                      embeddings: List[np.ndarray]) -> np.ndarray:
        """チャンク埋め込みの結合 - 重み付き平均の実装"""
        if not embeddings:
            raise ValueError("Empty embeddings list")
        
        weights = np.array([1 / (i + 1) for i in range(len(embeddings))])
        weights = weights / weights.sum()
        
        return np.average(embeddings, axis=0, weights=weights)

    def clear_cache(self):
        """キャッシュのクリア"""
        self.embedding_cache.clear()
        for preprocessor in self.preprocessors.values():
            preprocessor.preprocessed_cache.clear()
