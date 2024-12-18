classDiagram
    %% Core RAG Components
    class RAGSystem {
        -llamaModel: LLMModel
        -embedder: SentenceTransformer
        -vectorStore: VectorStore
        -pipeline: RAGPipeline
        +process(query: Query): Response
        +generateContent(context: Context): Content
    }

    class LLMModel {
        -model: Llama
        -configuration: ModelConfig
        +initialize(modelPath: string)
        +generate(prompt: string): string
        -quantize(bits: int)
    }

    class SentenceTransformer {
        -model: TransformerModel
        -config: EmbeddingConfig
        +encode(text: string): Vector
        +batchEncode(texts: List~string~): List~Vector~
    }

    %% RAG Pipeline Components
    class RAGPipeline {
        -contextBuilder: ContextBuilder
        -queryGenerator: QueryGenerator
        -retriever: Retriever
        -reranker: Reranker
        -promptGenerator: PromptGenerator
        +executePipeline(input: Input): Response
    }

    class ContextBuilder {
        -astReader: ASTReader
        -metadataReader: MetadataReader
        +buildContext(source: Source): Context
    }

    class Retriever {
        -vectorStore: VectorStore
        -config: RetrievalConfig
        +retrieve(query: Query): List~Document~
        -scoreDocuments(documents: List~Document~): List~Score~
    }

    class Reranker {
        -model: RankingModel
        -config: RankingConfig
        +rerank(documents: List~Document~): List~Document~
        -calculateRelevance(doc: Document): float
    }

    %% ML Components
    class MLProcessor {
        -embedder: SentenceTransformer
        -analyzer: CodeAnalyzer
        +processSource(source: Source): Analysis
    }

    class PatternAnalyzer {
        -clusterer: Clusterer
        -similarityCalculator: SimilarityCalculator
        +findPatterns(embeddings: List~Vector~): Patterns
    }

    class AnomalyDetector {
        -detector: Detector
        -threshold: float
        +detectAnomalies(embeddings: List~Vector~): Anomalies
    }

    %% Generation Components
    class ContentGenerator {
        -llm: LLMModel
        -templates: Templates
        +generateFlowchart(analysis: Analysis): string
        +generateSequenceDiagram(analysis: Analysis): string
        +generateMetrics(analysis: Analysis): Metrics
    }

    %% Relationships
    RAGSystem *-- LLMModel
    RAGSystem *-- SentenceTransformer
    RAGSystem *-- RAGPipeline

    RAGPipeline *-- ContextBuilder
    RAGPipeline *-- Retriever
    RAGPipeline *-- Reranker

    MLProcessor -- SentenceTransformer
    MLProcessor *-- PatternAnalyzer
    MLProcessor *-- AnomalyDetector

    ContentGenerator -- LLMModel
    ContentGenerator -- MLProcessor