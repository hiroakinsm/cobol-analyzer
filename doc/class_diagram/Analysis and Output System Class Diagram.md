classDiagram
    %% Analysis Types
    class AnalysisManager {
        -singleAnalyzer: SingleSourceAnalyzer
        -summaryAnalyzer: SummaryAnalyzer
        +analyzeSingleSource(source: Source): AnalysisResult
        +analyzeSummary(sources: List~Source~): SummaryResult
        -validateResults(): ValidationResult
    }

    class SummaryAnalyzer {
        -qualityAnalyzer: QualityAnalyzer
        -securityAnalyzer: SecurityAnalyzer
        -benchmarkAnalyzer: BenchmarkAnalyzer
        +generateSummary(results: List~Result~): Summary
        +compareResults(): ComparisonResult
        -aggregateMetrics(): AggregatedMetrics
    }

    %% Output Generation
    class OutputManager {
        -dashboardGenerator: DashboardGenerator
        -documentGenerator: DocumentGenerator
        -visualizationGenerator: VisualizationGenerator
        +generateOutputs(results: AnalysisResult): OutputPackage
        -validateOutputs(): ValidationResult
    }

    class DashboardGenerator {
        -templateManager: TemplateManager
        -chartGenerator: ChartGenerator
        -mermaidGenerator: MermaidGenerator
        +generateDashboard(data: DashboardData): Dashboard
        +updateDashboard(updates: Updates): void
        -validateLayout(): boolean
    }

    class DocumentGenerator {
        -templateEngine: TemplateEngine
        -markdownConverter: MarkdownConverter
        -pdfGenerator: PDFGenerator
        +generateDocument(data: DocumentData): Document
        +exportDocument(format: Format): void
        -validateContent(): boolean
    }

    %% Visualization Components
    class ChartGenerator {
        -chartTypes: Map~string, ChartType~
        -dataFormatter: DataFormatter
        +generateChart(data: ChartData): Chart
        +updateChart(updates: Updates): void
        -validateData(): boolean
    }

    class MermaidGenerator {
        -diagramTypes: Map~string, DiagramType~
        -styleManager: StyleManager
        +generateDiagram(data: DiagramData): Diagram
        +updateDiagram(updates: Updates): void
        -validateDiagram(): boolean
    }

    %% Report Components
    class ReportComponent {
        -type: ComponentType
        -data: ComponentData
        -layout: LayoutConfig
        +render(): RenderedComponent
        +update(updates: Updates): void
        -validate(): boolean
    }

    class MetricsComponent {
        -metrics: MetricsData
        -thresholds: ThresholdConfig
        +renderMetrics(): RenderedMetrics
        +updateMetrics(updates: Updates): void
        -validateMetrics(): boolean
    }

    class SecurityComponent {
        -vulnerabilities: VulnerabilityData
        -riskLevels: RiskConfig
        +renderSecurity(): RenderedSecurity
        +updateSecurity(updates: Updates): void
        -validateSecurity(): boolean
    }

    %% Relationships
    AnalysisManager --> SummaryAnalyzer
    OutputManager --> DashboardGenerator
    OutputManager --> DocumentGenerator
    DashboardGenerator --> ChartGenerator
    DashboardGenerator --> MermaidGenerator
    ReportComponent <|-- MetricsComponent
    ReportComponent <|-- SecurityComponent
    DashboardGenerator ..> ReportComponent