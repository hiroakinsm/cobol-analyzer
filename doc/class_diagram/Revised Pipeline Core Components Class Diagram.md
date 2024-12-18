classDiagram
    %% Core Pipeline Components
    class TaskManager {
        -db_functions: DatabaseFunctions
        -active_tasks: Dict~UUID, Task~
        -task_queue: PriorityQueue
        -processing_semaphore: Semaphore
        +submit_task(context: TaskContext): UUID
        +process_tasks(): void
    }

    class Pipeline {
        -stages: List~PipelineStage~
        -context: PipelineContext
        +add_stage(stage: PipelineStage): void
        +execute(): void
    }

    class PipelineStage {
        <<abstract>>
        #name: str
        #task_manager: TaskManager
        +process(context: TaskContext, data: Dict): Dict
        #handle_error(context: TaskContext, error: Exception): void
    }

    %% Task Management
    class TaskContext {
        +task_id: UUID
        +source_id: UUID
        +priority: TaskPriority
        +timeout: int
        +max_retries: int
        +retry_count: int
        +metadata: Dict
    }

    class PipelineError {
        +message: str
        +task_id: UUID
        +recoverable: bool
    }

    %% Analysis Stages
    class AnalysisStage {
        <<abstract>>
        -recovery_handlers: Dict~str, Callable~
        +analyze(context: TaskContext, data: Dict): Dict
        #cache_result(context: TaskContext, result: Dict): void
    }

    class ASTParsingStage {
        +analyze(context: TaskContext, data: Dict): Dict
        -parse_ast(source_code: str): Dict
    }

    class MetricsAnalysisStage {
        +analyze(context: TaskContext, data: Dict): Dict
        -calculate_metrics(ast_data: Dict): Dict
    }

    %% Relationships
    PipelineStage <|-- AnalysisStage
    AnalysisStage <|-- ASTParsingStage
    AnalysisStage <|-- MetricsAnalysisStage
    Pipeline *-- PipelineStage
    TaskManager -- TaskContext