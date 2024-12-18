classDiagram
    %% Error Management Core
    class ErrorController {
        -errorProcessors: Map~ErrorType, ErrorProcessor~
        -recoveryManager: RecoveryManager
        -notificationService: NotificationService
        +handleError(error: ApplicationError): ErrorResult
        +initiateRecovery(error: ApplicationError): RecoveryResult
    }

    class ErrorProcessor {
        -errorClassifier: ErrorClassifier
        -contextCollector: ErrorContextCollector
        -severityAnalyzer: SeverityAnalyzer
        +processError(error: ApplicationError): ProcessedError
        -enrichErrorContext(): ErrorContext
    }

    %% Error Classification
    class ErrorClassifier {
        -errorPatterns: Map~String, ErrorPattern~
        -classificationRules: List~ClassificationRule~
        +classifyError(error: ApplicationError): ErrorType
        -matchErrorPattern(error: ApplicationError): ErrorPattern
    }

    %% Error Types and Handling
    class ApplicationError {
        -errorType: ErrorType
        -message: String
        -stackTrace: String
        -timestamp: DateTime
        -context: ErrorContext
        +getErrorDetails(): ErrorDetails
    }

    class SystemError {
        <<extends ApplicationError>>
        -systemComponent: String
        -resourceState: ResourceState
        +getSystemContext(): SystemContext
    }

    class BusinessError {
        <<extends ApplicationError>>
        -businessRule: String
        -validationContext: ValidationContext
        +getBusinessContext(): BusinessContext
    }

    class SecurityError {
        <<extends ApplicationError>>
        -securityDomain: String
        -threatLevel: ThreatLevel
        +getSecurityContext(): SecurityContext
    }

    %% Recovery Management
    class RecoveryManager {
        -recoveryStrategies: Map~ErrorType, RecoveryStrategy~
        -stateManager: StateManager
        +executeRecovery(error: ProcessedError): RecoveryResult
        -validateRecoveryState(): StateValidation
    }

    class RecoveryStrategy {
        -steps: List~RecoveryStep~
        -fallbackStrategy: FallbackStrategy
        +attemptRecovery(): RecoveryAttempt
        -handleFailedRecovery(): FallbackResult
    }

    %% Error Logging and Monitoring
    class ErrorLogger {
        -logStorage: LogStorage
        -logFormatter: LogFormatter
        -retentionPolicy: RetentionPolicy
        +logError(error: ProcessedError): void
        +queryErrorLogs(criteria: SearchCriteria): List~ErrorLog~
    }

    class ErrorMonitor {
        -errorStats: ErrorStatistics
        -alertManager: AlertManager
        -thresholdMonitor: ThresholdMonitor
        +monitorErrors(): MonitoringResult
        +generateErrorReport(): ErrorReport
    }

    %% Relationships
    ErrorController *-- ErrorProcessor
    ErrorController *-- RecoveryManager
    ErrorProcessor *-- ErrorClassifier
    
    ApplicationError <|-- SystemError
    ApplicationError <|-- BusinessError
    ApplicationError <|-- SecurityError
    
    RecoveryManager *-- RecoveryStrategy
    ErrorController --> ErrorLogger
    ErrorController --> ErrorMonitor

    %% Dependencies
    ErrorProcessor ..> ApplicationError
    RecoveryStrategy ..> ProcessedError
    ErrorMonitor ..> ErrorLogger