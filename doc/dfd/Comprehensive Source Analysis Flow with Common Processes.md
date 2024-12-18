flowchart TB
    subgraph "Common Analysis Foundation"
        direction TB
        subgraph "Base Parser Framework"
            LEX["Lexical\nAnalyzer"]
            PARSE["Parser"]
            AST["AST\nGenerator"]
            STD_VAL["Syntax\nValidator"]
        end

        subgraph "Common Metrics Engine"
            MET_COL["Metrics\nCollector"]
            MET_EVAL["Metrics\nEvaluator"]
            MET_NORM["Metrics\nNormalizer"]
        end

        subgraph "Benchmark Engine"
            BM_EVAL["Benchmark\nEvaluator"]
            BM_COMP["Compliance\nChecker"]
            BM_REPORT["Benchmark\nReporter"]
        end
    end

    subgraph "Source Specific Analysis"
        direction TB
        subgraph "COBOL Analysis"
            COBOL_PARSE["COBOL\nParser"]
            COBOL_AST["COBOL AST\nGenerator"]
            
            subgraph "COBOL Structure"
                DIV_ANA["Division\nAnalyzer"]
                SECT_ANA["Section\nAnalyzer"]
                PROG_FLOW["Program Flow\nAnalyzer"]
            end
            
            subgraph "Dialect Analysis"
                VENDOR["Vendor Dialect\nAnalyzer"]
                CHAR_SET["Character Set\nAnalyzer"]
                SPEC_CMD["Special Command\nAnalyzer"]
            end
        end

        subgraph "JCL Analysis"
            JCL_PARSE["JCL\nParser"]
            JCL_AST["JCL AST\nGenerator"]
            JCL_STRUCT["JCL Structure\nAnalyzer"]
        end

        subgraph "Assembler Analysis"
            ASM_PARSE["Assembler\nParser"]
            ASM_AST["Assembler AST\nGenerator"]
            ASM_STRUCT["Assembler\nStructure Analyzer"]
        end
    end

    subgraph "Embedded Elements Analysis"
        direction TB
        subgraph "Database Integration"
            DB_PARSE["DB Statement\nParser"]
            SQL_ANA["SQL\nAnalyzer"]
            TX_ANA["Transaction\nAnalyzer"]
            DB_PAT["Access Pattern\nAnalyzer"]
        end

        subgraph "Assembler Integration"
            ASM_IF["Interface\nAnalyzer"]
            ASM_DATA["Data Exchange\nAnalyzer"]
            ASM_REG["Register Usage\nAnalyzer"]
        end

        subgraph "Batch Processing"
            BATCH_STRUCT["Batch Structure\nAnalyzer"]
            STEP_ANA["Step\nAnalyzer"]
            CP_REST["Checkpoint/Restart\nAnalyzer"]
            SORT_MERGE["Sort/Merge\nAnalyzer"]
        end

        subgraph "Screen/Form Processing"
            SCREEN["Screen\nAnalyzer"]
            FORM["Form\nAnalyzer"]
            UI_FLOW["UI Flow\nAnalyzer"]
            DATA_MAP["Data Mapping\nAnalyzer"]
        end
    end

    subgraph "External Reference Integration"
        direction TB
        subgraph "Security Reference"
            CVE_CHECK["CVE\nChecker"]
            CVSS_EVAL["CVSS\nEvaluator"]
            SEC_IMPACT["Security Impact\nAnalyzer"]
        end

        subgraph "Benchmark Reference"
            CODE_STD["Coding Standard\nReference"]
            QUAL_STD["Quality Standard\nReference"]
            PERF_STD["Performance Standard\nReference"]
            SEC_STD["Security Standard\nReference"]
            PORT_STD["Portability Standard\nReference"]
        end
    end

    subgraph "Quality & Security Analysis"
        direction TB
        subgraph "Quality Analysis"
            QUAL_ANA["Quality\nAnalyzer"]
            COMP_ANA["Complexity\nAnalyzer"]
            MAINT_ANA["Maintainability\nAnalyzer"]
        end

        subgraph "Security Analysis"
            VULN_SCAN["Vulnerability\nScanner"]
            ACCESS_ANA["Access Control\nAnalyzer"]
            ERR_ANA["Error Handling\nAnalyzer"]
        end

        subgraph "Cross-Reference Analysis"
            XREF_PROG["Program\nCross-Reference"]
            XREF_DATA["Data\nCross-Reference"]
            XREF_SYS["System\nCross-Reference"]
        end
    end

    %% Base Framework Flows
    LEX --> PARSE --> AST --> STD_VAL
    AST --> MET_COL --> MET_EVAL --> MET_NORM
    MET_NORM --> BM_EVAL --> BM_COMP --> BM_REPORT

    %% Source Specific Flows
    AST --> COBOL_PARSE & JCL_PARSE & ASM_PARSE
    COBOL_PARSE --> COBOL_AST --> DIV_ANA & VENDOR
    JCL_PARSE --> JCL_AST --> JCL_STRUCT
    ASM_PARSE --> ASM_AST --> ASM_STRUCT

    %% Embedded Analysis Flows
    COBOL_AST --> DB_PARSE --> SQL_ANA --> TX_ANA --> DB_PAT
    COBOL_AST --> ASM_IF --> ASM_DATA --> ASM_REG
    COBOL_AST --> BATCH_STRUCT --> STEP_ANA --> CP_REST --> SORT_MERGE
    COBOL_AST --> SCREEN & FORM --> UI_FLOW --> DATA_MAP

    %% External Reference Flows
    AST --> CVE_CHECK --> CVSS_EVAL --> SEC_IMPACT
    BM_EVAL --> CODE_STD & QUAL_STD & PERF_STD & SEC_STD & PORT_STD

    %% Quality & Security Flows
    AST --> QUAL_ANA --> COMP_ANA --> MAINT_ANA
    AST --> VULN_SCAN --> ACCESS_ANA --> ERR_ANA
    AST --> XREF_PROG & XREF_DATA --> XREF_SYS