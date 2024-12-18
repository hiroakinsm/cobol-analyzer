classDiagram
    %% Common Analysis Foundation
    class AnalysisController {
        -parser: ParserFramework
        -metricsEngine: MetricsEngine
        -analysisEngine: AnalysisEngine
        +initializeAnalysis(source: Source): void
        +executeAnalysis(): AnalysisResult
    }

    class ContentGenerationCore {
        -templates: List~Template~
        -generators: List~Generator~
        +generateBaseContent(analysis: Analysis): Content
        +requestEnhancement(content: Content): void
    }

    class DocumentGenerationCore {
        -templates: List~Template~
        -formatters: List~Formatter~
        +generateBaseDocument(analysis: Analysis): Document
        +requestEnhancement(document: Document): void
    }

    %% Application Server Control
    class ServiceController {
        -taskMonitor: TaskMonitor
        -multiSourceCoordinator: MultiSourceCoordinator
        +startAnalysis(source: Source): void
        +monitorProgress(): void
        +handleCompletion(result: Result): void
    }

    class TaskMonitor {
        -activeTasksMap: Map~UUID, TaskStatus~
        +checkTaskStatus(taskId: UUID): TaskStatus
        +updateTaskStatus(taskId: UUID, status: Status): void
        +notifyCompletion(taskId: UUID): void
    }

    class MultiSourceCoordinator {
        -sourceMap: Map~UUID, List~Source~~
        +registerSources(sources: List~Source~): void
        +trackProgress(sourceId: UUID): void
        +checkCompletion(): boolean
    }

    %% RAG/ML System
    class ContentFinalizer {
        -llm: LLMModel
        -vectorStore: VectorStore
        +enhanceContent(content: Content): EnhancedContent
        +validateContent(content: Content): ValidationResult
    }

    class DocumentFinalizer {
        -llm: LLMModel
        -vectorStore: VectorStore
        +enhanceDocument(document: Document): EnhancedDocument
        +validateDocument(document: Document): ValidationResult
    }

    class PatternAnalyzer {
        -embedder: SentenceTransformer
        -vectorStore: VectorStore
        +analyzePatterns(code: String): PatternResult
        +storePatterns(patterns: List~Pattern~): void
    }

    %% Relationships
    AnalysisController --> ServiceController
    ContentGenerationCore --> ContentFinalizer
    DocumentGenerationCore --> DocumentFinalizer

    ServiceController *-- TaskMonitor
    ServiceController *-- MultiSourceCoordinator

    ContentFinalizer --> VectorStore
    DocumentFinalizer --> VectorStore
    PatternAnalyzer --> VectorStore

    %% Core Services Integration
    ServiceController ..> AnalysisController: controls
    MultiSourceCoordinator ..> ContentGenerationCore: coordinates
    TaskMonitor ..> PatternAnalyzer: triggers analysis