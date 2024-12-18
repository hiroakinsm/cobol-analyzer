classDiagram
    %% Benchmark Engine Components
    class BenchmarkEvaluator {
        -benchmarks: Map~string, Benchmark~
        -standards: List~StandardReference~
        +evaluateAgainstBenchmarks(): BenchmarkResult
        +calculateCompliance(): ComplianceResult
        -validateAgainstStandards(): ValidationResult
    }

    class ComplianceChecker {
        -evaluator: BenchmarkEvaluator
        -rules: List~ComplianceRule~
        +checkCompliance(): ComplianceResult
        +validateRules(): ValidationResult
        -assessDeviation(): DeviationAnalysis
    }

    class BenchmarkReporter {
        -results: BenchmarkResult
        -compliance: ComplianceResult
        +generateReport(): Report
        +createVisualizations(): List~Chart~
        -formatResults(): FormattedResults
    }

    %% Standard References
    class CodingStandardReference {
        -standardDefinitions: List~Standard~
        -ruleSet: RuleSet
        +evaluateAgainstStandard(): StandardEvaluation
        +getViolations(): List~Violation~
    }

    class QualityStandardReference {
        -qualityMetrics: List~Metric~
        -thresholds: ThresholdSet
        +evaluateQuality(): QualityEvaluation
        +getQualityIssues(): List~Issue~
    }

    class PerformanceStandardReference {
        -performanceMetrics: List~Metric~
        -benchmarks: BenchmarkSet
        +evaluatePerformance(): PerformanceEvaluation
        +getPerformanceIssues(): List~Issue~
    }

    class SecurityStandardReference {
        -securityRules: List~SecurityRule~
        -vulnerabilityDefinitions: VulnerabilitySet
        +evaluateSecurity(): SecurityEvaluation
        +getSecurityIssues(): List~Issue~
    }

    class PortabilityStandardReference {
        -portabilityRules: List~PortabilityRule~
        -platformDefinitions: PlatformSet
        +evaluatePortability(): PortabilityEvaluation
        +getPortabilityIssues(): List~Issue~
    }

    %% Results and Reports
    class BenchmarkResult {
        +standardResults: Map~string, StandardResult~
        +compliance: ComplianceResult
        +issues: List~Issue~
        +generateReport(): BenchmarkReport
    }

    class ComplianceResult {
        +complianceLevel: ComplianceLevel
        +violations: List~Violation~
        +recommendations: List~Recommendation~
        +generateReport(): ComplianceReport
    }

    %% Flow Relationships - Direct from flowchart
    BenchmarkEvaluator --> ComplianceChecker
    BenchmarkEvaluator --> CodingStandardReference
    BenchmarkEvaluator --> QualityStandardReference
    BenchmarkEvaluator --> PerformanceStandardReference
    BenchmarkEvaluator --> SecurityStandardReference
    BenchmarkEvaluator --> PortabilityStandardReference

    %% Added ComplianceChecker to BenchmarkReporter relationship
    ComplianceChecker --> BenchmarkReporter: Provides compliance data

    %% Result Relationships
    BenchmarkEvaluator ..> BenchmarkResult
    ComplianceChecker ..> ComplianceResult
    CodingStandardReference ..> StandardResult
    QualityStandardReference ..> StandardResult
    PerformanceStandardReference ..> StandardResult
    SecurityStandardReference ..> StandardResult
    PortabilityStandardReference ..> StandardResult