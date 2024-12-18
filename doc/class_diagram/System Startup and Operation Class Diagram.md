classDiagram
    %% System Initialization
    class SystemInitializer {
        -configLoader: ConfigLoader
        -serviceManager: ServiceManager
        -statusMonitor: StatusMonitor
        +initialize(): InitializationResult
        +verifySystemStatus(): StatusReport
    }

    class ServiceManager {
        -services: Map~ServiceType, ServiceStatus~
        +startServices(): void
        +checkServiceStatus(): ServiceStatus
        +stopServices(): void
    }

    class StatusMonitor {
        -dbConnector: DatabaseConnector
        -serviceChecker: ServiceChecker
        +monitorSystemStatus(): SystemStatus
        +reportIssues(): List~Issue~
    }

    %% Authentication
    class AuthenticationManager {
        -userRepository: UserRepository
        -sessionManager: SessionManager
        -securityConfig: SecurityConfig
        +authenticate(credentials: Credentials): AuthResult
        +validateSession(sessionId: String): boolean
    }

    class SessionManager {
        -sessions: Map~String, SessionInfo~
        -timeoutConfig: TimeoutConfig
        +createSession(userId: String): Session
        +validateSession(sessionId: String): boolean
        +invalidateSession(sessionId: String): void
    }

    %% UI Management
    class DashboardController {
        -statusDisplay: StatusDisplay
        -menuManager: MenuManager
        -notificationService: NotificationService
        +initializeDashboard(): void
        +updateStatus(status: Status): void
    }

    class AnalysisMenuController {
        -sourceSelector: SourceSelector
        -taskSelector: TaskSelector
        -progressTracker: ProgressTracker
        +showAnalysisOptions(): void
        +handleSelection(selection: Selection): void
    }

    %% Progress Tracking
    class ProgressTracker {
        -currentTasks: Map~UUID, TaskProgress~
        -notificationService: NotificationService
        +updateProgress(taskId: UUID, progress: Progress): void
        +notifyCompletion(taskId: UUID): void
        -sendNotifications(notification: Notification): void
    }

    class NotificationService {
        -emailService: EmailService
        -uiNotifier: UINotifier
        +sendNotification(type: NotificationType, message: String): void
        +updateUI(status: Status): void
    }

    %% Status Management
    class StatusDisplay {
        -systemStatus: SystemStatus
        -taskStatus: TaskStatus
        -sourceStatus: SourceStatus
        +updateDisplay(status: Status): void
        +showError(error: Error): void
    }

    %% Relationships
    SystemInitializer --> ServiceManager
    SystemInitializer --> StatusMonitor
    AuthenticationManager --> SessionManager
    DashboardController --> StatusDisplay
    DashboardController --> AnalysisMenuController
    AnalysisMenuController --> ProgressTracker
    ProgressTracker --> NotificationService
    StatusDisplay --> NotificationService

    %% Dependencies
    AuthenticationManager ..> DashboardController: initializes
    SessionManager ..> StatusDisplay: updates
    ProgressTracker ..> StatusDisplay: updates