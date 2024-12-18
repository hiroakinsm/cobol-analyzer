classDiagram
    %% Parser Framework
    class BaseParser {
        <<abstract>>
        #logger: Logger
        +parse(content: str): AST
        +validate(ast: AST): List~ValidationResult~
    }

    class LexicalAnalyzer {
        -tokenRules: Dict
        +tokenize(content: str): List~Token~
        +getNextToken(): Token
    }

    class SyntaxValidator {
        -rules: List~ValidationRule~
        +validate(ast: AST): List~ValidationResult~
        +addRule(rule: ValidationRule): void
    }

    class ASTGenerator {
        -nodeFactory: ASTNodeFactory
        +generateAST(tokens: List~Token~): AST
        +optimizeAST(ast: AST): AST
    }

    %% COBOL Specific Parser
    class COBOLParser {
        -lexicalAnalyzer: LexicalAnalyzer
        -syntaxValidator: SyntaxValidator
        -astGenerator: ASTGenerator
        +parseProgram(source: str): COBOLProgram
        +analyzeDivision(division: str): DivisionAST
    }

    class COBOLLexicalAnalyzer {
        -cobolTokenRules: Dict
        +tokenizeDivision(content: str): List~Token~
        +tokenizeStatement(content: str): List~Token~
    }

    class COBOLSyntaxValidator {
        -cobolRules: List~ValidationRule~
        +validateDivisionOrder(): ValidationResult
        +validateSectionStructure(): ValidationResult
    }

    class COBOLASTGenerator {
        -cobolNodeFactory: COBOLNodeFactory
        +generateProgramAST(): ProgramAST
        +generateDivisionAST(): DivisionAST
    }

    %% Relationships
    BaseParser <|-- COBOLParser
    LexicalAnalyzer <|-- COBOLLexicalAnalyzer
    SyntaxValidator <|-- COBOLSyntaxValidator
    ASTGenerator <|-- COBOLASTGenerator
    COBOLParser -- COBOLLexicalAnalyzer
    COBOLParser -- COBOLSyntaxValidator
    COBOLParser -- COBOLASTGenerator