classDiagram
    %% Database Access Layer
    class DatabaseManager {
        -postgresManager: PostgresManager
        -mongoManager: MongoManager
        -vectorManager: VectorDBManager
        +initialize(): void
        +validateConnections(): ConnectionStatus
    }

    class PostgresManager {
        -connectionPool: ConnectionPool
        -transactionManager: TransactionManager
        +executeQuery(query: Query): Result
        +beginTransaction(): Transaction
        -handleError(error: Error): void
    }

    class MongoManager {
        -client: MongoClient
        -collections: Map~String, Collection~
        +insertDocument(collection: String, doc: Document): void
        +findDocuments(collection: String, query: Query): List~Document~
        -ensureIndexes(): void
    }

    class VectorDBManager {
        -vectorStore: VectorStore
        -cache: Cache
        +storeVector(vector: Vector, metadata: Metadata): void
        +searchSimilar(vector: Vector, k: int): List~Vector~
        -optimizeCache(): void
    }

    %% Repository Layer
    class MasterDataRepository {
        -dbManager: DatabaseManager
        +getEnvironmentSettings(): List~Setting~
        +getAnalysisSettings(): List~Setting~
        +getBenchmarkSettings(): List~Setting~
        +updateSettings(type: String, settings: Setting): void
    }

    class TransactionDataRepository {
        -dbManager: DatabaseManager
        +recordAnalysisTask(task: Task): void
        +updateTaskStatus(taskId: UUID, status: Status): void
        +getTaskHistory(criteria: Criteria): List~Task~
        -validateTransaction(transaction: Transaction): boolean
    }

    class ASTRepository {
        -mongoManager: MongoManager
        +storeAST(sourceId: UUID, ast: AST): void
        +getAST(sourceId: UUID): AST
        +updateASTMetadata(sourceId: UUID, metadata: Metadata): void
    }

    class VectorRepository {
        -vectorManager: VectorDBManager
        +storeEmbedding(sourceId: UUID, embedding: Vector): void
        +findSimilar(query: Vector, limit: int): List~Result~
        -optimizeStorage(): void
    }

    %% Cache Management
    class CacheManager {
        -resultCache: ResultCache
        -vectorCache: VectorCache
        +cacheResult(key: string, result: Result): void
        +getCachedResult(key: string): Optional~Result~
        -evictStaleData(): void
    }

    %% Entity Relationships
    DatabaseManager *-- PostgresManager
    DatabaseManager *-- MongoManager
    DatabaseManager *-- VectorDBManager

    MasterDataRepository --> DatabaseManager
    TransactionDataRepository --> DatabaseManager
    ASTRepository --> MongoManager
    VectorRepository --> VectorDBManager

    %% Usage Relationships
    PostgresManager ..> CacheManager: uses
    MongoManager ..> CacheManager: uses
    VectorDBManager ..> CacheManager: uses