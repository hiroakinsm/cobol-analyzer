flowchart TB
    subgraph "Data Sources"
        COBOL["COBOL Source Files\n(/home/koopa-cobol-analyzer/completed)"]
        AST_DB["MongoDB\n(AST Database)"]
        META_DB["PostgreSQL\n(Metadata Database)"]
    end

    subgraph "Processing Layer"
        APP["Application Server\n(172.16.0.27)\nPython 3.9 Application"]
        AI["AI/RAG/ML Server\n(172.16.0.19)\nLlama 3.1 8B-Inst"]
        ST["Sentence Transformer\n(172.16.0.19)"]
    end

    subgraph "Storage Layer"
        VECTOR_DB["Vector Database\n(172.16.0.15)"]
        MONGO_NEW["MongoDB\n(New Collections)"]
        SQL_LOG["PostgreSQL\n(Logs & Results)"]
    end

    subgraph "Presentation Layer"
        WEB["Web Server\n(172.16.0.25)"]
        DASH["Dashboard"]
        DOC["Document Generator"]
    end

    COBOL --> APP
    AST_DB --> APP
    META_DB --> APP
    
    APP --> AI
    APP --> ST
    
    AI --> VECTOR_DB
    AI --> MONGO_NEW
    APP --> SQL_LOG
    
    MONGO_NEW --> WEB
    SQL_LOG --> WEB
    
    WEB --> DASH
    WEB --> DOC