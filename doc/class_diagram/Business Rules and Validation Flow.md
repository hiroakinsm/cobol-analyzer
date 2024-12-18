classDiagram
    %% Core Validation Components
    class ValidationController {
        -ruleEngine: BusinessRuleEngine
        -validatorChain: ValidatorChain
        -contextManager: ValidationContextManager
        +validate(request: ValidationRequest): ValidationResult
        +enforceRules(context: BusinessContext): RuleResult
    }

    class BusinessRuleEngine {
        -ruleRepository: RuleRepository
        -ruleExecutor: RuleExecutor
        -ruleCache: RuleCache
        +executeRules(context: BusinessContext): RuleExecutionResult
        -resolveRuleDependencies(): DependencyGraph
    }

    class ValidatorChain {
        -validators: List~Validator~
        -validationStrategy: ValidationStrategy
        +addValidator(validator: Validator): void
        +executeValidation(): ValidationResult
    }

    %% Business Rules
    class COBOLAnalysisRules {
        -syntaxRules: List~SyntaxRule~
        -semanticRules: List~SemanticRule~
        -styleRules: List~StyleRule~
        +validateCOBOLStructure(): StructureValidation
        -checkProgramCompliance(): ComplianceResult
    }

    class MetricsValidationRules {
        -complexityRules: List~ComplexityRule~
        -qualityRules: List~QualityRule~
        -performanceRules: List~PerformanceRule~
        +validateMetrics(): MetricsValidation
        -checkThresholds(): ThresholdResult
    }

    class SecurityValidationRules {
        -accessRules: List~AccessRule~
        -dataRules: List~DataRule~
        -auditRules: List~AuditRule~
        +validateSecurity(): SecurityValidation
        -checkCompliance(): ComplianceResult
    }

    %% Validation Context
    class ValidationContext {
        -sourceContext: SourceContext
        -analysisContext: AnalysisContext
        -userContext: UserContext
        +getContextData(): ContextData
        -validateContext(): boolean
    }

    class SourceContext {
        -sourceId: UUID
        -sourceType: SourceType
        -metadata: SourceMetadata
        +getSourceInfo(): SourceInfo
        -validateSource(): boolean
    }

    class AnalysisContext {
        -analysisType: AnalysisType
        -parameters: AnalysisParameters
        -configuration: AnalysisConfig
        +getAnalysisInfo(): AnalysisInfo
        -validateAnalysis(): boolean
    }

    %% Specific Validators
    class SyntaxValidator {
        -syntaxRules: List~SyntaxRule~
        -parserConfig: ParserConfig
        +validateSyntax(source: Source): SyntaxResult
        -checkGrammar(): GrammarResult
    }

    class SemanticValidator {
        -semanticRules: List~SemanticRule~
        -contextResolver: ContextResolver
        +validateSemantics(ast: AST): SemanticResult
        -checkDataFlow(): DataFlowResult
    }

    class StyleValidator {
        -styleRules: List~StyleRule~
        -formatChecker: FormatChecker
        +validateStyle(source: Source): StyleResult
        -checkFormatting(): FormatResult
    }

    %% Rule Management
    class RuleRepository {
        -ruleStore: RuleStore
        -ruleLoader: RuleLoader
        -ruleIndexer: RuleIndexer
        +loadRules(context: RuleContext): List~Rule~
        -indexRules(): void
    }

    class RuleExecutor {
        -executionStrategy: ExecutionStrategy
        -resultCollector: ResultCollector
        +executeRule(rule: Rule): RuleResult
        -handleRuleFailure(): FailureHandler
    }

    %% Relationships
    ValidationController *-- BusinessRuleEngine
    ValidationController *-- ValidatorChain
    BusinessRuleEngine *-- RuleRepository
    BusinessRuleEngine *-- RuleExecutor

    ValidatorChain *-- SyntaxValidator
    ValidatorChain *-- SemanticValidator
    ValidatorChain *-- StyleValidator

    ValidationController *-- ValidationContext
    ValidationContext *-- SourceContext
    ValidationContext *-- AnalysisContext

    COBOLAnalysisRules --|> BusinessRuleEngine
    MetricsValidationRules --|> BusinessRuleEngine
    SecurityValidationRules --|> BusinessRuleEngine