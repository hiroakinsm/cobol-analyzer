classDiagram
    %% Application Core
    class ApplicationServer {
        -config: ServerConfig
        -taskManager: TaskManager
        -pipelineManager: PipelineManager
        -resultManager: ResultManager
        +initialize(): void
        +startAnalysis(source: Source): AnalysisResult
        +getStatus(taskId: UUID): TaskStatus
    }

    %% AI/RAG Service
    class AIServer {
        -config: AIServerConfig
        -ragSystem: RAGSystem
        -sentenceTransformer: SentenceTransformer
        -vectorDB: VectorDB
        +generateContent(request: ContentRequest): ContentResponse
        +embedText(text: string): Vector
        +search(query: string): SearchResult
    }

    %% Database Management
    class PostgresManager {
        -config: PostgresConfig
        -connectionPool: Pool
        +executeQuery(query: string): QueryResult
        +executeTransaction(queries: List~Query~): void
        #handleError(error: Error): void
    }

    class MongoManager {
        -config: MongoConfig
        -client: MongoClient
        +storeAST(ast: AST): void
        +retrieveAST(id: UUID): AST
        #handleError(error: Error): void
    }

    %% Master Data Management
    class MasterDataManager {
        -dbManager: PostgresManager
        -cache: Cache
        +getEnvironmentMaster(): EnvironmentMaster
        +getSingleAnalysisMaster(): SingleAnalysisMaster
        +getSummaryAnalysisMaster(): SummaryAnalysisMaster
        +getDashboardMaster(): DashboardMaster
        +getDocumentMaster(): DocumentMaster
        +getBenchmarkMaster(): BenchmarkMaster
    }

    %% Configuration Management
    class ConfigurationManager {
        -config: Dict
        -envManager: EnvironmentManager
        +loadConfig(): void
        +getServerConfig(): ServerConfig
        +getDatabaseConfig(): DatabaseConfig
        +getAnalysisConfig(): AnalysisConfig
    }

    %% Error Management
    class ErrorManager {
        -logger: Logger
        -notifier: ErrorNotifier
        +handleError(error: Error): void
        +logError(error: Error): void
        +notifyAdmin(error: Error): void
    }

    %% Health Check
    class HealthChecker {
        -services: List~Service~
        -interval: int
        +checkHealth(): HealthStatus
        +monitorServices(): void
        -notifyIssue(issue: Issue): void
    }

    %% Cache Management
    class CacheManager {
        -vectorCache: VectorCache
        -resultCache: ResultCache
        -metadataCache: MetadataCache
        +getCached(key: string): CachedData
        +setCached(key: string, data: any): void
        -cleanupCache(): void
    }

    %% Relationships
    ApplicationServer --> TaskManager
    ApplicationServer --> PipelineManager
    ApplicationServer --> ResultManager
    ApplicationServer --> ErrorManager
    ApplicationServer --> HealthChecker
    AIServer --> RAGSystem
    AIServer --> VectorDB
    MasterDataManager --> PostgresManager
    ConfigurationManager --> EnvironmentManager