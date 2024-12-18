flowchart TB
    subgraph "Authentication Flow"
        AUTH_CTRL["Authentication Controller"]
        
        subgraph "Login Process"
            LOGIN_REQ["Login Request"]
            CRED_VAL["Credential Validator"]
            PASS_CHECK["Password Validator"]
            MFA_CHECK["MFA Validator"]
        end
        
        subgraph "Session Management"
            SESS_GEN["Session Generator"]
            SESS_TRACK["Session Tracker"]
            SESS_VAL["Session Validator"]
            SESS_EXP["Session Expiry"]
        end
    end

    subgraph "Password Management"
        PASS_CTRL["Password Controller"]
        
        subgraph "Password Policy"
            POL_CHECK["Policy Checker"]
            COMP_CHECK["Complexity Checker"]
            HIST_CHECK["History Checker"]
            EXP_CHECK["Expiry Checker"]
        end
        
        subgraph "Password Operations"
            PASS_HASH["Password Hasher"]
            PASS_RESET["Password Reset"]
            TEMP_PASS["Temporary Password"]
        end
    end

    subgraph "Access Control"
        ACC_CTRL["Access Controller"]
        
        subgraph "Role Management"
            ROLE_CHECK["Role Checker"]
            PERM_CHECK["Permission Checker"]
            ROLE_ASSIGN["Role Assignment"]
        end
        
        subgraph "Access Logging"
            LOG_GEN["Log Generator"]
            LOG_STORE["Log Storage"]
            LOG_ROTATE["Log Rotation"]
            LOG_ALERT["Alert Generator"]
        end
    end

    subgraph "Security Monitoring"
        SEC_MON["Security Monitor"]
        
        subgraph "Activity Monitoring"
            ACT_TRACK["Activity Tracker"]
            FAIL_DET["Failure Detector"]
            THREAT_DET["Threat Detector"]
        end
        
        subgraph "Audit Trail"
            AUDIT_LOG["Audit Logger"]
            AUDIT_REP["Audit Reporter"]
            AUDIT_ALERT["Audit Alerter"]
        end
    end

    %% Authentication Flow
    LOGIN_REQ --> CRED_VAL
    CRED_VAL --> PASS_CHECK
    PASS_CHECK --> MFA_CHECK
    MFA_CHECK --> SESS_GEN
    SESS_GEN --> SESS_TRACK
    SESS_TRACK --> SESS_VAL
    SESS_VAL --> SESS_EXP

    %% Password Flow
    PASS_CHECK --> POL_CHECK
    POL_CHECK --> COMP_CHECK & HIST_CHECK & EXP_CHECK
    PASS_RESET --> PASS_HASH
    TEMP_PASS --> PASS_HASH

    %% Access Control Flow
    ACC_CTRL --> ROLE_CHECK
    ROLE_CHECK --> PERM_CHECK
    PERM_CHECK --> ROLE_ASSIGN
    ACC_CTRL --> LOG_GEN
    LOG_GEN --> LOG_STORE
    LOG_STORE --> LOG_ROTATE
    LOG_ALERT --> SEC_MON

    %% Security Monitoring Flow
    SEC_MON --> ACT_TRACK
    ACT_TRACK --> FAIL_DET & THREAT_DET
    FAIL_DET --> AUDIT_LOG
    THREAT_DET --> AUDIT_ALERT
    AUDIT_LOG --> AUDIT_REP