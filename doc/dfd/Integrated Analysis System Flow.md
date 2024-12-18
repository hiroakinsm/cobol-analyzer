flowchart TB
    subgraph "Common Analysis Foundation"
        direction TB
        PARSER["Parser Framework"]
        METRICS["Metrics Engine"]
        ANALYSIS["Analysis Engine"]
        CTL["Analysis Controller"]
        CONT_GEN["Content Generation Core"]
        DOC_GEN["Document Generation Core"]
    end

    subgraph "Application Server Control"
        direction TB
        SVC_CTL["Service Controller"]
        TASK_MON["Task Monitor"]
        MULTI_SRC["Multi-Source Coordinator"]
    end

    subgraph "RAG/ML System"
        direction TB
        LLM["LLM Model\nLlama 3.1 8B-Inst"]
        ST["Sentence Transformer"]
        
        subgraph "Content Enhancement"
            direction TB
            CONT_FIN["Content Finalizer"]
            DOC_FIN["Document Finalizer"]
            VEC_STORE["Vector Store Cache"]
        end
        
        subgraph "Analysis Enhancement"
            direction TB
            PAT_ANL["Pattern Analysis"]
            SIM_ANL["Similarity Analysis"]
            ANOM_DET["Anomaly Detection"]
        end
    end

    subgraph "Storage Layer"
        direction TB
        MONGO_DB[(MongoDB)]
        PG_DB[(PostgreSQL)]
        VEC_DB[(Vector DB)]
    end

    %% Common Analysis to App Server
    CTL --> SVC_CTL
    ANALYSIS --> TASK_MON
    CONT_GEN --> MULTI_SRC

    %% App Server to RAG/ML
    SVC_CTL --> LLM
    TASK_MON --> PAT_ANL
    MULTI_SRC --> SIM_ANL

    %% Content Generation Flow
    CONT_GEN --> CONT_FIN
    DOC_GEN --> DOC_FIN
    
    %% Analysis Enhancement Flow
    PAT_ANL --> VEC_STORE
    SIM_ANL --> VEC_STORE
    ANOM_DET --> VEC_STORE

    %% Storage Integration
    CONT_FIN --> MONGO_DB
    DOC_FIN --> MONGO_DB
    VEC_STORE --> VEC_DB
    TASK_MON --> PG_DB