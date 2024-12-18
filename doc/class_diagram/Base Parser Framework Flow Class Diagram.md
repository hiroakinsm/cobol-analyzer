classDiagram
    %% Base Components
    class LexicalAnalyzer {
        -tokenRules: Map~string, TokenRule~
        -position: int
        -currentLine: int
        -currentColumn: int
        +tokenize(source: string): TokenStream
        -processToken(): Token
        -handleSpecialToken(token: Token): Token
    }

    class Parser {
        -tokenStream: TokenStream
        -grammarRules: List~GrammarRule~
        +parse(tokens: TokenStream): ParseTree
        -parseNode(): ParseNode
        -matchToken(type: TokenType): Token
    }

    class ASTGenerator {
        -nodeFactory: ASTNodeFactory
        -parseTree: ParseTree
        +generateAST(parseTree: ParseTree): AST
        -createNode(parseNode: ParseNode): ASTNode
        -linkNodes(parent: ASTNode, child: ASTNode): void
    }

    class SyntaxValidator {
        -rules: List~ValidationRule~
        -ast: AST
        +validate(ast: AST): ValidationResult
        -checkSyntaxRules(): List~ValidationError~
        -validateStructure(): List~ValidationError~
    }

    %% Parser Framework Manager
    class ParserFramework {
        -lexicalAnalyzer: LexicalAnalyzer
        -parser: Parser
        -astGenerator: ASTGenerator
        -syntaxValidator: SyntaxValidator
        +process(source: string): ProcessingResult
        -validateResult(ast: AST): ValidationResult
    }

    %% Result Types
    class TokenStream {
        -tokens: List~Token~
        -position: int
        +next(): Token
        +peek(): Token
        +hasMore(): boolean
    }

    class ParseTree {
        -root: ParseNode
        -currentNode: ParseNode
        +addNode(node: ParseNode): void
        +traverse(visitor: ParseTreeVisitor): void
    }

    class AST {
        -root: ASTNode
        -metadata: Dict
        +traverse(visitor: ASTVisitor): void
        +validate(): ValidationResult
    }

    class ProcessingResult {
        +ast: AST
        +validationResult: ValidationResult
        +metadata: Dict
        +isValid(): boolean
    }

    %% Flow Relationships
    ParserFramework --> LexicalAnalyzer: 1. First
    ParserFramework --> Parser: 2. Second
    ParserFramework --> ASTGenerator: 3. Third
    ParserFramework --> SyntaxValidator: 4. Fourth

    LexicalAnalyzer ..> TokenStream: produces
    Parser ..> ParseTree: produces
    ASTGenerator ..> AST: produces
    SyntaxValidator ..> ValidationResult: produces
    ParserFramework ..> ProcessingResult: returns

    %% Data Flow
    LexicalAnalyzer --> Parser: TokenStream
    Parser --> ASTGenerator: ParseTree
    ASTGenerator --> SyntaxValidator: AST