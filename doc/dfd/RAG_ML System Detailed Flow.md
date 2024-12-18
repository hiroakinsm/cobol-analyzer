flowchart TB
    subgraph "RAG Orchestration"
        RAG_CTRL["RAG Controller"]
        
        subgraph "RAG Criteria"
            CONT_EVAL["Content Evaluation"]
            TASK_EVAL["Task Type Evaluation"]
            CTX_EVAL["Context Evaluation"]
        end
        
        subgraph "RAG Pipeline"
            CTX_BUILD["Context Builder"]
            QUERY_GEN["Query Generator"]
            RET["Retriever"]
            RERANK["Re-ranker"]
            PROMPT_GEN["Prompt Generator"]
        end
    end

    subgraph "Sentence Transformer"
        ST_PROC["Transformer Processor"]
        
        subgraph "Embedding Process"
            PRE_PROC["Text Preprocessing"]
            TOKEN["Tokenization"]
            EMB_GEN["Embedding Generation"]
            EMB_OPT["Embedding Optimization"]
        end
        
        subgraph "Batch Processing"
            BATCH_CTRL["Batch Controller"]
            CHUNK_PROC["Chunk Processor"]
            BATCH_OPT["Batch Optimizer"]
        end
    end

    subgraph "Vector Database Management"
        VEC_CTRL["Vector Controller"]
        
        subgraph "Vector Storage"
            VEC_STORE["Vector Store"]
            VEC_INDEX["Vector Index"]
            VEC_META["Vector Metadata"]
        end
        
        subgraph "Cache Strategy"
            CACHE_CTRL["Cache Controller"]
            FREQ_CACHE["Frequency Cache"]
            TEMP_CACHE["Temporal Cache"]
            EVICT["Cache Eviction"]
        end
    end

    %% RAG Flow
    RAG_CTRL --> CONT_EVAL & TASK_EVAL & CTX_EVAL
    CONT_EVAL & TASK_EVAL & CTX_EVAL --> CTX_BUILD
    CTX_BUILD --> QUERY_GEN
    QUERY_GEN --> RET
    RET --> RERANK
    RERANK --> PROMPT_GEN

    %% Transformer Flow
    ST_PROC --> PRE_PROC
    PRE_PROC --> TOKEN
    TOKEN --> EMB_GEN
    EMB_GEN --> EMB_OPT
    ST_PROC --> BATCH_CTRL
    BATCH_CTRL --> CHUNK_PROC
    CHUNK_PROC --> BATCH_OPT

    %% Vector DB Flow
    VEC_CTRL --> VEC_STORE
    VEC_STORE --> VEC_INDEX
    VEC_INDEX --> VEC_META
    VEC_CTRL --> CACHE_CTRL
    CACHE_CTRL --> FREQ_CACHE & TEMP_CACHE
    FREQ_CACHE & TEMP_CACHE --> EVICT