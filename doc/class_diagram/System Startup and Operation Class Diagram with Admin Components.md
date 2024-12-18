classDiagram
    %% Core System Components
    class SystemInitializer {
        -configLoader: ConfigLoader
        -serviceManager: ServiceManager
        -statusMonitor: StatusMonitor
        +initialize(): InitializationResult
        +verifySystemStatus(): StatusReport
    }

    %% Authentication and Authorization
    class AuthenticationManager {
        -userRepository: UserRepository
        -sessionManager: SessionManager
        -roleManager: RoleManager
        +authenticate(credentials: Credentials): AuthResult
        +validateSession(sessionId: String): boolean
        +checkUserRole(userId: String): List~Role~
    }

    class RoleManager {
        -roles: Map~String, List~Permission~~
        +validateRole(userId: String, role: Role): boolean
        +getUserPermissions(userId: String): List~Permission~
        +updateUserRole(userId: String, role: Role): void
    }

    %% UI Management
    class DashboardController {
        -statusDisplay: StatusDisplay
        -menuManager: MenuManager
        -notificationService: NotificationService
        +initializeDashboard(userRole: Role): void
        +updateStatus(status: Status): void
    }

    %% Admin Components
    class AdminController {
        -userManager: UserManager
        -systemConfig: SystemConfig
        -masterManager: MasterManager
        -logMonitor: LogMonitor
        -backupManager: BackupManager
        +initializeAdminComponents(): void
        +handleAdminOperation(operation: AdminOperation): void
    }

    class UserManager {
        -userRepository: UserRepository
        -roleManager: RoleManager
        +createUser(userData: UserData): User
        +updateUser(userId: String, data: UserData): void
        +deleteUser(userId: String): void
        +listUsers(): List~User~
    }

    class SystemConfig {
        -configRepository: ConfigRepository
        -serviceManager: ServiceManager
        +updateConfig(config: Config): void
        +getSystemSettings(): SystemSettings
        +applySettings(settings: SystemSettings): void
    }

    class MasterManager {
        -masterRepository: MasterRepository
        +updateMasterData(type: MasterType, data: MasterData): void
        +getMasterData(type: MasterType): List~MasterData~
        +validateMasterData(data: MasterData): ValidationResult
    }

    class LogMonitor {
        -logRepository: LogRepository
        -alertService: AlertService
        +monitorLogs(): List~LogEntry~
        +searchLogs(criteria: SearchCriteria): List~LogEntry~
        +exportLogs(format: ExportFormat): File
    }

    class BackupManager {
        -backupService: BackupService
        -storageManager: StorageManager
        +createBackup(type: BackupType): BackupResult
        +restoreBackup(backupId: String): RestoreResult
        +listBackups(): List~Backup~
    }

    %% Menu Management
    class MenuManager {
        -roleManager: RoleManager
        -menuRepository: MenuRepository
        +getAvailableMenus(role: Role): List~Menu~
        +validateMenuAccess(userId: String, menuId: String): boolean
    }

    %% Relationships
    SystemInitializer --> AuthenticationManager
    AuthenticationManager --> RoleManager
    DashboardController --> MenuManager
    AdminController --> UserManager
    AdminController --> SystemConfig
    AdminController --> MasterManager
    AdminController --> LogMonitor
    AdminController --> BackupManager

    %% Role-based Dependencies
    RoleManager ..> MenuManager: controls access
    AuthenticationManager ..> DashboardController: initializes UI
    MenuManager ..> AdminController: admin menus
    UserManager ..> RoleManager: manages roles