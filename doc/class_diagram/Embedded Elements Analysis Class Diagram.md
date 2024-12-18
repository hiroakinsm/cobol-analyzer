classDiagram
    class EmbeddedAnalyzer {
        <<abstract>>
        #context: AnalysisContext
        #metrics: MetricsCollector
        +analyze(): AnalysisResult
        #validate(): ValidationResult
    }

    class DatabaseIntegrationAnalyzer {
        -statement_parser: DBStatementParser
        -sql_analyzer: SQLAnalyzer
        -transaction_analyzer: TransactionAnalyzer
        +analyzeDBStatements(): DBAnalysis
        +analyzeSQLPatterns(): SQLPatternAnalysis
        +analyzeTransactions(): TransactionAnalysis
    }

    class AssemblerIntegrationAnalyzer {
        -interface_analyzer: InterfaceAnalyzer
        -data_exchange_analyzer: DataExchangeAnalyzer
        -register_usage_analyzer: RegisterUsageAnalyzer
        +analyzeInterfaces(): InterfaceAnalysis
        +analyzeDataExchange(): DataExchangeAnalysis
        +analyzeRegisterUsage(): RegisterAnalysis
    }

    class BatchProcessingAnalyzer {
        -structure_analyzer: BatchStructureAnalyzer
        -step_analyzer: StepAnalyzer
        -checkpoint_analyzer: CheckpointAnalyzer
        -sort_merge_analyzer: SortMergeAnalyzer
        +analyzeStructure(): StructureAnalysis
        +analyzeSteps(): StepAnalysis
        +analyzeSortMerge(): SortMergeAnalysis
    }

    class ScreenFormAnalyzer {
        -screen_analyzer: ScreenAnalyzer
        -form_analyzer: FormAnalyzer
        -ui_flow_analyzer: UIFlowAnalyzer
        -data_mapping_analyzer: DataMappingAnalyzer
        +analyzeScreens(): ScreenAnalysis
        +analyzeForms(): FormAnalysis
        +analyzeUIFlow(): UIFlowAnalysis
    }

    class EmbeddedElementsReport {
        -database_integration: DBAnalysis
        -assembler_integration: AssemblerAnalysis
        -batch_processing: BatchAnalysis
        -screen_form: ScreenFormAnalysis
        +generateSummary(): Summary
        +getRecommendations(): List~Recommendation~
    }

    EmbeddedAnalyzer <|-- DatabaseIntegrationAnalyzer
    EmbeddedAnalyzer <|-- AssemblerIntegrationAnalyzer
    EmbeddedAnalyzer <|-- BatchProcessingAnalyzer
    EmbeddedAnalyzer <|-- ScreenFormAnalyzer
    DatabaseIntegrationAnalyzer ..> EmbeddedElementsReport
    AssemblerIntegrationAnalyzer ..> EmbeddedElementsReport
    BatchProcessingAnalyzer ..> EmbeddedElementsReport
    ScreenFormAnalyzer ..> EmbeddedElementsReport