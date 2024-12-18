classDiagram
    %% Database Access Interfaces
    class IRepository~T~ {
        <<interface>>
        +get(id: Any): Optional~T~
        +get_many(filter_dict: Dict): List~T~
        +add(entity: T): Any
        +update(entity: T): bool
        +delete(id: Any): bool
    }

    class DatabaseConnection {
        <<abstract>>
        +connect(): void
        +disconnect(): void
        +begin_transaction(): void
        +commit(): void
        +rollback(): void
    }

    %% Concrete Implementations
    class PostgresRepository~T~ {
        -db: PostgresManager
        -model_class: type[T]
        -table_name: str
        +get(id: Any): Optional~T~
        +get_many(filter_dict: Dict): List~T~
    }

    class MongoRepository~T~ {
        -db: MongoManager
        -model_class: type[T]
        -collection_name: str
        +get(id: Any): Optional~T~
        +get_many(filter_dict: Dict): List~T~
    }

    %% Specific Repositories
    class AnalysisTaskRepository {
        +get_pending_tasks(): List~AnalysisTask~
        +update_status(task_id: UUID, status: AnalysisStatus): bool
    }

    class AnalysisResultRepository {
        +get_results_by_source(source_id: UUID): List~AnalysisResult~
        +store_stage_result(task_id: UUID, stage: str, result: Dict): void
    }

    class ASTRepository {
        +get_ast_by_source(source_id: UUID): Optional~ASTData~
        +update_ast(source_id: UUID, ast_data: Dict): bool
    }

    %% Database Managers
    class DatabaseManager {
        -config: DatabaseConfig
        -connections: Dict
        +get_connection(name: str): DatabaseConnection
        +close_all(): void
    }

    class PostgresManager {
        -pool: Pool
        +execute(query: str, *args): str
        +fetch(query: str, *args): List~Dict~
        +fetchrow(query: str, *args): Optional~Dict~
    }

    class MongoManager {
        -client: MongoClient
        -db: Database
        +get_collection(name: str): Collection
        +aggregate(pipeline: List): List~Dict~
    }

    %% Cache Management
    class CacheManager {
        -ttl: timedelta
        -cache: Dict
        -timestamps: Dict
        +get_cached_result(key: str): Optional~Any~
        +set_cached_result(key: str, value: Any): void
        -is_valid(key: str): bool
    }

    %% Relationships
    IRepository <|.. PostgresRepository
    IRepository <|.. MongoRepository
    PostgresRepository <|-- AnalysisTaskRepository
    PostgresRepository <|-- AnalysisResultRepository
    MongoRepository <|-- ASTRepository
    DatabaseConnection <|-- PostgresManager
    DatabaseConnection <|-- MongoManager