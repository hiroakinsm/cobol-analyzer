flowchart TB
    subgraph "Data Sources"
        COBOL["/home/koopa-cobol-analyzer/completed\nCOBOL Sources"]
        AST_DB["MongoDB AST\n(172.16.0.17)"]
        META_DB["PostgreSQL Metadata\n(172.16.0.13)"]
    end

    subgraph "Core Processing"
        APP["Application Server\n(172.16.0.27)"]
        RAG["RAG/ML Server\n(172.16.0.19)"]
        
        subgraph "Analysis Pipeline"
            PARSE["Parser & AST Analysis"]
            METRICS["Metrics Analysis"]
            QUAL["Quality Analysis"]
            SEC["Security Analysis"]
        end
        
        subgraph "Content Generation"
            MERM["Mermaid Diagrams"]
            DOC["Documentation"]
            DASH["Dashboards"]
        end
    end

    subgraph "Storage"
        VECTOR_DB["Vector DB\n(172.16.0.15)"]
        NEW_MONGO["New MongoDB Collections"]
    end

    subgraph "Output"
        WEB["Web Server\n(172.16.0.25)"]
        UI["Web UI"]
    end

    %% Data flow
    COBOL --> APP
    AST_DB --> APP
    META_DB --> APP
    
    APP --> PARSE --> METRICS --> QUAL --> SEC
    
    RAG --> |Enhancement| DOC
    RAG --> |Enhancement| DASH
    APP --> MERM --> DOC
    APP --> MERM --> DASH
    
    RAG -.-> VECTOR_DB
    APP --> NEW_MONGO
    
    DOC & DASH --> WEB --> UI