# /home/administrator/ai-server/src/rag/rag_use_cases.py
# /srv/cobol-analyzer/src/rag/use_cases.py

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import asyncio
import logging
from pathlib import Path
import aiocache
from cachetools import TTLCache, LRUCache
import aioredis
from functools import wraps

@dataclass
class CacheConfig:
    """キャッシュ設定"""
    local_cache_size: int = 1000
    local_cache_ttl: int = 3600  # 1時間
    redis_url: str = "redis://localhost"
    redis_ttl: int = 7200  # 2時間
    analysis_cache_ttl: int = 86400  # 24時間
    enable_distributed_cache: bool = True

class RAGCacheManager:
    """RAGキャッシュ管理"""
    def __init__(self, config: CacheConfig):
        self.config = config
        self.local_cache = TTLCache(
            maxsize=config.local_cache_size,
            ttl=config.local_cache_ttl
        )
        self.analysis_cache = LRUCache(maxsize=config.local_cache_size)
        
        if config.enable_distributed_cache:
            self.redis = aioredis.from_url(config.redis_url)
        else:
            self.redis = None

        self.logger = logging.getLogger(__name__)

    def cache_key(func):
        """キャッシュキー生成デコレータ"""
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # キャッシュキーの生成
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # ローカルキャッシュチェック
            if cache_key in self.local_cache:
                return self.local_cache[cache_key]

            # 分散キャッシュチェック
            if self.redis:
                cached = await self.redis.get(cache_key)
                if cached:
                    self.local_cache[cache_key] = cached
                    return cached

            # 結果の生成
            result = await func(self, *args, **kwargs)
            
            # キャッシュへの保存
            if result is not None:
                self.local_cache[cache_key] = result
                if self.redis:
                    await self.redis.set(
                        cache_key,
                        result,
                        ex=self.config.redis_ttl
                    )
            
            return result
        return wrapper

