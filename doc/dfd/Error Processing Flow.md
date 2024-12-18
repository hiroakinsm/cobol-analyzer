flowchart TB
    subgraph "Error Detection"
        ERR_OCCUR["Error Occurs"]
        ERR_CATCH["Error Caught"]
        CONTEXT_COL["Context Collection"]
        ERR_CLASS["Error Classification"]
    end

    subgraph "Error Processing"
        SEV_ANAL["Severity Analysis"]
        
        subgraph "Context Enrichment"
            SYS_CTX["System Context"]
            USER_CTX["User Context"]
            PROC_CTX["Process Context"]
            STATE_CTX["State Context"]
        end

        subgraph "Impact Analysis"
            DIRECT_IMP["Direct Impact"]
            CASCAD_IMP["Cascading Impact"]
            DATA_IMP["Data Impact"]
        end
    end

    subgraph "Recovery Processing"
        REC_EVAL["Recovery Evaluation"]
        
        subgraph "Recovery Strategies"
            AUTO_REC["Automatic Recovery"]
            MANUAL_REC["Manual Recovery"]
            FALLBACK["Fallback Processing"]
        end
        
        subgraph "State Management"
            STATE_CHECK["State Check"]
            STATE_SAVE["State Save"]
            STATE_RESTORE["State Restore"]
        end
    end

    subgraph "Notification & Logging"
        subgraph "Notification"
            USER_NOTIF["User Notification"]
            ADMIN_NOTIF["Admin Notification"]
            SYS_NOTIF["System Notification"]
        end
        
        subgraph "Logging"
            ERR_LOG["Error Logging"]
            AUDIT_LOG["Audit Logging"]
            DEBUG_LOG["Debug Logging"]
        end
    end

    subgraph "Monitoring & Analysis"
        ERR_TRACK["Error Tracking"]
        PATTERN_ANAL["Pattern Analysis"]
        TREND_ANAL["Trend Analysis"]
        ALERT_GEN["Alert Generation"]
    end

    %% Error Detection Flow
    ERR_OCCUR --> ERR_CATCH
    ERR_CATCH --> CONTEXT_COL
    CONTEXT_COL --> ERR_CLASS

    %% Error Processing Flow
    ERR_CLASS --> SEV_ANAL
    SEV_ANAL --> SYS_CTX & USER_CTX & PROC_CTX & STATE_CTX
    SYS_CTX & USER_CTX & PROC_CTX & STATE_CTX --> DIRECT_IMP
    DIRECT_IMP --> CASCAD_IMP
    CASCAD_IMP --> DATA_IMP

    %% Recovery Flow
    DATA_IMP --> REC_EVAL
    REC_EVAL --> AUTO_REC & MANUAL_REC & FALLBACK
    AUTO_REC & MANUAL_REC & FALLBACK --> STATE_CHECK
    STATE_CHECK --> STATE_SAVE
    STATE_SAVE --> STATE_RESTORE

    %% Notification and Logging Flow
    STATE_RESTORE --> USER_NOTIF & ADMIN_NOTIF & SYS_NOTIF
    USER_NOTIF & ADMIN_NOTIF & SYS_NOTIF --> ERR_LOG
    ERR_LOG --> AUDIT_LOG
    AUDIT_LOG --> DEBUG_LOG

    %% Monitoring Flow
    DEBUG_LOG --> ERR_TRACK
    ERR_TRACK --> PATTERN_ANAL
    PATTERN_ANAL --> TREND_ANAL
    TREND_ANAL --> ALERT_GEN