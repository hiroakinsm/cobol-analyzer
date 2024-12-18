classDiagram
    %% Core Analysis Classes
    class AnalysisController {
        -taskManager: TaskManager
        -sourceManager: SourceManager
        -metricsEngine: MetricsEngine
        +initializeAnalysis(source: Source): void
        +executeAnalysis(): AnalysisResult
        +handleAnalysisCompletion(result: Result): void
    }

    class TaskManager {
        -activeTasks: Map~UUID, TaskStatus~
        -taskHistory: Map~UUID, TaskHistory~
        +createTask(type: TaskType, source: Source): Task
        +updateTaskStatus(taskId: UUID, status: Status): void
        +isTaskComplete(taskId: UUID): boolean
        -validateTaskExecution(): boolean
    }

    class SourceManager {
        -sourceRepository: SourceRepository
        -analysisSummary: Map~String, AnalysisStatus~
        +validateSource(path: String): ValidationResult
        +checkAnalysisStatus(source: Source): AnalysisStatus
        +registerAnalysisResult(source: Source): void
    }

    %% Application Control Classes
    class ServiceController {
        -sourceValidator: SourceValidator
        -dependencyChecker: DependencyChecker
        -coordinators: Map~TaskType, Coordinator~
        +handleSourceSelection(sources: List~Source~): void
        +initiateAnalysis(type: AnalysisType): void
        +monitorProgress(): ProgressStatus
    }

    class SourceValidator {
        -sourceManager: SourceManager
        +validateSources(sources: List~Source~): ValidationResult
        +checkPreviousAnalysis(source: Source): boolean
        -validateSourceFormat(source: Source): boolean
    }

    class DependencyChecker {
        -sourceManager: SourceManager
        +checkDependencies(sources: List~Source~): DependencyResult
        +identifyMissingAnalysis(): List~Source~
        -validateDependencyChain(): boolean
    }

    class SingleAnalysisCoordinator {
        -analysisController: AnalysisController
        -taskMonitor: TaskMonitor
        +processSingleSource(source: Source): void
        +checkAnalysisStatus(): AnalysisStatus
        -handleAnalysisCompletion(): void
    }

    class MultiAnalysisCoordinator {
        -analysisController: AnalysisController
        -taskMonitor: TaskMonitor
        -dependencyManager: DependencyManager
        +processMultipleSource(sources: List~Source~): void
        +manageDependencies(): void
        -coordinateAnalysis(): void
    }

    %% UI Interface Classes
    class AnalysisMenu {
        -sourceSelector: SourceSelector
        -taskSelector: TaskSelector
        +showMenu(): void
        +handleSelection(selection: Selection): void
    }

    class SourceSelector {
        -sourceManager: SourceManager
        +listAvailableSources(): List~Source~
        +handleSourceSelection(sources: List~Source~): void
        -validateSelection(selection: Selection): boolean
    }

    class TaskSelector {
        -taskManager: TaskManager
        +getAvailableTasks(): List~TaskType~
        +selectTask(taskType: TaskType): void
        -validateTaskSelection(selection: Selection): boolean
    }

    %% Relationships
    AnalysisController o-- TaskManager
    AnalysisController o-- SourceManager
    
    ServiceController o-- SourceValidator
    ServiceController o-- DependencyChecker
    ServiceController o-- SingleAnalysisCoordinator
    ServiceController o-- MultiAnalysisCoordinator

    SingleAnalysisCoordinator --> AnalysisController
    MultiAnalysisCoordinator --> AnalysisController

    AnalysisMenu o-- SourceSelector
    AnalysisMenu o-- TaskSelector
    
    SourceSelector --> SourceManager
    TaskSelector --> TaskManager

    %% Usage Flow
    ServiceController ..> TaskManager: monitors
    DependencyChecker ..> SourceManager: validates
    TaskManager ..> SourceManager: coordinates