class COBOLAnalysisRAG:
    """COBOL解析用RAGシステム"""
    def __init__(self,
                 rag_system: RAGSystem,
                 embedding_model: CustomEmbeddingModel,
                 context_manager: ContextManager,
                 search_optimizer: SearchOptimizer,
                 prompt_template: PromptTemplate,
                 cache_config: CacheConfig = None):
        self.rag = rag_system
        self.embedding_model = embedding_model
        self.context_manager = context_manager
        self.search_optimizer = search_optimizer
        self.prompt_template = prompt_template
        self.cache_manager = RAGCacheManager(cache_config or CacheConfig())
        self.logger = logging.getLogger(__name__)
        self._setup_performance_monitoring()

    def _setup_performance_monitoring(self):
        """パフォーマンスモニタリングの設定"""
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "average_latency": 0.0,
            "error_count": 0
        }

    @RAGCacheManager.cache_key
    async def answer_analysis_question(self,
                                     question: AnalysisQuestion,
                                     session_id: Optional[str] = None) -> str:
        """解析に関する質問への回答"""
        start_time = datetime.utcnow()
        self.performance_metrics["total_requests"] += 1
        
        try:
            session_id = session_id or str(uuid4())
            
            # 解析結果の取得（キャッシュ付き）
            analysis_results = await self._get_cached_analysis_results(
                question.source_id,
                question.context_type
            )

            # コンテキストの最適化
            optimized_context = await self._optimize_context(
                session_id,
                analysis_results,
                question
            )

            # 検索の最適化
            search_results = await self.search_optimizer.optimize_search(
                question.question,
                question.context_type,
                optimized_context
            )

            # プロンプトの生成と最適化
            prompt = await self._generate_optimized_prompt(
                question,
                search_results,
                optimized_context
            )

            # 応答の生成
            response = await self.rag.generate_response(
                prompt,
                {"session_id": session_id}
            )

            # パフォーマンス統計の更新
            self._update_performance_metrics(start_time)
            
            return response

        except Exception as e:
            self.performance_metrics["error_count"] += 1
            self.logger.error(f"Failed to answer analysis question: {str(e)}")
            raise

    async def _get_cached_analysis_results(self,
                                         source_id: UUID,
                                         context_type: ContentType) -> Dict[str, Any]:
        """キャッシュ付き解析結果の取得"""
        cache_key = f"analysis:{source_id}:{context_type.value}"
        
        # キャッシュチェック
        if cache_key in self.cache_manager.analysis_cache:
            self.performance_metrics["cache_hits"] += 1
            return self.cache_manager.analysis_cache[cache_key]

        # 結果の取得と保存
        results = await self._get_analysis_results(source_id, context_type)
        self.cache_manager.analysis_cache[cache_key] = results
        return results

    async def _optimize_context(self,
                              session_id: str,
                              analysis_results: Dict[str, Any],
                              question: AnalysisQuestion) -> List[Dict[str, Any]]:
        """コンテキストの最適化"""
        # コンテキストの追加と重要度の計算
        await self.context_manager.add_context(
            session_id,
            {
                "analysis_results": analysis_results,
                "metadata": question.metadata,
                "importance": self._calculate_context_importance(question)
            }
        )

        # 関連コンテキストの取得と最適化
        contexts = await self.context_manager.get_context(
            session_id,
            question.question
        )
        
        return self._prioritize_contexts(contexts)
    
    async def _generate_optimized_prompt(self,
                                       question: AnalysisQuestion,
                                       search_results: List[Dict[str, Any]],
                                       contexts: List[Dict[str, Any]]) -> str:
        """最適化されたプロンプトの生成"""
        # プロンプトテンプレートの選択
        template_name = self._select_prompt_template(question.context_type)
        
        return self.prompt_template.get_prompt(
            template_name,
            {
                "question": question.question,
                "search_results": self._filter_relevant_results(search_results),
                "contexts": self._format_contexts(contexts),
                "metadata": question.metadata
            }
        )

    def _select_prompt_template(self, context_type: ContentType) -> str:
        """コンテキストタイプに基づくテンプレート選択"""
        template_mapping = {
            ContentType.CODE: "code_analysis",
            ContentType.METRICS: "metrics_analysis",
            ContentType.DOCUMENTATION: "documentation_analysis",
            ContentType.SECURITY: "security_analysis",
            ContentType.ANALYSIS: "general_analysis"
        }
        return template_mapping.get(context_type, "general_analysis")

    def _calculate_context_importance(self, question: AnalysisQuestion) -> float:
        """コンテキストの重要度計算"""
        # 基本重要度
        importance = 1.0
        
        # メタデータに基づく調整
        if question.metadata:
            if question.metadata.get("priority") == "high":
                importance *= 1.5
            elif question.metadata.get("critical") is True:
                importance *= 2.0
                
        return importance

    def _prioritize_contexts(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """コンテキストの優先順位付け"""
        return sorted(
            contexts,
            key=lambda x: (
                x.get("importance", 0),
                x.get("timestamp", datetime.min)
            ),
            reverse=True
        )

    def _filter_relevant_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """関連性の高い結果のフィルタリング"""
        # スコアに基づくフィルタリング
        threshold = 0.5
        return [
            result for result in results
            if result.get("score", 0) > threshold
        ]

    def _format_contexts(self, contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """コンテキストのフォーマット"""
        formatted_contexts = []
        for ctx in contexts:
            formatted = {
                "content": ctx.get("content", ""),
                "type": ctx.get("type", "unknown"),
                "timestamp": ctx.get("timestamp", datetime.utcnow()).isoformat()
            }
            if metadata := ctx.get("metadata"):
                formatted["metadata"] = metadata
            formatted_contexts.append(formatted)
        return formatted_contexts

    def _update_performance_metrics(self, start_time: datetime):
        """パフォーマンス統計の更新"""
        duration = (datetime.utcnow() - start_time).total_seconds()
        total_requests = self.performance_metrics["total_requests"]
        
        # 平均レイテンシーの更新
        self.performance_metrics["average_latency"] = (
            (self.performance_metrics["average_latency"] * (total_requests - 1) + duration)
            / total_requests
        )

    async def cleanup(self):
        """リソースのクリーンアップ"""
        if self.cache_manager.redis:
            await self.cache_manager.redis.close()
