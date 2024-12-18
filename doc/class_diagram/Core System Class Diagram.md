classDiagram
    %% Core Analysis Framework
    class AnalysisEngine {
        -taskManager: TaskManager
        -pipelineManager: PipelineManager
        -resultManager: ResultManager
        +analyze(sourceId: UUID): AnalysisResult
        +analyzeBatch(sourceIds: List~UUID~): BatchAnalysisResult
    }

    %% Base Components
    class TaskManager {
        -activeTasks: Dict~UUID, Task~
        -taskQueue: PriorityQueue
        +submitTask(context: TaskContext): UUID
        +processTask(taskId: UUID): void
        +getTaskStatus(taskId: UUID): TaskStatus
    }

    class PipelineManager {
        -stages: List~AnalysisStage~
        -currentPipeline: Pipeline
        +createPipeline(config: PipelineConfig): Pipeline
        +executePipeline(pipeline: Pipeline): void
    }

    class ResultManager {
        -dbManager: DatabaseManager
        -cacheManager: CacheManager
        +storeResult(result: AnalysisResult): void
        +getResult(taskId: UUID): AnalysisResult
        +aggregateResults(taskIds: List~UUID~): SummaryResult
    }

    %% Abstract Base Classes
    class AnalysisStage {
        <<abstract>>
        #context: AnalysisContext
        #logger: Logger
        +prepare(): void
        +execute(): void
        +cleanup(): void
    }

    class Pipeline {
        <<abstract>>
        #stages: List~AnalysisStage~
        #context: PipelineContext
        +addStage(stage: AnalysisStage): void
        +execute(): void
        +rollback(): void
    }

    %% Relationships
    AnalysisEngine -- TaskManager
    AnalysisEngine -- PipelineManager
    AnalysisEngine -- ResultManager
    PipelineManager -- Pipeline
    Pipeline -- AnalysisStage