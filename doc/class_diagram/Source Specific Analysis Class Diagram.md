classDiagram
    class SourceAnalyzer {
        <<abstract>>
        #ast_accessor: ASTAccessor
        #metrics_collector: MetricsCollector
        +analyze(source: str): AnalysisResult
        #validate(): ValidationResult
        #collectMetrics(): MetricsResult
    }

    class COBOLAnalyzer {
        -division_analyzer: DivisionAnalyzer
        -section_analyzer: SectionAnalyzer
        -dialect_analyzer: DialectAnalyzer
        +analyzeDivisions(): DivisionAnalysis
        +analyzeDataStructures(): DataAnalysis
        +analyzeDialect(): DialectAnalysis
    }

    class JCLAnalyzer {
        -step_analyzer: StepAnalyzer
        -procedure_analyzer: ProcedureAnalyzer
        -condition_analyzer: ConditionAnalyzer
        +analyzeSteps(): StepAnalysis
        +analyzeProcedures(): ProcedureAnalysis
        +analyzeConditions(): ConditionAnalysis
    }

    class AssemblerAnalyzer {
        -instruction_analyzer: InstructionAnalyzer
        -macro_analyzer: MacroAnalyzer
        -register_analyzer: RegisterAnalyzer
        +analyzeInstructions(): InstructionAnalysis
        +analyzeMacros(): MacroAnalysis
        +analyzeRegisters(): RegisterAnalysis
    }

    class BatchProcessAnalyzer {
        -jcl_analyzer: JCLAnalyzer
        -step_chain_analyzer: StepChainAnalyzer
        -resource_analyzer: ResourceAnalyzer
        +analyzeBatchFlow(): BatchFlowAnalysis
        +analyzeResources(): ResourceAnalysis
        +analyzeJobnet(): JobnetAnalysis
    }

    class IntegrationAnalyzer {
        -cobol_analyzer: COBOLAnalyzer
        -jcl_analyzer: JCLAnalyzer
        -assembler_analyzer: AssemblerAnalyzer
        +analyzeInteractions(): InteractionAnalysis
        +analyzeDataFlow(): DataFlowAnalysis
        +validateIntegrity(): ValidationResult
    }

    SourceAnalyzer <|-- COBOLAnalyzer
    SourceAnalyzer <|-- JCLAnalyzer
    SourceAnalyzer <|-- AssemblerAnalyzer
    IntegrationAnalyzer -- COBOLAnalyzer
    IntegrationAnalyzer -- JCLAnalyzer
    IntegrationAnalyzer -- AssemblerAnalyzer
    BatchProcessAnalyzer -- JCLAnalyzer