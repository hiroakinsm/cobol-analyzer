classDiagram
    class AnalysisController {
        -taskManager: TaskManager
        -pipelineManager: PipelineManager
        -resultManager: ResultManager
        +analyzeSingle(source: Source): AnalysisResult
        +analyzeBatch(sources: List~Source~): BatchResult
    }

    class PipelineManager {
        -stages: List~AnalysisStage~
        -validators: List~Validator~
        +createPipeline(config: Config): Pipeline
        +executePipeline(pipeline: Pipeline): Result
    }

    class ContentGenerator {
        -ragSystem: RAGSystem
        -templateEngine: TemplateEngine
        -visualizer: Visualizer
        +generateDocument(data: AnalysisData): Document
        +generateDashboard(data: AnalysisData): Dashboard
    }

    class RAGSystem {
        -llm: LLMModel
        -embedder: SentenceTransformer
        -vectorStore: VectorStore
        +enhance(content: String): String
        +generateContent(context: Context): String
    }

    class DatabaseManager {
        -postgresClient: PostgresClient
        -mongoClient: MongoClient
        -vectorDB: VectorDB
        +storeResults(results: Results): void
        +retrieveData(id: UUID): Data
    }

    class WebController {
        -uiRenderer: UIRenderer
        -responseHandler: ResponseHandler
        +renderDashboard(data: DashboardData): void
        +renderDocument(data: DocumentData): void
    }

    AnalysisController --> PipelineManager
    AnalysisController --> ContentGenerator
    ContentGenerator --> RAGSystem
    AnalysisController --> DatabaseManager
    ContentGenerator --> WebController