flowchart TB
    subgraph "Analysis Feedback Core"
        FEED_CTRL["Feedback Controller"]
        
        subgraph "Result Processing"
            RES_COL["Result Collector"]
            RES_VAL["Result Validator"]
            RES_AGG["Result Aggregator"]
        end
        
        subgraph "Error Handling"
            ERR_DET["Error Detector"]
            ERR_CLASS["Error Classifier"]
            RETRY_CTRL["Retry Controller"]
            REC_STRAT["Recovery Strategy"]
        end
    end

    subgraph "Result Validation"
        subgraph "Validation Rules"
            STRUCT_CHECK["Structure Check"]
            DATA_CHECK["Data Validation"]
            METRIC_CHECK["Metrics Validation"]
            REL_CHECK["Relationship Check"]
        end
        
        subgraph "Quality Control"
            THRESH_CHECK["Threshold Check"]
            CONSIST_CHECK["Consistency Check"]
            COMP_CHECK["Completeness Check"]
        end
    end

    subgraph "Cache Management"
        CACHE_CTRL["Cache Controller"]
        
        subgraph "Cache Strategy"
            RESULT_CACHE["Result Cache"]
            PARTIAL_CACHE["Partial Results Cache"]
            RETRY_CACHE["Retry Information Cache"]
        end
        
        subgraph "Cache Optimization"
            EVICT_CTRL["Eviction Controller"]
            PRIO_CTRL["Priority Controller"]
            SPACE_MGR["Space Manager"]
        end
    end

    subgraph "Feedback Channels"
        UI_FEED["UI Feedback"]
        LOG_FEED["Log Feedback"]
        EMAIL_FEED["Email Notification"]
    end

    %% Main Flow
    FEED_CTRL --> RES_COL
    RES_COL --> RES_VAL
    RES_VAL --> RES_AGG

    %% Error Flow
    RES_VAL --> ERR_DET
    ERR_DET --> ERR_CLASS
    ERR_CLASS --> RETRY_CTRL
    RETRY_CTRL --> REC_STRAT

    %% Validation Flow
    RES_VAL --> STRUCT_CHECK & DATA_CHECK & METRIC_CHECK & REL_CHECK
    STRUCT_CHECK & DATA_CHECK & METRIC_CHECK & REL_CHECK --> THRESH_CHECK
    THRESH_CHECK --> CONSIST_CHECK
    CONSIST_CHECK --> COMP_CHECK

    %% Cache Flow
    RES_AGG --> CACHE_CTRL
    CACHE_CTRL --> RESULT_CACHE & PARTIAL_CACHE & RETRY_CACHE
    RESULT_CACHE & PARTIAL_CACHE & RETRY_CACHE --> EVICT_CTRL
    EVICT_CTRL --> PRIO_CTRL
    PRIO_CTRL --> SPACE_MGR

    %% Feedback Distribution
    FEED_CTRL --> UI_FEED & LOG_FEED & EMAIL_FEED