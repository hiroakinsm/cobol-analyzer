classDiagram
    %% Core Controllers
    class SingleSourceOutputController {
        -masterDataManager: MasterDataManager
        -contentProcessor: ContentProcessor
        -outputManager: OutputManager
        +processOutput(sourceId: UUID): OutputResult
        -validateProcessing(): ValidationResult
    }

    %% Master Data Management
    class MasterDataManager {
        -validationMaster: ValidationMaster
        -thresholdMaster: ThresholdMaster
        -uiMaster: DashboardMaster
        -docMaster: DocumentMaster
        +getMasterData(type: MasterType): MasterData
        -validateMasterData(): ValidationResult
    }

    %% Base Processing
    class ContentProcessor {
        -astProcessor: ASTProcessor
        -metricsProcessor: MetricsProcessor
        -validationProcessor: ValidationProcessor
        +processContent(data: SourceData): ProcessedContent
        -validateContent(): ValidationResult
    }

    %% Dashboard Specific
    class DashboardProcessor {
        -drillDownManager: DrillDownManager
        -viewManager: ViewManager
        -interactionManager: InteractionManager
        +processDashboard(content: ProcessedContent): DashboardContent
        -validateDashboardContent(): ValidationResult
    }

    class DrillDownManager {
        -structureDrillDown: StructureDrillDown
        -metricDrillDown: MetricDrillDown
        -issueDrillDown: IssueDrillDown
        +configureDrillDown(): DrillDownConfig
        -validateDrillDown(): ValidationResult
    }

    class ViewManager {
        -overviewBuilder: OverviewBuilder
        -structureBuilder: StructureBuilder
        -metricBuilder: MetricBuilder
        -alertBuilder: AlertBuilder
        +buildViews(): ViewSet
        -validateViews(): ValidationResult
    }

    %% Document Specific
    class DocumentProcessor {
        -analysisBuilder: AnalysisBuilder
        -sectionBuilder: SectionBuilder
        -referenceBuilder: ReferenceBuilder
        +processDocument(content: ProcessedContent): DocumentContent
        -validateDocumentContent(): ValidationResult
    }

    class AnalysisBuilder {
        -technicalAnalyzer: TechnicalAnalyzer
        -riskAnalyzer: RiskAnalyzer
        -complianceAnalyzer: ComplianceAnalyzer
        +buildAnalysis(): AnalysisContent
        -validateAnalysis(): ValidationResult
    }

    class SectionBuilder {
        -summaryBuilder: SummaryBuilder
        -detailBuilder: DetailBuilder
        -metricsBuilder: MetricsBuilder
        -recommendationBuilder: RecommendationBuilder
        +buildSections(): SectionSet
        -validateSections(): ValidationResult
    }

    %% Output Generation
    class DashboardGenerator {
        -componentBuilder: ComponentBuilder
        -stateController: StateController
        -layoutManager: LayoutManager
        +generateDashboard(content: DashboardContent): Dashboard
        -validateDashboard(): ValidationResult
    }

    class DocumentGenerator {
        -pdfBuilder: PDFBuilder
        -tocGenerator: TOCGenerator
        -formatManager: FormatManager
        +generateDocument(content: DocumentContent): Document
        -validateDocument(): ValidationResult
    }

    %% Relationships
    SingleSourceOutputController *-- MasterDataManager
    SingleSourceOutputController *-- ContentProcessor
    
    ContentProcessor --* DashboardProcessor
    ContentProcessor --* DocumentProcessor
    
    DashboardProcessor *-- DrillDownManager
    DashboardProcessor *-- ViewManager
    
    DocumentProcessor *-- AnalysisBuilder
    DocumentProcessor *-- SectionBuilder
    
    DashboardGenerator --* DashboardProcessor
    DocumentGenerator --* DocumentProcessor
    
    MasterDataManager --* DashboardProcessor
    MasterDataManager --* DocumentProcessor