flowchart TB
    subgraph "Input Layer"
        AST["AST Data\n(MongoDB)"]
        META["Metadata\n(PostgreSQL)"]
        SRC["Source Files"]
    end

    subgraph "RAG System Layer"
        LLAMA["Llama 3.1 8B-Inst\n(4-bit Quantized)"]
        EMBED["Sentence Transformer\nEmbedding Model"]
        VSTORE["Vector Store\n(Cache & Index)"]
        
        subgraph "RAG Pipeline"
            direction TB
            CTX["Context Builder"]
            QG["Query Generator"]
            RET["Retriever"]
            RERANK["Re-ranker"]
            PROMPT["Prompt Generator"]
        end
    end

    subgraph "ML Analysis Layer"
        SEMB["Source Code\nEmbedding"]
        SIMIL["Similarity Analysis"]
        CLUST["Pattern Clustering"]
        ANOM["Anomaly Detection"]
    end

    subgraph "Generation Layer"
        FLOW["Flowchart Generator"]
        SEQ["Sequence Diagram\nGenerator"]
        METR["Code Metrics\nGenerator"]
        SEC["Security Analysis\nGenerator"]
        DOC["Documentation\nGenerator"]
    end

    %% Input Layer to Processing
    AST --> CTX
    META --> CTX
    SRC --> SEMB

    %% RAG Pipeline Flow
    CTX --> QG
    QG --> RET
    RET --> RERANK
    RERANK --> PROMPT
    PROMPT --> LLAMA

    %% Vector Store Integration
    EMBED --> VSTORE
    RET --> VSTORE
    RERANK --> VSTORE

    %% ML Analysis Flow
    SEMB --> SIMIL
    SEMB --> CLUST
    SEMB --> ANOM

    %% Generation Integration
    LLAMA --> FLOW
    LLAMA --> SEQ
    LLAMA --> METR
    LLAMA --> SEC
    LLAMA --> DOC

    %% ML to Generation Integration
    SIMIL --> DOC
    CLUST --> METR
    ANOM --> SEC