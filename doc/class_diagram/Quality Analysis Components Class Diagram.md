classDiagram
    %% Core Quality Components
    class QualityAnalyzer {
        -metrics: QualityMetricsCollector
        -evaluator: QualityEvaluator
        +analyzeQuality(ast: AST): QualityReport
        +evaluateMetrics(): QualityScore
    }

    class QualityMetricsCollector {
        -complexityAnalyzer: ComplexityAnalyzer
        -maintainabilityAnalyzer: MaintainabilityAnalyzer
        -moduleAnalyzer: ModuleAnalyzer
        +collectMetrics(ast: AST): QualityMetrics
    }

    class QualityEvaluator {
        -benchmarks: QualityBenchmarks
        -thresholds: Dict~str, float~
        +evaluateMetrics(metrics: QualityMetrics): QualityEvaluation
        +compareToBenchmark(value: float, type: str): Score
    }

    %% Specific Analyzers
    class ComplexityAnalyzer {
        +calculateCyclomaticComplexity(): float
        +calculateCognitiveComplexity(): float
        +calculateHalsteadMetrics(): HalsteadMetrics
        +analyzeControlFlow(): ControlFlowMetrics
    }

    class MaintainabilityAnalyzer {
        +calculateMaintainabilityIndex(): float
        +analyzeCodeCohesion(): float
        +analyzeCodeCoupling(): float
        +evaluateDocumentation(): DocumentationScore
    }

    class ModuleAnalyzer {
        +analyzeModuleSize(): ModuleMetrics
        +analyzeModuleCohesion(): CohesionMetrics
        +analyzeModuleCoupling(): CouplingMetrics
        +evaluateModuleQuality(): ModuleQualityScore
    }

    %% Quality Models
    class QualityMetrics {
        +complexityMetrics: ComplexityMetrics
        +maintainabilityMetrics: MaintainabilityMetrics
        +moduleMetrics: ModuleMetrics
        +calculateOverallScore(): float
    }

    class QualityReport {
        +metrics: QualityMetrics
        +evaluation: QualityEvaluation
        +issues: List~QualityIssue~
        +recommendations: List~Recommendation~
    }

    class QualityIssue {
        +type: IssueType
        +severity: Severity
        +location: CodeLocation
        +impact: str
        +suggestion: str
    }

    class Recommendation {
        +category: str
        +priority: Priority
        +description: str
        +benefit: str
        +effort: str
    }

    %% Relationships
    QualityAnalyzer --> QualityMetricsCollector
    QualityAnalyzer --> QualityEvaluator
    QualityMetricsCollector --> ComplexityAnalyzer
    QualityMetricsCollector --> MaintainabilityAnalyzer
    QualityMetricsCollector --> ModuleAnalyzer
    QualityAnalyzer ..> QualityReport
    QualityReport *-- QualityMetrics
    QualityReport *-- QualityIssue
    QualityReport *-- Recommendation