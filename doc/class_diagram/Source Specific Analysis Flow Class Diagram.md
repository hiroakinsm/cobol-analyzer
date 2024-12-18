classDiagram
    %% Assembler Analysis Flow
    class AssemblerParser {
        -lexicalAnalyzer: LexicalAnalyzer
        -syntaxRules: AssemblerSyntaxRules
        +parseAssembler(source: string): AssemblerParseTree
        -parseInstructions(): List~Instruction~
        -parseMacros(): List~Macro~
    }

    class AssemblerASTGenerator {
        -parser: AssemblerParser
        -nodeFactory: AssemblerNodeFactory
        +generateAssemblerAST(parseTree: AssemblerParseTree): AssemblerAST
        -resolveInstructions(): List~InstructionNode~
        -resolveMacros(): List~MacroNode~
    }

    class AssemblerStructureAnalyzer {
        -ast: AssemblerAST
        -metrics: MetricsCollector
        +analyzeStructure(): StructureAnalysis
        -analyzeControlFlow(): ControlFlowGraph
        -analyzeDependencies(): DependencyAnalysis
    }

    %% JCL Analysis Flow
    class JCLParser {
        -lexicalAnalyzer: LexicalAnalyzer
        -syntaxRules: JCLSyntaxRules
        +parseJCL(source: string): JCLParseTree
        -parseSteps(): List~Step~
        -parseDDStatements(): List~DDStatement~
    }

    class JCLASTGenerator {
        -parser: JCLParser
        -nodeFactory: JCLNodeFactory
        +generateJCLAST(parseTree: JCLParseTree): JCLAST
        -resolveSteps(): List~StepNode~
        -resolveProcedures(): List~ProcedureNode~
    }

    class JCLStructureAnalyzer {
        -ast: JCLAST
        -metrics: MetricsCollector
        +analyzeStructure(): StructureAnalysis
        -analyzeJobFlow(): JobFlowAnalysis
        -analyzeResourceUsage(): ResourceAnalysis
    }

    %% AST Models
    class AssemblerAST {
        +instructions: List~InstructionNode~
        +macros: List~MacroNode~
        +registers: List~RegisterNode~
        +validateStructure(): ValidationResult
    }

    class JCLAST {
        +steps: List~StepNode~
        +procedures: List~ProcedureNode~
        +ddStatements: List~DDStatementNode~
        +validateStructure(): ValidationResult
    }

    %% Analysis Results
    class StructureAnalysis {
        +metrics: AnalysisMetrics
        +issues: List~Issue~
        +dependencies: List~Dependency~
        +generateReport(): Report
    }

    %% Flow Relationships - Exact match with flowchart
    AssemblerParser --> AssemblerASTGenerator: "Parse Tree"
    AssemblerASTGenerator --> AssemblerStructureAnalyzer: "AST"
    JCLParser --> JCLASTGenerator: "Parse Tree"
    JCLASTGenerator --> JCLStructureAnalyzer: "AST"

    %% Result Relationships
    AssemblerASTGenerator ..> AssemblerAST: generates
    JCLASTGenerator ..> JCLAST: generates
    AssemblerStructureAnalyzer ..> StructureAnalysis: produces
    JCLStructureAnalyzer ..> StructureAnalysis: produces