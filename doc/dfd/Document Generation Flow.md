flowchart TB
    subgraph "Document Generation Core"
        DOC_CTRL["Document Controller"]
        
        subgraph "Content Assembly"
            CONT_COLLECT["Content Collector"]
            TEMP_SELECT["Template Selector"]
            CONT_FORMAT["Content Formatter"]
        end
        
        subgraph "Visualization Generation"
            VIZ_GEN["Visualization Generator"]
            MERM_GEN["Mermaid Generator"]
            CHART_GEN["Chart Generator"]
            METRIC_VIZ["Metrics Visualizer"]
        end
        
        subgraph "Document Formatting"
            FMT_PROC["Format Processor"]
            PDF_GEN["PDF Generator"]
            STYLE_APP["Style Applicator"]
            TOC_GEN["Table of Contents Generator"]
        end
    end

    subgraph "RAG Enhancement"
        RAG_ENHANCE["RAG Content Enhancement"]
        
        subgraph "Content Processing"
            TEXT_ENHANCE["Text Enhancement"]
            DESC_GEN["Description Generator"]
            INSIGHT_GEN["Insight Generator"]
        end
    end

    subgraph "Quality Control"
        DOC_VAL["Document Validator"]
        
        subgraph "Validation Process"
            STRUCT_VAL["Structure Validator"]
            CONT_VAL["Content Validator"]
            FMT_VAL["Format Validator"]
        end
        
        subgraph "Quality Assurance"
            QA_CHECK["Quality Checker"]
            CONSIST_CHECK["Consistency Checker"]
            COMP_CHECK["Completeness Checker"]
        end
    end

    %% Main Document Flow
    DOC_CTRL --> CONT_COLLECT
    CONT_COLLECT --> TEMP_SELECT
    TEMP_SELECT --> CONT_FORMAT

    %% Visualization Flow
    CONT_FORMAT --> VIZ_GEN
    VIZ_GEN --> MERM_GEN & CHART_GEN & METRIC_VIZ

    %% RAG Enhancement Flow
    CONT_FORMAT --> RAG_ENHANCE
    RAG_ENHANCE --> TEXT_ENHANCE
    TEXT_ENHANCE --> DESC_GEN
    DESC_GEN --> INSIGHT_GEN

    %% Document Assembly Flow
    VIZ_GEN & RAG_ENHANCE --> FMT_PROC
    FMT_PROC --> STYLE_APP
    STYLE_APP --> TOC_GEN
    TOC_GEN --> PDF_GEN

    %% Validation Flow
    PDF_GEN --> DOC_VAL
    DOC_VAL --> STRUCT_VAL & CONT_VAL & FMT_VAL
    STRUCT_VAL & CONT_VAL & FMT_VAL --> QA_CHECK
    QA_CHECK --> CONSIST_CHECK
    CONSIST_CHECK --> COMP_CHECK