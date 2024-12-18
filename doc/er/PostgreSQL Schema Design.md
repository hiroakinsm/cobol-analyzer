erDiagram
    analysis_tasks {
        UUID task_id PK
        UUID source_id FK
        string task_type
        string status
        int priority
        string source_path
        jsonb analysis_config
        timestamp started_at
        timestamp completed_at
        string error_message
        string created_by
        timestamp created_at
        timestamp updated_at
    }

    analysis_sources {
        UUID source_id PK
        UUID task_id FK
        string file_path
        string file_type
        string file_hash
        bigint file_size
        string encoding
        int line_count
        jsonb metadata
        timestamp created_at
    }

    analysis_results {
        UUID result_id PK
        UUID task_id FK
        UUID source_id FK
        string result_type
        string status
        string mongodb_collection
        string mongodb_document_id
        jsonb summary_data
        timestamp created_at
        timestamp updated_at
    }

    analysis_logs {
        bigint log_id PK
        UUID task_id FK
        UUID source_id FK
        string log_level
        string component
        string message
        jsonb details
        timestamp created_at
    }

    environment_master {
        serial environment_id PK
        string category
        string sub_category
        string name
        text value
        text description
        boolean is_encrypted
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    single_analysis_master {
        serial analysis_id PK
        string analysis_type
        string process_type
        string parameter_name
        text parameter_value
        text data_type
        text default_value
        boolean is_required
        text validation_rule
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    summary_analysis_master {
        serial summary_id PK
        string analysis_type
        string process_type
        string parameter_name
        text parameter_value
        text data_type
        text default_value
        boolean is_required
        text validation_rule
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    dashboard_master {
        serial dashboard_id PK
        string dashboard_type
        string component_type
        string parameter_name
        text parameter_value
        int display_order
        boolean is_required
        jsonb layout_config
        jsonb style_config
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    document_master {
        serial document_id PK
        string document_type
        string section_type
        string parameter_name
        text parameter_value
        int display_order
        text template_path
        jsonb format_config
        text description
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    benchmark_master {
        serial benchmark_id PK
        string category
        string sub_category
        string metric_name
        text description
        string unit
        numeric min_value
        numeric max_value
        numeric target_value
        numeric warning_threshold
        numeric error_threshold
        text evaluation_rule
        numeric weight
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    analysis_tasks ||--o{ analysis_sources : "has"
    analysis_tasks ||--o{ analysis_results : "generates"
    analysis_tasks ||--o{ analysis_logs : "produces"
    analysis_sources ||--o{ analysis_results : "analyzed_in"
    analysis_sources ||--o{ analysis_logs : "logged_in"
    benchmark_master ||--o{ analysis_results : "evaluates"