flowchart TB
    subgraph "System Startup"
        INIT["System Initialization"]
        DB_CHECK["Database Connection Check"]
        SRV_CHECK["Service Status Check"]
        
        subgraph "Status Verification"
            APP_STAT["Application Server Status"]
            AI_STAT["AI/RAG/ML Server Status"]
            WEB_STAT["Web Server Status"]
        end
    end

    subgraph "User Authentication"
        LOGIN["Login Screen"]
        AUTH["Authentication"]
        SESSION["Session Management"]
        ROLE_CHECK["Role Verification"]
    end

    subgraph "Initial UI"
        DASH["Dashboard"]
        
        subgraph "System Status Display"
            SYS_STAT["System Status"]
            TASK_STAT["Task Status"]
            SRC_STAT["Source Status"]
        end
        
        subgraph "Operation Menu"
            MAIN_MENU["Main Menu"]
            ANA_MENU["Analysis Menu"]
            HIST_MENU["History Menu"]
            
            subgraph "Admin Menu"
                USER_MGM["User Management"]
                SYS_CONFIG["System Configuration"]
                MASTER_MGM["Master Data Management"]
                LOG_MON["Log Monitor"]
                BACKUP_MGM["Backup Management"]
            end
        end
    end

    subgraph "Analysis Flow"
        SRC_SEL["Source Selection"]
        TASK_SEL["Task Selection"]
        
        subgraph "Analysis Feedback"
            PROG_BAR["Progress Bar"]
            STAT_MSG["Status Messages"]
            ERR_MSG["Error Messages"]
        end
        
        subgraph "Completion Notification"
            COMP_NOTIF["Completion Notification"]
            RESULT_LINK["Results Link"]
            EMAIL_NOTIF["Email Notification"]
        end
    end

    %% Startup Flow
    INIT --> DB_CHECK
    DB_CHECK --> SRV_CHECK
    SRV_CHECK --> APP_STAT & AI_STAT & WEB_STAT

    %% Authentication Flow
    APP_STAT & AI_STAT & WEB_STAT --> LOGIN
    LOGIN --> AUTH
    AUTH --> SESSION
    SESSION --> ROLE_CHECK
    
    %% UI Initialization
    ROLE_CHECK --> DASH
    DASH --> SYS_STAT & TASK_STAT & SRC_STAT
    DASH --> MAIN_MENU
    MAIN_MENU --> ANA_MENU & HIST_MENU

    %% Admin Menu Flow - Only accessible with admin role
    ROLE_CHECK -- "Admin Role" --> ADMIN_MENU
    ADMIN_MENU --> USER_MGM & SYS_CONFIG & MASTER_MGM & LOG_MON & BACKUP_MGM

    %% Analysis Operation
    ANA_MENU --> SRC_SEL
    SRC_SEL --> TASK_SEL
    TASK_SEL --> PROG_BAR
    PROG_BAR --> |Progress Updates| STAT_MSG
    STAT_MSG --> |On Error| ERR_MSG
    STAT_MSG --> |On Completion| COMP_NOTIF
    COMP_NOTIF --> RESULT_LINK & EMAIL_NOTIF