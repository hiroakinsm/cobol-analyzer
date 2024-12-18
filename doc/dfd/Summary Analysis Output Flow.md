flowchart TB
    subgraph "Analysis Input Sources"
        AST_COL["AST Collection\nfrom Multiple Sources"]
        METRIC_COL["Metrics Collection\nfrom Multiple Sources"]
        BENCH_DB["Benchmark Master\nThreshold Data"]
        VALID_DB["Validation Master\nRule Sets"]
    end

    subgraph "Aggregation Processing"
        subgraph "Data Aggregation"
            AST_AGG["AST Aggregator"]
            METRIC_AGG["Metrics Aggregator"]
            TREND_AGG["Trend Analyzer"]
        end

        subgraph "Pattern Analysis"
            STRUCT_PAT["Structure Pattern\nAnalyzer"]
            CODE_PAT["Coding Pattern\nAnalyzer"]
            ISSUE_PAT["Issue Pattern\nAnalyzer"]
        end

        subgraph "Validation Processing"
            MASTER_VAL["Master Based\nValidator"]
            RULE_APP["Rule Application"]
            THRESH_VAL["Threshold\nValidator"]
        end
    end

    subgraph "Dashboard Specific Processing"
        DASH_PROC["Dashboard Data Processor"]
        
        subgraph "Interactive Metrics"
            REAL_METRIC["Realtime Metrics"]
            INTERACT_CHART["Interactive Charts"]
            DRILL_DOWN["Drill-Down Analysis"]
        end
        
        subgraph "Dashboard Views"
            PROJ_SUM["Project Summary View"]
            TREND_VIEW["Trend Analysis View"]
            ISSUE_TRACK["Issue Tracking View"]
        end
        
        subgraph "Alert Components"
            THRESH_ALERT["Threshold Alerts"]
            TREND_ALERT["Trend Alerts"]
            COMP_ALERT["Compliance Alerts"]
        end
    end

    subgraph "Document Specific Processing"
        DOC_PROC["Document Data Processor"]
        
        subgraph "Technical Analysis"
            TECH_SUMM["Technical Summary"]
            RISK_ANAL["Risk Analysis"]
            QUAL_ANAL["Quality Analysis"]
        end
        
        subgraph "Business Impact"
            BIZ_IMPACT["Business Impact"]
            RESOURCE_EST["Resource Estimation"]
            MAINT_PLAN["Maintenance Planning"]
        end
        
        subgraph "Detailed Reports"
            DETAIL_METRIC["Detailed Metrics"]
            PATTERN_REP["Pattern Reports"]
            REC_DETAIL["Detailed Recommendations"]
        end
    end

    subgraph "Output Generation"
        subgraph "Dashboard Generation"
            DASH_GEN["Dashboard Generator"]
            DASH_LAYOUT["Dashboard Layout"]
            INTERACT_COMP["Interactive Components"]
        end

        subgraph "Document Generation"
            DOC_GEN["Document Generator"]
            DOC_STRUCT["Document Structure"]
            PDF_GEN["PDF Generation"]
        end
    end

    %% Base Flow
    AST_COL & METRIC_COL --> AST_AGG & METRIC_AGG
    AST_AGG & METRIC_AGG --> TREND_AGG
    BENCH_DB --> THRESH_VAL
    VALID_DB --> MASTER_VAL

    %% Dashboard Specific Flow
    TREND_AGG --> DASH_PROC
    METRIC_AGG --> REAL_METRIC
    STRUCT_PAT & CODE_PAT --> INTERACT_CHART
    ISSUE_PAT --> DRILL_DOWN
    MASTER_VAL --> THRESH_ALERT
    TREND_AGG --> TREND_ALERT
    RULE_APP --> COMP_ALERT

    %% Document Specific Flow
    AST_AGG --> TECH_SUMM
    METRIC_AGG --> RISK_ANAL
    TREND_AGG --> QUAL_ANAL
    PATTERN_REP --> DETAIL_METRIC
    STRUCT_PAT & CODE_PAT --> PATTERN_REP
    ISSUE_PAT --> REC_DETAIL

    %% Output Generation Flow
    PROJ_SUM & TREND_VIEW & ISSUE_TRACK --> DASH_LAYOUT
    THRESH_ALERT & TREND_ALERT & COMP_ALERT --> INTERACT_COMP
    DASH_LAYOUT & INTERACT_COMP --> DASH_GEN

    TECH_SUMM & RISK_ANAL & QUAL_ANAL --> DOC_STRUCT
    BIZ_IMPACT & RESOURCE_EST & MAINT_PLAN --> DOC_STRUCT
    DETAIL_METRIC & PATTERN_REP & REC_DETAIL --> DOC_STRUCT
    DOC_STRUCT --> DOC_GEN --> PDF_GEN