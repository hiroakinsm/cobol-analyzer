erDiagram
    ast_collection {
        ObjectId _id PK
        string source_id FK
        string task_id FK
        string ast_type
        string ast_version
        date created_at
        object ast_data
        object metadata
        object source_mapping
    }

    analysis_results_collection {
        ObjectId _id PK
        string result_id FK
        string source_id FK
        string task_id FK
        string analysis_type
        date created_at
        date updated_at
        object details
        object metrics
        array issues
        object references
    }

    metrics_data_collection {
        ObjectId _id PK
        string source_id FK
        string task_id FK
        date created_at
        string metrics_type
        object metrics_data
        object trend_data
        object analysis_details
    }

    document_data_collection {
        ObjectId _id PK
        string task_id FK
        string document_type
        date created_at
        object content
        object formatting
        object references
    }

    cross_reference_collection {
        ObjectId _id PK
        string task_id FK
        string reference_type
        date created_at
        object references
        object dependencies
        object impact_analysis
    }

    ast_collection ||--o{ analysis_results_collection : "analyzed_in"
    analysis_results_collection ||--o{ metrics_data_collection : "contains"
    analysis_results_collection ||--o{ document_data_collection : "generates"
    analysis_results_collection ||--o{ cross_reference_collection : "references"