classDiagram
    %% Base AST Generation Framework
    class ASTGenerator {
        <<abstract>>
        #lexer: LexicalAnalyzer
        #parser: Parser
        #validator: SyntaxValidator
        +generateAST(source: string): AST
        +validate(ast: AST): ValidationResult
        #optimize(ast: AST): AST
    }

    class AST {
        +type: SourceType
        +nodes: List~ASTNode~
        +metadata: Dict
        +validate(): ValidationResult
        +traverse(visitor: ASTVisitor): void
    }

    %% COBOL Specific
    class COBOLASTGenerator {
        -division_parser: DivisionParser
        -data_parser: DataParser
        -procedure_parser: ProcedureParser
        +parseDivisions(): List~DivisionNode~
        +parseDataItems(): List~DataNode~
        +parseProcedures(): List~ProcedureNode~
    }

    class COBOLAST {
        +divisions: List~DivisionNode~
        +dataItems: List~DataNode~
        +procedures: List~ProcedureNode~
        +validateStructure(): ValidationResult
    }

    %% JCL Specific
    class JCLASTGenerator {
        -step_parser: StepParser
        -exec_parser: ExecParser
        -dd_parser: DDParser
        +parseSteps(): List~StepNode~
        +parseExecStatements(): List~ExecNode~
        +parseDDStatements(): List~DDNode~
    }

    class JCLAST {
        +steps: List~StepNode~
        +execStatements: List~ExecNode~
        +ddStatements: List~DDNode~
        +validateJobStructure(): ValidationResult
    }

    %% Assembler Specific
    class AssemblerASTGenerator {
        -instruction_parser: InstructionParser
        -macro_parser: MacroParser
        -data_parser: DataParser
        +parseInstructions(): List~InstructionNode~
        +parseMacros(): List~MacroNode~
        +parseDataDefinitions(): List~DataNode~
    }

    class AssemblerAST {
        +instructions: List~InstructionNode~
        +macros: List~MacroNode~
        +dataDefinitions: List~DataNode~
        +validateAssembly(): ValidationResult
    }

    %% Screen/Form Specific
    class ScreenASTGenerator {
        -layout_parser: LayoutParser
        -field_parser: FieldParser
        -action_parser: ActionParser
        +parseLayout(): LayoutNode
        +parseFields(): List~FieldNode~
        +parseActions(): List~ActionNode~
    }

    class ScreenAST {
        +layout: LayoutNode
        +fields: List~FieldNode~
        +actions: List~ActionNode~
        +validateScreenStructure(): ValidationResult
    }

    %% Batch Processing Specific
    class BatchASTGenerator {
        -flow_parser: FlowParser
        -checkpoint_parser: CheckpointParser
        -resource_parser: ResourceParser
        +parseFlow(): FlowNode
        +parseCheckpoints(): List~CheckpointNode~
        +parseResources(): List~ResourceNode~
    }

    class BatchAST {
        +flow: FlowNode
        +checkpoints: List~CheckpointNode~
        +resources: List~ResourceNode~
        +validateBatchStructure(): ValidationResult
    }

    %% Persistence and Management
    class ASTManager {
        -astGenerators: Map~SourceType, ASTGenerator~
        -storage: ASTStorage
        +generateAST(source: Source): AST
        +storeAST(ast: AST): void
        +loadAST(id: UUID): AST
    }

    class ASTStorage {
        -mongoClient: MongoClient
        -collection: Collection
        +store(ast: AST): UUID
        +load(id: UUID): AST
        +update(id: UUID, ast: AST): void
    }

    %% Relationships
    ASTGenerator <|-- COBOLASTGenerator
    ASTGenerator <|-- JCLASTGenerator
    ASTGenerator <|-- AssemblerASTGenerator
    ASTGenerator <|-- ScreenASTGenerator
    ASTGenerator <|-- BatchASTGenerator
    AST <|-- COBOLAST
    AST <|-- JCLAST
    AST <|-- AssemblerAST
    AST <|-- ScreenAST
    AST <|-- BatchAST
    ASTManager --> ASTGenerator
    ASTManager --> ASTStorage