classDiagram
    %% Embedded Elements Analysis - Screen/Form Processing
    class ScreenAnalyzer {
        -ast: COBOLAST
        -screenRules: ScreenRules
        +analyzeScreens(): ScreenAnalysis
        +validateScreenLayout(): ValidationResult
    }

    class FormAnalyzer {
        -ast: COBOLAST
        -formRules: FormRules
        +analyzeForms(): FormAnalysis
        +validateFormStructure(): ValidationResult
    }

    class UIFlowAnalyzer {
        -screenAnalysis: ScreenAnalysis
        -formAnalysis: FormAnalysis
        +analyzeUIFlow(): UIFlowAnalysis
        +validateUIFlow(): ValidationResult
    }

    class DataMappingAnalyzer {
        -uiFlowAnalysis: UIFlowAnalysis
        +analyzeDataMapping(): DataMappingAnalysis
        +validateMapping(): ValidationResult
    }

    %% Embedded Elements Analysis - Batch Processing
    class BatchStructureAnalyzer {
        -ast: COBOLAST
        -batchRules: BatchRules
        +analyzeBatchStructure(): BatchAnalysis
        +validateBatchFlow(): ValidationResult
    }

    class StepAnalyzer {
        -batchAnalysis: BatchAnalysis
        +analyzeSteps(): StepAnalysis
        +validateStepFlow(): ValidationResult
    }

    class CheckpointRestartAnalyzer {
        -stepAnalysis: StepAnalysis
        +analyzeCheckpoints(): CheckpointAnalysis
        +validateRecovery(): ValidationResult
    }

    class SortMergeAnalyzer {
        -checkpointAnalysis: CheckpointAnalysis
        +analyzeSortMerge(): SortMergeAnalysis
        +validateOperations(): ValidationResult
    }

    %% Embedded Elements Analysis - Assembler Integration
    class InterfaceAnalyzer {
        -ast: COBOLAST
        -interfaceRules: InterfaceRules
        +analyzeInterfaces(): InterfaceAnalysis
        +validateInterfaces(): ValidationResult
    }

    class DataExchangeAnalyzer {
        -interfaceAnalysis: InterfaceAnalysis
        +analyzeDataExchange(): DataExchangeAnalysis
        +validateExchange(): ValidationResult
    }

    class RegisterUsageAnalyzer {
        -dataExchangeAnalysis: DataExchangeAnalysis
        +analyzeRegisterUsage(): RegisterUsageAnalysis
        +validateUsage(): ValidationResult
    }

    %% Embedded Elements Analysis - Database Integration
    class DBStatementParser {
        -ast: COBOLAST
        -sqlPatterns: List~SQLPattern~
        +parseDBStatements(): DBStatementAnalysis
        +validateStatements(): ValidationResult
    }

    class SQLAnalyzer {
        -dbStatements: DBStatementAnalysis
        +analyzeSQL(): SQLAnalysis
        +validateSQL(): ValidationResult
    }

    class TransactionAnalyzer {
        -sqlAnalysis: SQLAnalysis
        +analyzeTransactions(): TransactionAnalysis
        +validateTransactions(): ValidationResult
    }

    class AccessPatternAnalyzer {
        -transactionAnalysis: TransactionAnalysis
        +analyzeAccessPatterns(): AccessPatternAnalysis
        +validatePatterns(): ValidationResult
    }

    %% Flow Relationships
    ScreenAnalyzer --> UIFlowAnalyzer: Screen Flow
    FormAnalyzer --> UIFlowAnalyzer: Form Flow
    UIFlowAnalyzer --> DataMappingAnalyzer: UI Data Flow

    BatchStructureAnalyzer --> StepAnalyzer: Batch Flow
    StepAnalyzer --> CheckpointRestartAnalyzer: Step Flow
    CheckpointRestartAnalyzer --> SortMergeAnalyzer: Process Flow

    InterfaceAnalyzer --> DataExchangeAnalyzer: Interface Flow
    DataExchangeAnalyzer --> RegisterUsageAnalyzer: Exchange Flow

    DBStatementParser --> SQLAnalyzer: SQL Statements
    SQLAnalyzer --> TransactionAnalyzer: SQL Analysis
    TransactionAnalyzer --> AccessPatternAnalyzer: Transaction Flow