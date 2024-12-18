classDiagram
    %% Base Analysis Framework
    class ASTAnalyzer {
        <<abstract>>
        #metrics: MetricsCollector
        #validator: Validator
        +analyze(ast: AST): AnalysisResult
        #validateStructure(): ValidationResult
        #collectMetrics(): MetricsResult
    }

    %% COBOL Analysis
    class COBOLASTAnalyzer {
        -division_analyzer: DivisionAnalyzer
        -data_analyzer: DataAnalyzer
        -procedure_analyzer: ProcedureAnalyzer
        +analyzeDivisions(): DivisionAnalysis
        +analyzeDataItems(): DataAnalysis
        +analyzeProcedures(): ProcedureAnalysis
    }

    %% JCL Analysis
    class JCLASTAnalyzer {
        -step_analyzer: StepAnalyzer
        -exec_analyzer: ExecAnalyzer
        -resource_analyzer: ResourceAnalyzer
        +analyzeSteps(): StepAnalysis
        +analyzeExecStatements(): ExecAnalysis
        +analyzeResources(): ResourceAnalysis
    }

    %% Assembler Analysis
    class AssemblerASTAnalyzer {
        -instruction_analyzer: InstructionAnalyzer
        -macro_analyzer: MacroAnalyzer
        -optimization_analyzer: OptimizationAnalyzer
        +analyzeInstructions(): InstructionAnalysis
        +analyzeMacros(): MacroAnalysis
        +analyzeOptimizations(): OptimizationAnalysis
    }

    %% Screen Analysis
    class ScreenASTAnalyzer {
        -layout_analyzer: LayoutAnalyzer
        -field_analyzer: FieldAnalyzer
        -flow_analyzer: FlowAnalyzer
        +analyzeLayout(): LayoutAnalysis
        +analyzeFields(): FieldAnalysis
        +analyzeFlow(): FlowAnalysis
    }

    %% Batch Analysis
    class BatchASTAnalyzer {
        -flow_analyzer: FlowAnalyzer
        -checkpoint_analyzer: CheckpointAnalyzer
        -performance_analyzer: PerformanceAnalyzer
        +analyzeFlow(): FlowAnalysis
        +analyzeCheckpoints(): CheckpointAnalysis
        +analyzePerformance(): PerformanceAnalysis
    }

    %% Cross-Reference Analysis
    class CrossReferenceAnalyzer {
        -ast_collection: List~AST~
        -dependency_analyzer: DependencyAnalyzer
        +analyzeDependencies(): DependencyAnalysis
        +buildDependencyGraph(): DependencyGraph
        +validateReferences(): ValidationResult
    }

    %% Integration Analysis
    class IntegratedASTAnalyzer {
        -cross_reference: CrossReferenceAnalyzer
        -flow_analyzer: IntegratedFlowAnalyzer
        -impact_analyzer: ImpactAnalyzer
        +analyzeIntegration(): IntegrationAnalysis
        +analyzeDataFlow(): DataFlowAnalysis
        +analyzeImpact(): ImpactAnalysis
    }

    %% Analysis Result Models
    class AnalysisResult {
        +sourceType: SourceType
        +metrics: MetricsResult
        +issues: List~Issue~
        +recommendations: List~Recommendation~
        +generateReport(): Report
    }

    class IntegratedAnalysisResult {
        +crossReferences: List~Reference~
        +dependencies: DependencyGraph
        +dataFlow: DataFlowGraph
        +impactAnalysis: ImpactAnalysis
        +generateSummary(): Summary
    }

    %% Relationships
    ASTAnalyzer <|-- COBOLASTAnalyzer
    ASTAnalyzer <|-- JCLASTAnalyzer
    ASTAnalyzer <|-- AssemblerASTAnalyzer
    ASTAnalyzer <|-- ScreenASTAnalyzer
    ASTAnalyzer <|-- BatchASTAnalyzer
    IntegratedASTAnalyzer --> CrossReferenceAnalyzer
    IntegratedASTAnalyzer ..> IntegratedAnalysisResult
    ASTAnalyzer ..> AnalysisResult