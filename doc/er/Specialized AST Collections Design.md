erDiagram
    ast_base_collection {
        ObjectId _id PK
        string source_id FK
        string task_id FK
        string ast_type
        string ast_version
        date created_at
        object metadata
        object source_mapping
    }

    ast_jcl_collection {
        ObjectId _id PK
        string source_id FK
        object jcl_procedures
        object step_definitions
        object dd_statements
        object job_control
        object resource_dependencies
    }

    ast_assembler_collection {
        ObjectId _id PK
        string source_id FK
        object instruction_set
        object macro_definitions
        object register_usage
        object memory_layout
        object linkage_info
    }

    ast_batch_collection {
        ObjectId _id PK
        string source_id FK
        object flow_control
        object checkpoints
        object recovery_points
        object resource_management
        object job_dependencies
    }

    ast_db_collection {
        ObjectId _id PK
        string source_id FK
        object sql_statements
        object db_operations
        object transaction_control
        object cursor_management
        object connection_info
    }

    ast_screen_collection {
        ObjectId _id PK
        string source_id FK
        object screen_layouts
        object field_definitions
        object screen_flow
        object validation_rules
        object screen_io
    }

    ast_form_collection {
        ObjectId _id PK
        string source_id FK
        object form_layouts
        object field_mappings
        object validation_rules
        object event_handlers
        object data_bindings
    }

    ast_dialect_collection {
        ObjectId _id PK
        string source_id FK
        string vendor
        object special_features
        object extensions
        object compatibility_info
        object dialect_specific_syntax
    }

    embedded_elements_collection {
        ObjectId _id PK
        string source_id FK
        string element_type
        object element_data
        object cross_references
        object dependencies
    }

    cross_reference_collection {
        ObjectId _id PK
        string source_id FK
        string reference_type
        object program_references
        object data_references
        object system_references
    }

    integrated_analysis_collection {
        ObjectId _id PK
        string source_id FK
        array ast_references
        object combined_metrics
        object integration_analysis
        object impact_assessment
    }

    ast_base_collection ||--o{ ast_jcl_collection : "extends"
    ast_base_collection ||--o{ ast_assembler_collection : "extends"
    ast_base_collection ||--o{ ast_batch_collection : "extends"
    ast_base_collection ||--o{ ast_db_collection : "extends"
    ast_base_collection ||--o{ ast_screen_collection : "extends"
    ast_base_collection ||--o{ ast_form_collection : "extends"
    ast_base_collection ||--o{ ast_dialect_collection : "extends"
    ast_base_collection ||--o{ embedded_elements_collection : "contains"
    ast_base_collection ||--o{ cross_reference_collection : "references"
    ast_base_collection ||--o{ integrated_analysis_collection : "analyzes"