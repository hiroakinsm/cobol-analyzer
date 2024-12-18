classDiagram
    %% RAG System Core
    class RAGController {
        -criteriaEvaluator: CriteriaEvaluator
        -pipeline: RAGPipeline
        -llmModel: LLMModel
        +processRequest(request: RAGRequest): RAGResponse
        +evaluateRAGNecessity(context: Context): boolean
    }

    class CriteriaEvaluator {
        -contentEvaluator: ContentEvaluator
        -taskEvaluator: TaskEvaluator
        -contextEvaluator: ContextEvaluator
        +evaluateCriteria(request: RAGRequest): EvaluationResult
        -calculateConfidenceScore(): float
    }

    class RAGPipeline {
        -contextBuilder: ContextBuilder
        -queryGenerator: QueryGenerator
        -retriever: Retriever
        -reranker: Reranker
        -promptGenerator: PromptGenerator
        +executePipeline(context: Context): PipelineResult
        -validatePipelineSteps(): ValidationResult
    }

    %% Sentence Transformer Components
    class TransformerProcessor {
        -preprocessor: TextPreprocessor
        -tokenizer: Tokenizer
        -embeddingGenerator: EmbeddingGenerator
        -batchController: BatchController
        +processText(text: String): Embedding
        +processBatch(texts: List~String~): List~Embedding~
    }

    class BatchController {
        -chunkProcessor: ChunkProcessor
        -batchOptimizer: BatchOptimizer
        -config: BatchConfig
        +processBatch(data: List~String~): BatchResult
        -optimizeBatchSize(size: int): int
    }

    class EmbeddingGenerator {
        -model: SentenceTransformer
        -optimizer: EmbeddingOptimizer
        +generateEmbedding(tokens: List~Token~): Embedding
        -optimizeEmbedding(embedding: Embedding): Embedding
    }

    %% Vector Database Components
    class VectorController {
        -vectorStore: VectorStore
        -cacheController: CacheController
        -metadataManager: MetadataManager
        +storeVector(vector: Vector): void
        +searchVectors(query: Vector, k: int): List~Vector~
    }

    class CacheController {
        -frequencyCache: FrequencyCache
        -temporalCache: TemporalCache
        -evictionManager: EvictionManager
        +cacheVector(vector: Vector): void
        +getCachedVector(id: String): Optional~Vector~
        -evictStaleEntries(): void
    }

    class VectorStore {
        -index: VectorIndex
        -metadata: VectorMetadata
        -storageManager: StorageManager
        +insertVector(vector: Vector): void
        +searchNearest(query: Vector, k: int): List~Vector~
        -optimizeIndex(): void
    }

    %% Cache Strategy Components
    class FrequencyCache {
        -frequencyMap: Map~String, Integer~
        -cacheSize: int
        +updateFrequency(key: String): void
        +getFrequentItems(): List~CacheItem~
    }

    class TemporalCache {
        -timeMap: Map~String, Timestamp~
        -timeWindow: Duration
        +updateTimestamp(key: String): void
        +getRecentItems(): List~CacheItem~
    }

    class EvictionManager {
        -evictionStrategy: EvictionStrategy
        -cacheMonitor: CacheMonitor
        +evictItems(): List~String~
        -selectItemsForEviction(): List~String~
    }

    %% Relationships
    RAGController *-- CriteriaEvaluator
    RAGController *-- RAGPipeline
    
    TransformerProcessor *-- BatchController
    TransformerProcessor *-- EmbeddingGenerator
    
    VectorController *-- VectorStore
    VectorController *-- CacheController
    
    CacheController *-- FrequencyCache
    CacheController *-- TemporalCache
    CacheController *-- EvictionManager
    
    %% Dependencies
    RAGPipeline ..> TransformerProcessor: uses
    RAGPipeline ..> VectorController: uses
    EmbeddingGenerator ..> VectorStore: stores
    VectorStore ..> CacheController: caches