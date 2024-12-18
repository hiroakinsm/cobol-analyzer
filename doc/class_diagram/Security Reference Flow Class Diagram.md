classDiagram
    %% Security Reference Components
    class CVEChecker {
        -cveDatabase: CVEDatabase
        -patternMatcher: PatternMatcher
        +checkForCVEs(): List~CVEMatch~
        +validateVulnerabilities(): ValidationResult
        -analyzeCVEPatterns(): PatternAnalysis
    }

    class CVSSEvaluator {
        -cveMatches: List~CVEMatch~
        -calculator: CVSSCalculator
        +calculateCVSSScore(): CVSSScore
        +evaluateRiskLevel(): RiskLevel
        -determineImpactMetrics(): ImpactMetrics
    }

    class SecurityImpactAnalyzer {
        -cvssEvaluation: CVSSScore
        -riskLevel: RiskLevel
        +analyzeSecurityImpact(): ImpactAnalysis
        +assessSystemVulnerability(): VulnerabilityAssessment
        -generateRecommendations(): List~SecurityRecommendation~
    }

    %% Data Models
    class CVEMatch {
        +cveId: string
        +description: string
        +affectedComponents: List~Component~
        +matchConfidence: float
        +validate(): ValidationResult
    }

    class CVSSScore {
        +baseScore: float
        +temporalScore: float
        +environmentalScore: float
        +vector: string
        +calculateOverallScore(): float
    }

    class SecurityImpactResult {
        +impactLevel: ImpactLevel
        +affectedAreas: List~AffectedArea~
        +recommendations: List~Recommendation~
        +generateReport(): ImpactReport
    }

    %% Flow Relationships - Exact match with flowchart
    CVEChecker --> CVSSEvaluator: CVE Findings
    CVSSEvaluator --> SecurityImpactAnalyzer: CVSS Assessment

    %% Data Flow
    CVEChecker ..> CVEMatch: produces
    CVSSEvaluator ..> CVSSScore: calculates
    SecurityImpactAnalyzer ..> SecurityImpactResult: generates

    %% Dependencies
    CVSSEvaluator -- CVEMatch: uses
    SecurityImpactAnalyzer -- CVSSScore: analyzes