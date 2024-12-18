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
    
    %% UI Initialization
    SESSION --> DASH
    DASH --> SYS_STAT & TASK_STAT & SRC_STAT
    DASH --> MAIN_MENU
    MAIN_MENU --> ANA_MENU & HIST_MENU

    %% Analysis Operation
    ANA_MENU --> SRC_SEL
    SRC_SEL --> TASK_SEL
    TASK_SEL --> PROG_BAR
    PROG_BAR --> |Progress Updates| STAT_MSG
    STAT_MSG --> |On Error| ERR_MSG
    STAT_MSG --> |On Completion| COMP_NOTIF
    COMP_NOTIF --> RESULT_LINK & EMAIL_NOTIF