flowchart TB
    subgraph "Input Validation"
        INPUT_RECV["Input Received"]
        CONTEXT_BUILD["Context Building"]
        RULE_LOAD["Rule Loading"]
        
        subgraph "Context Validation"
            SRC_VAL["Source Validation"]
            USER_VAL["User Validation"]
            PARAM_VAL["Parameter Validation"]
        end
    end

    subgraph "COBOL Analysis Validation"
        subgraph "Syntax Validation"
            LEX_CHECK["Lexical Check"]
            GRAM_CHECK["Grammar Check"]
            STRUCT_CHECK["Structure Check"]
        end
        
        subgraph "Semantic Validation"
            DATA_CHECK["Data Division Check"]
            PROC_CHECK["Procedure Division Check"]
            FLOW_CHECK["Control Flow Check"]
        end
        
        subgraph "Style Validation"
            NAME_CHECK["Naming Check"]
            FORMAT_CHECK["Format Check"]
            COMMENT_CHECK["Comment Check"]
        end
    end

    subgraph "Metrics Validation"
        subgraph "Complexity Metrics"
            CYCLO_CHECK["Cyclomatic Complexity"]
            HALST_CHECK["Halstead Metrics"]
            MAINT_CHECK["Maintainability Index"]
        end
        
        subgraph "Quality Metrics"
            DOC_CHECK["Documentation Quality"]
            TEST_CHECK["Testability"]
            MODULAR_CHECK["Modularity"]
        end
        
        subgraph "Performance Metrics"
            MEM_CHECK["Memory Usage"]
            CPU_CHECK["CPU Usage"]
            IO_CHECK["I/O Operations"]
        end
    end

    subgraph "Rule Execution"
        RULE_EXEC["Rule Execution"]
        
        subgraph "Rule Processing"
            DEP_CHECK["Dependency Check"]
            PRIO_CHECK["Priority Check"]
            ORDER_CHECK["Order Check"]
        end
        
        subgraph "Result Collection"
            RES_COL["Result Collection"]
            RES_AGG["Result Aggregation"]
            RES_EVAL["Result Evaluation"]
        end
    end

    %% Input Flow
    INPUT_RECV --> CONTEXT_BUILD
    CONTEXT_BUILD --> RULE_LOAD
    RULE_LOAD --> SRC_VAL & USER_VAL & PARAM_VAL

    %% COBOL Analysis Flow
    SRC_VAL --> LEX_CHECK & GRAM_CHECK & STRUCT_CHECK
    GRAM_CHECK --> DATA_CHECK & PROC_CHECK
    STRUCT_CHECK --> FLOW_CHECK
    FLOW_CHECK --> NAME_CHECK & FORMAT_CHECK & COMMENT_CHECK

    %% Metrics Flow
    PARAM_VAL --> CYCLO_CHECK & HALST_CHECK & MAINT_CHECK
    MAINT_CHECK --> DOC_CHECK & TEST_CHECK & MODULAR_CHECK
    MODULAR_CHECK --> MEM_CHECK & CPU_CHECK & IO_CHECK

    %% Rule Execution Flow
    FORMAT_CHECK & IO_CHECK --> RULE_EXEC
    RULE_EXEC --> DEP_CHECK --> PRIO_CHECK --> ORDER_CHECK
    ORDER_CHECK --> RES_COL --> RES_AGG --> RES_EVAL