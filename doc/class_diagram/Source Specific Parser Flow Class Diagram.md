classDiagram
    %% Base Parser Components
    class BaseParser {
        <<abstract>>
        #lexicalAnalyzer: LexicalAnalyzer
        #syntaxValidator: SyntaxValidator
        +parse(source: string): ParseTree
        +validate(tree: ParseTree): ValidationResult
    }

    class BaseASTGenerator {
        <<abstract>>
        #nodeFactory: ASTNodeFactory
        #validator: ASTValidator
        +generateAST(parseTree: ParseTree): AST
        +validate(ast: AST): ValidationResult
    }

    class BaseStructureAnalyzer {
        <<abstract>>
        #ast: AST
        #metrics: MetricsCollector
        +analyzeStructure(): StructureAnalysis
        +validateStructure(): ValidationResult
    }

    %% Assembler Analysis Flow
    class AssemblerParser {
        -instructionParser: InstructionParser
        -macroParser: MacroParser
        +parseAssembler(source: string): AssemblerParseTree
        -parseInstructions(): List~Instruction~
        -parseMacros(): List~Macro~
    }

    class AssemblerASTGenerator {
        -assemblerNodeFactory: AssemblerNodeFactory
        -macroResolver: MacroResolver
        +generateAssemblerAST(tree: AssemblerParseTree): AssemblerAST
        -resolveInstructions(): List~InstructionNode~
        -resolveMacros(): List~MacroNode~
    }

    class AssemblerStructureAnalyzer {
        -instructionAnalyzer: InstructionAnalyzer
        -macroAnalyzer: MacroAnalyzer
        +analyzeInstructions(): InstructionAnalysis
        +analyzeMacroUsage(): MacroAnalysis
        -analyzeControlFlow(): ControlFlowGraph
    }

    %% JCL Analysis Flow
    class JCLParser {
        -stepParser: StepParser
        -ddParser: DDParser
        +parseJCL(source: string): JCLParseTree
        -parseSteps(): List~Step~
        -parseDDStatements(): List~DDStatement~
    }

    class JCLASTGenerator {
        -jclNodeFactory: JCLNodeFactory
        -stepResolver: StepResolver
        +generateJCLAST(tree: JCLParseTree): JCLAST
        -resolveSteps(): List~StepNode~
        -resolveDDStatements(): List~DDNode~
    }

    class JCLStructureAnalyzer {
        -stepAnalyzer: StepAnalyzer
        -resourceAnalyzer: ResourceAnalyzer
        +analyzeSteps(): StepAnalysis
        +analyzeResources(): ResourceAnalysis
        -analyzeJobFlow(): JobFlowGraph
    }

    %% Flow Relationships
    BaseParser <|-- AssemblerParser
    BaseParser <|-- JCLParser
    BaseASTGenerator <|-- AssemblerASTGenerator
    BaseASTGenerator <|-- JCLASTGenerator
    BaseStructureAnalyzer <|-- AssemblerStructureAnalyzer
    BaseStructureAnalyzer <|-- JCLStructureAnalyzer

    %% Direct Flow Paths
    AssemblerParser --> AssemblerASTGenerator: ParseTree
    AssemblerASTGenerator --> AssemblerStructureAnalyzer: AST
    
    JCLParser --> JCLASTGenerator: ParseTree
    JCLASTGenerator --> JCLStructureAnalyzer: AST

    %% Common Result Types
    class ParseTree {
        <<abstract>>
        +root: Node
        +validate(): ValidationResult
    }

    class AST {
        <<abstract>>
        +root: ASTNode
        +validate(): ValidationResult
    }

    class StructureAnalysis {
        <<abstract>>
        +metrics: AnalysisMetrics
        +issues: List~Issue~
        +generateReport(): Report
    }

    %% Result Relationships
    AssemblerParser ..> ParseTree
    JCLParser ..> ParseTree
    AssemblerASTGenerator ..> AST
    JCLASTGenerator ..> AST
    AssemblerStructureAnalyzer ..> StructureAnalysis
    JCLStructureAnalyzer ..> StructureAnalysis