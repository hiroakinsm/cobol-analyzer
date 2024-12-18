flowchart TB
    subgraph "Analysis Input Sources"
        AST_IN["AST Data\nfrom BaseParser"]
        METRIC_IN["Metrics Data\nfrom MetricsEngine"]
        BENCH_IN["Benchmark Data\nfrom BenchmarkEngine"]
        RAG_IN["RAG Enhanced Content"]
    end

    subgraph "Master Data Sources"
        VALID_MASTER["Validation Master\nRule Sets"]
        THRESH_MASTER["Threshold Master"]
        UI_MASTER["Dashboard Master\nLayout & Components"]
        DOC_MASTER["Document Master\nTemplates & Structure"]
    end

    subgraph "Base Content Processing"
        subgraph "Code Analysis"
            STRUCT_ANAL["Structure Analyzer"]
            FLOW_GEN["Flowchart Generator"]
            SEQ_GEN["Sequence Generator"]
        end

        subgraph "Metrics Processing"
            COMP_METRIC["Complexity Metrics"]
            QUAL_METRIC["Quality Metrics"]
            SEC_METRIC["Security Metrics"]
            PERF_METRIC["Performance Metrics"]
        end

        subgraph "Validation Processing"
            RULE_VAL["Rule Validation"]
            BM_VAL["Benchmark Validation"]
            THRESH_VAL["Threshold Validation"]
        end
    end

    subgraph "Dashboard Specific Processing"
        DASH_PROC["Dashboard Data Processor"]
        
        subgraph "Interactive Analysis"
            DRILL_STRUCT["Structure Drill-Down"]
            DRILL_METRIC["Metrics Drill-Down"]
            DRILL_ISSUE["Issue Drill-Down"]
        end
        
        subgraph "Dashboard Views"
            OVERVIEW["Overview Panel"]
            STRUCT_VIEW["Structure View"]
            METRIC_VIEW["Metrics View"]
            ALERT_VIEW["Alert View"]
        end
        
        subgraph "Interactive Elements"
            ZOOM_CTRL["Zoom Controls"]
            FILTER_CTRL["Filter Controls"]
            NAV_CTRL["Navigation Controls"]
        end
    end

    subgraph "Document Specific Processing"
        DOC_PROC["Document Data Processor"]
        
        subgraph "Analysis Content"
            TECH_ANAL["Technical Analysis"]
            RISK_ANAL["Risk Analysis"]
            COMP_ANAL["Compliance Analysis"]
        end
        
        subgraph "Document Sections"
            EXEC_SUM["Executive Summary"]
            DETAIL_ANAL["Detailed Analysis"]
            METRIC_REP["Metrics Report"]
            REC_SEC["Recommendations"]
        end
        
        subgraph "Reference Content"
            BM_REF["Benchmark Reference"]
            RULE_REF["Rule Reference"]
            THRESH_REF["Threshold Reference"]
        end
    end

    subgraph "Output Generation"
        subgraph "Dashboard Output"
            DASH_GEN["Dashboard Generator"]
            COMP_BUILD["Component Builder"]
            STATE_CTRL["State Controller"]
        end

        subgraph "Document Output"
            DOC_GEN["Document Generator"]
            PDF_BUILD["PDF Builder"]
            TOC_GEN["TOC Generator"]
        end
    end

    %% Master Data Flow
    VALID_MASTER --> RULE_VAL
    THRESH_MASTER --> THRESH_VAL
    UI_MASTER --> DASH_PROC
    DOC_MASTER --> DOC_PROC

    %% Base Content Flow
    AST_IN --> STRUCT_ANAL & FLOW_GEN & SEQ_GEN
    METRIC_IN --> COMP_METRIC & QUAL_METRIC & SEC_METRIC & PERF_METRIC
    BENCH_IN --> BM_VAL

    %% Dashboard Flow
    STRUCT_ANAL --> DRILL_STRUCT
    COMP_METRIC & QUAL_METRIC --> DRILL_METRIC
    SEC_METRIC & PERF_METRIC --> DRILL_ISSUE
    
    DRILL_STRUCT & DRILL_METRIC & DRILL_ISSUE --> OVERVIEW
    DRILL_STRUCT --> STRUCT_VIEW
    DRILL_METRIC --> METRIC_VIEW
    DRILL_ISSUE --> ALERT_VIEW

    OVERVIEW & STRUCT_VIEW & METRIC_VIEW & ALERT_VIEW --> COMP_BUILD
    ZOOM_CTRL & FILTER_CTRL & NAV_CTRL --> STATE_CTRL
    
    %% Document Flow
    STRUCT_ANAL & FLOW_GEN & SEQ_GEN --> TECH_ANAL
    COMP_METRIC & QUAL_METRIC --> RISK_ANAL
    SEC_METRIC & PERF_METRIC --> COMP_ANAL

    TECH_ANAL --> EXEC_SUM & DETAIL_ANAL
    RISK_ANAL & COMP_ANAL --> METRIC_REP & REC_SEC
    BM_REF & RULE_REF & THRESH_REF --> DETAIL_ANAL

    DOC_GEN --> PDF_BUILD --> TOC_GEN