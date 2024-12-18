classDiagram
    %% Core Controllers
    class SummaryAnalysisController {
        -aggregationManager: AggregationManager
        -dashboardProcessor: DashboardDataProcessor
        -documentProcessor: DocumentDataProcessor
        +processSummary(sourceIds: List~UUID~): SummaryResult
        -validateProcessing(): ValidationResult
    }

    %% Base Aggregation
    class AggregationManager {
        -astAggregator: ASTAggregator
        -metricsAggregator: MetricsAggregator
        -trendAnalyzer: TrendAnalyzer
        +aggregateData(sourceData: List~SourceData~): AggregatedData
        -validateAggregation(): ValidationResult
    }

    %% Dashboard Specific Processing
    class DashboardDataProcessor {
        -realtimeProcessor: RealtimeProcessor
        -interactiveBuilder: InteractiveBuilder
        -alertManager: AlertManager
        +processDashboardData(data: AggregatedData): DashboardData
        -validateDashboardData(): ValidationResult
    }

    class RealtimeProcessor {
        -metricStreamer: MetricStreamer
        -updateManager: UpdateManager
        -cacheManager: CacheManager
        +processRealtimeData(): RealtimeData
        -manageUpdates(): UpdateResult
    }

    class InteractiveBuilder {
        -chartBuilder: InteractiveChartBuilder
        -drillDownProcessor: DrillDownProcessor
        -filterManager: FilterManager
        +buildInteractiveElements(): InteractiveElements
        -validateInteractivity(): ValidationResult
    }

    class AlertManager {
        -thresholdMonitor: ThresholdMonitor
        -trendMonitor: TrendMonitor
        -complianceMonitor: ComplianceMonitor
        +manageAlerts(): AlertConfiguration
        -validateAlerts(): ValidationResult
    }

    %% Document Specific Processing
    class DocumentDataProcessor {
        -technicalAnalyzer: TechnicalAnalyzer
        -businessAnalyzer: BusinessAnalyzer
        -reportBuilder: DetailedReportBuilder
        +processDocumentData(data: AggregatedData): DocumentData
        -validateDocumentData(): ValidationResult
    }

    class TechnicalAnalyzer {
        -metricAnalyzer: MetricAnalyzer
        -riskAssessor: RiskAssessor
        -qualityEvaluator: QualityEvaluator
        +analyzeTechnicalAspects(): TechnicalAnalysis
        -validateAnalysis(): ValidationResult
    }

    class BusinessAnalyzer {
        -impactAnalyzer: ImpactAnalyzer
        -resourceEstimator: ResourceEstimator
        -maintenancePlanner: MaintenancePlanner
        +analyzeBusinessAspects(): BusinessAnalysis
        -validateAnalysis(): ValidationResult
    }

    class DetailedReportBuilder {
        -metricReporter: MetricReporter
        -patternReporter: PatternReporter
        -recommendationBuilder: RecommendationBuilder
        +buildDetailedReports(): DetailedReports
        -validateReports(): ValidationResult
    }

    %% Output Generation
    class DashboardGenerator {
        -layoutManager: DashboardLayoutManager
        -componentBuilder: InteractiveComponentBuilder
        -stateManager: DashboardStateManager
        +generateDashboard(data: DashboardData): Dashboard
        -validateDashboard(): ValidationResult
    }

    class DocumentGenerator {
        -structureBuilder: DocumentStructureBuilder
        -contentFormatter: ContentFormatter
        -pdfBuilder: PDFBuilder
        +generateDocument(data: DocumentData): Document
        -validateDocument(): ValidationResult
    }

    %% Shared Components
    class ValidationManager {
        -ruleValidator: RuleValidator
        -thresholdValidator: ThresholdValidator
        -complianceValidator: ComplianceValidator
        +validateData(data: Any): ValidationResult
        -applyValidationRules(): RuleResult
    }

    class MasterDataManager {
        -ruleMaster: RuleMaster
        -benchmarkMaster: BenchmarkMaster
        -thresholdMaster: ThresholdMaster
        +getMasterData(type: MasterType): MasterData
        -validateMasterData(): ValidationResult
    }

    %% Relationships
    SummaryAnalysisController *-- AggregationManager
    SummaryAnalysisController *-- DashboardDataProcessor
    SummaryAnalysisController *-- DocumentDataProcessor

    DashboardDataProcessor *-- RealtimeProcessor
    DashboardDataProcessor *-- InteractiveBuilder
    DashboardDataProcessor *-- AlertManager

    DocumentDataProcessor *-- TechnicalAnalyzer
    DocumentDataProcessor *-- BusinessAnalyzer
    DocumentDataProcessor *-- DetailedReportBuilder

    DashboardGenerator --* DashboardDataProcessor
    DocumentGenerator --* DocumentDataProcessor

    ValidationManager --* DashboardDataProcessor
    ValidationManager --* DocumentDataProcessor
    MasterDataManager --* ValidationManager