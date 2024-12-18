classDiagram
    %% Core COBOL Analysis Components
    class ASTGenerator {
        +generateAST(source: Source): AST
        +validate(ast: AST): ValidationResult
        +optimize(ast: AST): AST
    }

    class COBOLParser {
        -lexicalAnalyzer: LexicalAnalyzer
        -syntaxRules: List~SyntaxRule~
        +parseProgram(): ParseTree
        +validateSyntax(): ValidationResult
        -handleDialect(token: Token): ParseResult
    }

    class COBOLASTGenerator {
        -parser: COBOLParser
        -nodeFactory: ASTNodeFactory
        +generateCOBOLAST(): COBOLAST
        +validateAST(): ValidationResult
        -processNode(node: ParseNode): ASTNode
    }

    %% Dialect Analysis
    class VendorDialectAnalyzer {
        -ast: COBOLAST
        -dialectRules: Map~Vendor, Rules~
        +analyzeDialect(): DialectAnalysis
        +identifyVendorSpecifics(): List~VendorSpecific~
        -validateDialectUsage(): ValidationResult
    }

    class CharacterSetAnalyzer {
        -ast: COBOLAST
        -charsetRules: CharsetRules
        +analyzeCharacterSet(): CharsetAnalysis
        +detectEncoding(): EncodingInfo
        -validateCharacters(): ValidationResult
    }

    class SpecialCommandAnalyzer {
        -ast: COBOLAST
        -commandPatterns: List~Pattern~
        +analyzeSpecialCommands(): CommandAnalysis
        +identifyCustomCommands(): List~Command~
        -validateCommands(): ValidationResult
    }

    %% COBOL Structure Analysis
    class DivisionAnalyzer {
        -ast: COBOLAST
        -divisionRules: DivisionRules
        +analyzeDivisions(): DivisionAnalysis
        +validateDivisionStructure(): ValidationResult
        -analyzeDivisionFlow(): FlowAnalysis
    }

    class SectionAnalyzer {
        -ast: COBOLAST
        -sectionRules: SectionRules
        +analyzeSections(): SectionAnalysis
        +validateSectionStructure(): ValidationResult
        -analyzeSectionDependencies(): DependencyAnalysis
    }

    class ProgramFlowAnalyzer {
        -ast: COBOLAST
        -flowRules: FlowRules
        +analyzeProgramFlow(): FlowAnalysis
        +buildFlowGraph(): FlowGraph
        -validateFlowLogic(): ValidationResult
    }

    %% Embedded Elements Analysis - Screen/Form
    class ScreenAnalyzer {
        -ast: COBOLAST
        -screenRules: ScreenRules
        +analyzeScreens(): ScreenAnalysis
        +validateScreenLayout(): ValidationResult
        -analyzeScreenFlow(): ScreenFlowAnalysis
    }

    class FormAnalyzer {
        -ast: COBOLAST
        -formRules: FormRules
        +analyzeForms(): FormAnalysis
        +validateFormStructure(): ValidationResult
        -analyzeFormFlow(): FormFlowAnalysis
    }

    %% Embedded Elements Analysis - Batch
    class BatchStructureAnalyzer {
        -ast: COBOLAST
        -batchRules: BatchRules
        +analyzeBatchStructure(): BatchAnalysis
        +validateBatchFlow(): ValidationResult
        -analyzeBatchDependencies(): DependencyAnalysis
    }

    %% Embedded Elements Analysis - Assembler
    class InterfaceAnalyzer {
        -ast: COBOLAST
        -interfaceRules: InterfaceRules
        +analyzeInterfaces(): InterfaceAnalysis
        +validateInterfaces(): ValidationResult
        -analyzeCallDependencies(): CallAnalysis
    }

    %% Embedded Elements Analysis - Database
    class DBStatementParser {
        -ast: COBOLAST
        -sqlPatterns: List~SQLPattern~
        +parseDBStatements(): DBStatementAnalysis
        +validateStatements(): ValidationResult
        -analyzeSQLStructure(): SQLAnalysis
    }

    %% Flow Relationships - Direct from Flowchart
    ASTGenerator --> COBOLParser: 1. generates
    COBOLParser --> COBOLASTGenerator: 2. provides parse tree
    COBOLASTGenerator --> VendorDialectAnalyzer: 3. AST for dialect
    COBOLASTGenerator --> DivisionAnalyzer: 4. AST for structure
    COBOLASTGenerator --> ScreenAnalyzer: 5. AST for screens
    COBOLASTGenerator --> FormAnalyzer: 6. AST for forms
    COBOLASTGenerator --> BatchStructureAnalyzer: 7. AST for batch
    COBOLASTGenerator --> InterfaceAnalyzer: 8. AST for interfaces
    COBOLASTGenerator --> DBStatementParser: 9. AST for DB

    %% Additional Relationships - Implicit from Requirements
    COBOLASTGenerator --> CharacterSetAnalyzer: AST for charset
    COBOLASTGenerator --> SpecialCommandAnalyzer: AST for commands
    COBOLASTGenerator --> SectionAnalyzer: AST for sections
    COBOLASTGenerator --> ProgramFlowAnalyzer: AST for flow