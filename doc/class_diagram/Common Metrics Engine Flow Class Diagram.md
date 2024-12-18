classDiagram
    %% Core Components
    class ASTGenerator {
        +generateAST(source: Source): AST
        +validate(ast: AST): ValidationResult
        +optimize(ast: AST): AST
    }

    class MetricsCollector {
        -ast: AST
        -metricRules: List~MetricRule~
        +collect(ast: AST): MetricsData
        +calculateBaseMetrics(): BaseMetrics
        -processMetric(node: ASTNode, rule: MetricRule): Metric
    }

    class MetricsEvaluator {
        -metrics: MetricsData
        -thresholds: Map~string, Threshold~
        +evaluate(metrics: MetricsData): EvaluationResult
        +compareToThresholds(): ComparisonResult
        -calculateScores(): MetricScores
    }

    class MetricsNormalizer {
        -metrics: MetricsData
        -ranges: Map~string, Range~
        +normalize(metrics: MetricsData): NormalizedMetrics
        +scaleMetrics(): ScaledMetrics
        -adjustOutliers(): AdjustedMetrics
    }

    class BenchmarkEvaluator {
        -normalizedMetrics: NormalizedMetrics
        -benchmarks: Map~string, Benchmark~
        +evaluateAgainstBenchmarks(): BenchmarkResult
        +calculateCompliance(): ComplianceResult
        -generateRecommendations(): List~Recommendation~
    }

    %% Data Models
    class MetricsData {
        +baseMetrics: BaseMetrics
        +derivedMetrics: DerivedMetrics
        +metadata: MetricsMetadata
        +validate(): ValidationResult
    }

    class EvaluationResult {
        +scores: Map~string, Score~
        +comparisons: List~Comparison~
        +issues: List~Issue~
        +generateReport(): EvaluationReport
    }

    class NormalizedMetrics {
        +metrics: Map~string, float~
        +ranges: Map~string, Range~
        +metadata: NormalizationMetadata
        +validate(): ValidationResult
    }

    class BenchmarkResult {
        +complianceScores: Map~string, Score~
        +deviations: List~Deviation~
        +recommendations: List~Recommendation~
        +generateReport(): BenchmarkReport
    }

    %% Direct Flow Relationships
    ASTGenerator --> MetricsCollector: AST
    MetricsCollector --> MetricsEvaluator: MetricsData
    MetricsEvaluator --> MetricsNormalizer: EvaluationResult
    MetricsNormalizer --> BenchmarkEvaluator: NormalizedMetrics

    %% Data Flow Relationships
    MetricsCollector ..> MetricsData
    MetricsEvaluator ..> EvaluationResult
    MetricsNormalizer ..> NormalizedMetrics
    BenchmarkEvaluator ..> BenchmarkResult

    %% Validation and Support
    class MetricsValidator {
        +validateMetrics(metrics: MetricsData): ValidationResult
        +validateEvaluation(result: EvaluationResult): ValidationResult
        +validateNormalization(metrics: NormalizedMetrics): ValidationResult
    }

    class MetricsProcessor {
        +processMetrics(ast: AST): ProcessedMetrics
        +aggregateMetrics(metrics: List~Metrics~): AggregatedMetrics
        -validateProcessing(): ValidationResult
    }

    MetricsValidator -- MetricsCollector
    MetricsValidator -- MetricsEvaluator
    MetricsValidator -- MetricsNormalizer
    MetricsProcessor -- MetricsCollector