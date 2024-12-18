classDiagram
    %% Core Security Components
    class SecurityAnalyzer {
        -scanner: VulnerabilityScanner
        -evaluator: SecurityEvaluator
        -patterns: SecurityPatternDetector
        +analyzeSecurity(ast: AST): SecurityReport
        +evaluateRisks(): RiskAssessment
    }

    class VulnerabilityScanner {
        -ruleEngine: SecurityRuleEngine
        -contextAnalyzer: SecurityContextAnalyzer
        +scanForVulnerabilities(ast: AST): List~Vulnerability~
        +analyzeDataFlow(): DataFlowAnalysis
    }

    class SecurityEvaluator {
        -cvssCalculator: CVSSCalculator
        -riskMatrix: RiskMatrix
        +evaluateVulnerabilities(vulns: List~Vulnerability~): RiskAssessment
        +calculateRiskScore(): float
    }

    %% Specialized Analyzers
    class AccessControlAnalyzer {
        +analyzeDataAccess(): AccessControlReport
        +checkAuthorization(): AuthorizationResult
        +validatePrivileges(): List~PrivilegeIssue~
        +assessAccessRisks(): RiskAssessment
    }

    class DataSecurityAnalyzer {
        +analyzeDataHandling(): DataSecurityReport
        +checkSensitiveData(): List~SensitiveDataFound~
        +validateDataProtection(): ProtectionAssessment
        +assessDataRisks(): RiskAssessment
    }

    class ErrorHandlingAnalyzer {
        +analyzeErrorHandling(): ErrorHandlingReport
        +checkExceptionHandling(): ExceptionAnalysis
        +validateErrorRecovery(): RecoveryAssessment
        +assessErrorRisks(): RiskAssessment
    }

    %% Security Models
    class SecurityReport {
        +vulnerabilities: List~Vulnerability~
        +riskAssessment: RiskAssessment
        +recommendations: List~SecurityRecommendation~
        +mitigations: List~Mitigation~
    }

    class Vulnerability {
        +type: VulnerabilityType
        +severity: Severity
        +location: CodeLocation
        +cvssScore: float
        +description: str
        +mitigation: str
    }

    class RiskAssessment {
        +riskLevel: RiskLevel
        +impactScore: float
        +likelihoodScore: float
        +cvssVector: str
        +calculateOverallRisk(): float
    }

    class SecurityRecommendation {
        +category: str
        +priority: Priority
        +impact: str
        +effort: str
        +description: str
    }

    class Mitigation {
        +vulnerability: Vulnerability
        +strategy: str
        +implementation: str
        +verification: str
        +status: MitigationStatus
    }

    %% Relationships
    SecurityAnalyzer --> VulnerabilityScanner
    SecurityAnalyzer --> SecurityEvaluator
    VulnerabilityScanner --> AccessControlAnalyzer
    VulnerabilityScanner --> DataSecurityAnalyzer
    VulnerabilityScanner --> ErrorHandlingAnalyzer
    SecurityReport *-- Vulnerability
    SecurityReport *-- RiskAssessment
    SecurityReport *-- SecurityRecommendation
    SecurityReport *-- Mitigation