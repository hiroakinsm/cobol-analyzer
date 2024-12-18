flowchart TB
    subgraph "UI Layer"
        MENU["Analysis Menu"]
        SRC_SEL["Source Selector"]
        TASK_SEL["Task Type Selector"]
        PROG_MON["Progress Monitor"]
    end

    subgraph "Common Analysis Foundation"
        direction TB
        subgraph "Base Parser Framework"
            LEX["Lexical Analyzer"]
            PARSE["Parser"]
            AST["AST Generator"]
        end

        subgraph "Analysis Core"
            ANALYSIS_CTL["Analysis Controller"]
            TASK_MGR["Task Manager"]
            SRC_MGR["Source Manager"]
        end

        subgraph "Metrics Engine"
            MET_COL["Metrics Collector"]
            MET_EVAL["Metrics Evaluator"]
        end
    end

    subgraph "Application Control"
        direction TB
        SVC_CTL["Service Controller"]
        SRC_VALID["Source Validator"]
        DEP_CHECK["Dependency Checker"]
        
        subgraph "Task Coordination"
            SINGLE_COORD["Single Analysis Coordinator"]
            MULTI_COORD["Multi Analysis Coordinator"]
            TASK_MON["Task Monitor"]
        end
    end

    subgraph "RAG/ML Enhancement"
        direction TB
        LLM["LLM Model"]
        ST["Sentence Transformer"]
        CONT_FIN["Content Finalizer"]
        DOC_FIN["Document Finalizer"]
    end

    %% UI Flow
    MENU --> SRC_SEL
    SRC_SEL --> TASK_SEL
    TASK_SEL --> SVC_CTL

    %% Source Validation Flow
    SVC_CTL --> SRC_VALID
    SRC_VALID --> SRC_MGR
    SRC_VALID --> DEP_CHECK

    %% Analysis Flow
    DEP_CHECK --> SINGLE_COORD
    DEP_CHECK --> MULTI_COORD
    SINGLE_COORD --> ANALYSIS_CTL
    MULTI_COORD --> ANALYSIS_CTL

    %% Task Management
    TASK_MGR --> TASK_MON
    TASK_MON --> PROG_MON

    %% Processing Flow
    ANALYSIS_CTL --> LEX
    LEX --> PARSE
    PARSE --> AST
    AST --> MET_COL
    MET_COL --> MET_EVAL

    %% Enhancement Flow
    MET_EVAL --> CONT_FIN
    CONT_FIN --> DOC_FIN

    %% Monitoring Flow
    TASK_MON --> PROG_MON