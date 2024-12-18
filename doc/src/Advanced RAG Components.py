```python
from typing import List, Dict, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import torch
from sentence_transformers import SentenceTransformer, util
import numpy as np
from pathlib import Path
import json
import re
from abc import ABC, abstractmethod

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

class TextPreprocessor:
    """テキスト前処理"""
    def __init__(self, content_type: ContentType):
        self.content_type = content_type

    def preprocess(self, text: str) -> str:
        """テキストの前処理"""
        if self.content_type == ContentType.CODE:
            return self._preprocess_code(text)
        elif self.content_type == ContentType.METRICS:
            return self._preprocess_metrics(text)
        else:
            return self._preprocess_text(text)

    def _preprocess_code(self, code: str) -> str:
        """コードの前処理"""
        # コメント抽出
        comments = re.findall(r'(?:^|\s+)\*>.*?$|(?:^|\s+)\*.*?$', code, re.MULTILINE)
        # 主要なキーワード抽出
        keywords = re.findall(r'\b(PERFORM|IF|MOVE|COMPUTE|CALL)\b', code)
        # データ定義抽出
        data_items = re.findall(r'\d{2}\s+(\w+)\s+PIC', code)
        
        return " ".join([
            " ".join(comments),
            " ".join(keywords),
            " ".join(data_items)
        ])

    def _preprocess_metrics(self, metrics: str) -> str:
        """メトリクスの前処理"""
        try:
            metrics_dict = json.loads(metrics)
            return " ".join([
                f"{k}: {v}" for k, v in metrics_dict.items()
            ])
        except json.JSONDecodeError:
            return metrics

    def _preprocess_text(self, text: str) -> str:
        """一般テキストの前処理"""
        # 空白の正規化
        text = re.sub(r'\s+', ' ', text)
        # 特殊文字の除去
        text = re.sub(r'[^\w\s]', ' ', text)
        return text.strip()

class CustomEmbeddingModel:
    """カスタム埋め込みモデル"""
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.model = SentenceTransformer(config.model_name)
        self.preprocessors = {
            content_type: TextPreprocessor(content_type)
            for content_type in ContentType
        }

    async def encode(self, 
                    texts: List[str],
                    content_type: ContentType,
                    batch_size: Optional[int] = None) -> np.ndarray:
        """テキストのエンコード"""
        preprocessor = self.preprocessors[content_type]
        processed_texts = [preprocessor.preprocess(text) for text in texts]
        
        # チャンク分割
        chunked_texts = self._chunk_texts(processed_texts)
        
        # バッチ処理でエンコード
        embeddings = []
        batch_size = batch_size or self.config.batch_size
        
        for i in range(0, len(chunked_texts), batch_size):
            batch = chunked_texts[i:i + batch_size]
            batch_embeddings = self.model.encode(
                batch,
                normalize_embeddings=self.config.normalize_embeddings
            )
            embeddings.extend(batch_embeddings)

        # チャンク単位の埋め込みを結合
        return self._combine_chunk_embeddings(embeddings)

    def _chunk_texts(self, texts: List[str]) -> List[str]:
        """テキストのチャンク分割"""
        chunked_texts = []
        for text in texts:
            if len(text) > self.config.chunk_size:
                chunks = []
                start = 0
                while start < len(text):
                    end = start + self.config.chunk_size
                    chunk = text[start:end]
                    chunks.append(chunk)
                    start += self.config.chunk_size - self.config.chunk_overlap
                chunked_texts.extend(chunks)
            else:
                chunked_texts.append(text)
        return chunked_texts

    def _combine_chunk_embeddings(self, embeddings: List[np.ndarray]) -> np.ndarray:
        """チャンク埋め込みの結合"""
        return np.mean(embeddings, axis=0)

class ContextManager:
    """コンテキスト管理"""
    def __init__(self, max_context_length: int = 4096):
        self.max_context_length = max_context_length
        self.context_store: Dict[str, List[Dict[str, Any]]] = {}

    async def add_context(self, 
                         session_id: str,
                         context: Dict[str, Any],
                         importance: float = 1.0):
        """コンテキストの追加"""
        if session_id not in self.context_store:
            self.context_store[session_id] = []

        context['importance'] = importance
        context['timestamp'] = datetime.utcnow()
        self.context_store[session_id].append(context)
        
        # コンテキストの整理
        await self._optimize_context(session_id)

    async def get_context(self, 
                         session_id: str,
                         query: str) -> List[Dict[str, Any]]:
        """関連コンテキストの取得"""
        if session_id not in self.context_store:
            return []

        contexts = self.context_store[session_id]
        # クエリに関連する重要なコンテキストを選択
        relevant_contexts = await self._select_relevant_contexts(
            contexts,
            query
        )
        
        return relevant_contexts

    async def _optimize_context(self, session_id: str):
        """コンテキストの最適化"""
        contexts = self.context_store[session_id]
        
        # 重要度と時間でソート
        contexts.sort(
            key=lambda x: (x['importance'], x['timestamp']),
            reverse=True
        )
        
        # コンテキスト長の制限
        total_length = 0
        optimized_contexts = []
        
        for context in contexts:
            context_length = len(json.dumps(context))
            if total_length + context_length <= self.max_context_length:
                optimized_contexts.append(context)
                total_length += context_length
            else:
                break
        
        self.context_store[session_id] = optimized_contexts

class PromptTemplate:
    """プロンプトテンプレート"""
    def __init__(self, template_path: Path):
        self.templates = self._load_templates(template_path)

    def _load_templates(self, template_path: Path) -> Dict[str, str]:
        """テンプレートの読み込み"""
        with open(template_path) as f:
            return json.load(f)

    def get_prompt(self, 
                  template_key: str,
                  context: Dict[str, Any],
                  **kwargs) -> str:
        """プロンプトの生成"""
        if template_key not in self.templates:
            raise ValueError(f"Template not found: {template_key}")

        template = self.templates[template_key]
        return template.format(
            context=self._format_context(context),
            **kwargs
        )

    def _format_context(self, context: Dict[str, Any]) -> str:
        """コンテキストのフォーマット"""
        formatted_parts = []
        
        if 'code' in context:
            formatted_parts.append(f"コード:\n{context['code']}\n")
        
        if 'metrics' in context:
            formatted_parts.append(f"メトリクス:\n{context['metrics']}\n")
        
        if 'analysis' in context:
            formatted_parts.append(f"解析結果:\n{context['analysis']}\n")
        
        return "\n".join(formatted_parts)

class SearchOptimizer:
    """検索最適化"""
    def __init__(self, embedding_model: CustomEmbeddingModel):
        self.embedding_model = embedding_model
        self.search_cache: Dict[str, List[SearchResult]] = {}

    async def optimize_search(self, 
                            query: str,
                            content_type: ContentType,
                            recent_contexts: List[Dict[str, Any]]
                            ) -> List[SearchResult]:
        """検索の最適化"""
        # クエリの拡張
        expanded_query = await self._expand_query(query, recent_contexts)
        
        # キャッシュチェック
        cache_key = f"{expanded_query}:{content_type.value}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        # 埋め込みの生成
        query_embedding = await self.embedding_model.encode(
            [expanded_query],
            content_type
        )
        
        # 検索実行
        results = await self._execute_search(
            query_embedding,
            content_type
        )
        
        # 結果の後処理
        processed_results = await self._post_process_results(
            results,
            recent_contexts
        )
        
        # キャッシュに保存
        self.search_cache[cache_key] = processed_results
        
        return processed_results

    async def _expand_query(self,
                           query: str,
                           recent_contexts: List[Dict[str, Any]]
                           ) -> str:
        """クエリの拡張"""
        # 最近のコンテキストから関連キーワードを抽出
        keywords = []
        for context in recent_contexts[-3:]:  # 直近3つのコンテキストを使用
            if 'keywords' in context:
                keywords.extend(context['keywords'])
        
        # クエリにキーワードを追加
        if keywords:
            expanded_query = f"{query} {' '.join(keywords)}"
        else:
            expanded_query = query
        
        return expanded_query

    async def _post_process_results(self,
                                  results: List[SearchResult],
                                  recent_contexts: List[Dict[str, Any]]
                                  ) -> List[SearchResult]:
        """検索結果の後処理"""
        # コンテキストに基づいて結果をフィルタリング
        filtered_results = []
        for result in results:
            # 重複チェック
            if not self._is_duplicate(result, filtered_results):
                # スコアの調整
                adjusted_score = await self._adjust_score(
                    result,
                    recent_contexts
                )
                result.score = adjusted_score
                filtered_results.append(result)
        
        # スコアでソート
        filtered_results.sort(key=lambda x: x.score, reverse=True)
        
        return filtered_results

    def _is_duplicate(self,
                     result: SearchResult,
                     existing_results: List[SearchResult]
                     ) -> bool:
        """重複チェック"""
        for existing in existing_results:
            if self._calculate_similarity(result.content, existing.content) > 0.9:
                return True
        return False

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """テキスト類似度の計算"""
        # 簡易的な類似度計算（実際にはより洗練された方法を使用）
        words1 = set(text1.split())
        words2 = set(text2.split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

# 使用例
async def advanced_rag_example():
    # 設定
    embedding_config = EmbeddingConfig(
        model_name="sentence-transformers/all-mpnet-base-v2",
        max_seq_length=512
    )

    # モデルとコンポーネントの初期化
    embedding_model = CustomEmbeddingModel(embedding_config)
    context_manager = ContextManager()
    prompt_template = PromptTemplate(Path("templates/prompts.json"))
    search_optimizer = SearchOptimizer(embedding_model)

    # セッションの開始
    session_id = str(uuid4())

    # コンテキストの追加
    await context_manager.add_context(
        session_id,
        {
            "code": "IDENTIFICATION DIVISION...",
            "metrics": {"complexity": 10},
            "keywords": ["COBOL", "complexity"]
        }
    )

    # クエリ処理
    query = "プログラムの複雑度を説明してください"
    
    # 関連コンテキストの取得
    relevant_contexts = await context_manager.get_context(
        session_id,
        query
    )

    # 検索の最適化
    search_results = await search_optimizer.optimize_search(
        query,
        ContentType.METRICS,
        relevant_contexts
    )

    # プロンプトの生成
    prompt = prompt_template.get_prompt(
        "metrics_explanation",
        relevant_contexts[0],
        query=query
    )

    print(f"Generated prompt: {prompt}")
```