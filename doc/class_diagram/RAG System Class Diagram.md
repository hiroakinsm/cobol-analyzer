classDiagram
    %% Application Core
    class AnalysisController {
        -analysisService: AnalysisService
        -contentGenerationService: ContentGenerationService
        -webController: WebController
        +analyzeSource(sourceId: UUID): AnalysisResult
        +generateDashboard(analysisId: UUID): DashboardContent
        +generateDocument(analysisId: UUID): DocumentContent
    }

    class AnalysisService {
        -ragSystem: RAGSystem
        -mlProcessor: MLProcessor
        -dbManager: DatabaseManager
        +performAnalysis(source: Source): Analysis
        +storeResults(analysis: Analysis): void
    }

    %% RAG System Components
    class RAGSystem {
        -llm: LLMModel
        -embedder: SentenceTransformer
        -vectorStore: VectorStore
        +generateContent(context: Context): Content
        -processQuery(query: Query): Response
    }

    class LLMModel {
        -model: Llama
        -config: ModelConfig
        +initialize(path: string): void
        +generate(prompt: string): string
        -quantize(bits: int): void
    }

    class SentenceTransformer {
        -model: TransformerModel
        -config: EmbeddingConfig
        +encode(text: string): Vector
        +batchEncode(texts: List~string~): List~Vector~
    }

    class VectorStore {
        -store: VectorDatabase
        -cache: Cache
        +store(vectors: List~Vector~): void
        +search(query: Vector): List~Document~
    }

    %% Content Generation
    class ContentGenerationService {
        -dashboardGenerator: DashboardGenerator
        -documentGenerator: DocumentGenerator
        +createDashboard(data: AnalysisData): DashboardContent
        +createDocument(data: AnalysisData): DocumentContent
    }

    class DashboardGenerator {
        -templates: List~Template~
        -chartGenerator: ChartGenerator
        +generateContent(data: AnalysisData): DashboardContent
        -createVisualization(data: AnalysisData): Visualization
    }

    class DocumentGenerator {
        -templates: List~Template~
        -mermaidGenerator: MermaidGenerator
        +generateContent(data: AnalysisData): DocumentContent
        -createDiagrams(data: AnalysisData): List~Diagram~
    }

    %% Web Interface
    class WebController {
        -renderer: UIRenderer
        +renderDashboard(content: DashboardContent): void
        +renderDocument(content: DocumentContent): void
        -handleUserInteraction(event: UIEvent): void
    }

    class UIRenderer {
        -dashboardComponent: DashboardComponent
        -documentComponent: DocumentComponent
        +render(content: Content): void
        -updateUI(component: UIComponent): void
    }

    %% Storage
    class DatabaseManager {
        -postgresClient: PostgresClient
        -mongoClient: MongoClient
        -vectorDb: VectorDatabase
        +storeAnalysisResult(result: AnalysisResult): void
        +storeVectors(vectors: List~Vector~): void
    }

    %% Relationships
    AnalysisController --> AnalysisService
    AnalysisController --> ContentGenerationService
    AnalysisController --> WebController

    AnalysisService --> RAGSystem
    AnalysisService --> DatabaseManager

    RAGSystem *-- LLMModel
    RAGSystem *-- SentenceTransformer
    RAGSystem *-- VectorStore

    ContentGenerationService *-- DashboardGenerator
    ContentGenerationService *-- DocumentGenerator

    WebController *-- UIRenderer

    %% Data Flow
    AnalysisService ..> DatabaseManager: stores results
    ContentGenerationService ..> WebController: provides content
    DatabaseManager ..> ContentGenerationService: provides data