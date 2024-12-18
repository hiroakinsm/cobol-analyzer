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
        WEB["Web Server\n(172.16.0.25)\nUI Rendering"]
        UI_DASH["Dashboard UI"]
        UI_DOC["Document UI"]
    end

    subgraph "Content Generation"
        DASH_GEN["Dashboard Content Generator"]
        DOC_GEN["Document Content Generator"]
    end

    %% Data Sources to Processing Layer
    COBOL --> APP
    COBOL --> AI
    AST_DB --> APP
    AST_DB --> AI
    META_DB --> APP
    META_DB --> AI
    
    %% Processing Layer Internal Flow
    APP --> AI
    AI --> ST
    
    %% Processing to Storage Layer
    AI --> VECTOR_DB
    AI --> MONGO_NEW
    APP --> MONGO_NEW
    APP --> SQL_LOG
    
    %% Application Server to Content Generation
    APP --> DASH_GEN
    APP --> DOC_GEN
    
    %% Content Generation to Web Server
    DASH_GEN --> WEB
    DOC_GEN --> WEB
    
    %% Web Server to UI Components
    WEB --> UI_DASH
    WEB --> UI_DOC
    
    %% Application Server Controls Web Server
    APP --"Control & Data Flow"--> WEB