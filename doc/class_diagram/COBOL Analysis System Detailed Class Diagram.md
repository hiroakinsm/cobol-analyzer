classDiagram
    %% COBOL Structure Analysis
    class COBOLAnalyzer {
        -parser: COBOLParser
        -structureAnalyzer: StructureAnalyzer
        -dataAnalyzer: DataAnalyzer
        -flowAnalyzer: FlowAnalyzer
        +analyze(source: string): AnalysisResult
        +generateAST(): AST
        +validateProgram(): ValidationResult
    }

    class StructureAnalyzer {
        -divisions: Map~string, DivisionAnalyzer~
        -metrics: StructureMetrics
        +analyzeDivisions(): DivisionAnalysis
        +analyzeSections(): SectionAnalysis
        +analyzeParagraphs(): ParagraphAnalysis
        -calculateMetrics(): StructureMetrics
    }

    class DataAnalyzer {
        -workingStorage: WorkingStorageAnalyzer
        -linkage: LinkageAnalyzer
        -fileSection: FileSectionAnalyzer
        +analyzeDataDivision(): DataAnalysis
        +analyzeDataDependencies(): DependencyGraph
        +validateDataStructures(): ValidationResult
    }

    class FlowAnalyzer {
        -controlFlow: ControlFlowAnalyzer
        -dataFlow: DataFlowAnalyzer
        -callGraph: CallGraphAnalyzer
        +analyzeControlFlow(): ControlFlowGraph
        +analyzeDataFlow(): DataFlowGraph
        +analyzeCallHierarchy(): CallHierarchy
    }

    %% Specific Analyzers
    class DivisionAnalyzer {
        -type: DivisionType
        -content: string
        -validators: List~DivisionValidator~
        +analyze(): DivisionAnalysis
        -validateStructure(): boolean
        -analyzeComponents(): ComponentAnalysis
    }

    class WorkingStorageAnalyzer {
        -items: List~DataItem~
        -groups: List~DataGroup~
        -redefines: Map~string, RedefinesInfo~
        +analyzeItems(): DataItemAnalysis
        +analyzeGroups(): GroupAnalysis
        +validateRedefines(): ValidationResult
    }

    class ControlFlowAnalyzer {
        -statements: List~Statement~
        -branches: List~Branch~
        -loops: List~Loop~
        +buildControlFlowGraph(): ControlFlowGraph
        +analyzeComplexity(): ComplexityMetrics
        +detectPatterns(): List~Pattern~
    }

    %% Analysis Models
    class COBOLProgram {
        -identification: IdentificationDivision
        -environment: EnvironmentDivision
        -data: DataDivision
        -procedure: ProcedureDivision
        +validate(): ValidationResult
        +analyze(): ProgramAnalysis
        +getMetrics(): ProgramMetrics
    }

    class DataItem {
        -level: number
        -name: string
        -picture: string
        -usage: string
        -value: string
        +validate(): boolean
        +analyze(): ItemAnalysis
        +getDependencies(): List~Dependency~
    }

    class Statement {
        -type: StatementType
        -operands: List~Operand~
        -conditions: List~Condition~
        +analyze(): StatementAnalysis
        +validateSyntax(): boolean
        +getControlFlow(): ControlFlow
    }

    %% Embedded Elements
    class EmbeddedElementAnalyzer {
        -sqlAnalyzer: SQLAnalyzer
        -cicsAnalyzer: CICSAnalyzer
        -assemblerAnalyzer: AssemblerAnalyzer
        +analyzeSQL(): SQLAnalysis
        +analyzeCICS(): CICSAnalysis
        +analyzeAssembler(): AssemblerAnalysis
    }

    class SQLAnalyzer {
        -statements: List~SQLStatement~
        -tables: List~TableReference~
        +analyzeSQLStatements(): SQLAnalysis
        +validateSQL(): ValidationResult
        +buildDataAccess(): DataAccessMap
    }

    %% Relationships
    COBOLAnalyzer *-- StructureAnalyzer
    COBOLAnalyzer *-- DataAnalyzer
    COBOLAnalyzer *-- FlowAnalyzer
    COBOLAnalyzer *-- EmbeddedElementAnalyzer
    StructureAnalyzer *-- DivisionAnalyzer
    DataAnalyzer *-- WorkingStorageAnalyzer
    FlowAnalyzer *-- ControlFlowAnalyzer
    EmbeddedElementAnalyzer *-- SQLAnalyzer