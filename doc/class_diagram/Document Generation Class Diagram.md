classDiagram
    %% Document Generation Core
    class DocumentController {
        -contentAssembler: ContentAssembler
        -visualizationManager: VisualizationManager
        -formatManager: FormatManager
        -qualityController: QualityController
        +generateDocument(analysisResult: AnalysisResult): Document
        +validateDocument(document: Document): ValidationResult
    }

    class ContentAssembler {
        -collector: ContentCollector
        -templateSelector: TemplateSelector
        -formatter: ContentFormatter
        +assembleContent(data: AnalysisData): AssembledContent
        -validateContentStructure(): boolean
    }

    class VisualizationManager {
        -mermaidGenerator: MermaidGenerator
        -chartGenerator: ChartGenerator
        -metricsVisualizer: MetricsVisualizer
        +generateVisualizations(data: AnalysisData): List~Visualization~
        -optimizeVisualizations(): void
    }

    %% Visualization Components
    class MermaidGenerator {
        -templateEngine: TemplateEngine
        -styleConfig: StyleConfig
        +generateFlowchart(data: FlowData): string
        +generateSequenceDiagram(data: SequenceData): string
        -validateMermaidSyntax(diagram: string): boolean
    }

    class ChartGenerator {
        -chartConfig: ChartConfig
        -dataTransformer: DataTransformer
        +generateChart(data: ChartData): Chart
        +customizeChartStyle(style: ChartStyle): void
    }

    class MetricsVisualizer {
        -metricConfig: MetricConfig
        -visualizationRules: VisualizationRules
        +visualizeMetrics(metrics: Metrics): Visualization
        -selectVisualizationType(metric: Metric): VisualizationType
    }

    %% Content Enhancement
    class RAGEnhancer {
        -textEnhancer: TextEnhancer
        -descriptionGenerator: DescriptionGenerator
        -insightGenerator: InsightGenerator
        +enhanceContent(content: Content): EnhancedContent
        -validateEnhancements(): ValidationResult
    }

    class TextEnhancer {
        -llmModel: LLMModel
        -enhancementRules: EnhancementRules
        +enhanceText(text: string): string
        -applyEnhancementRules(): void
    }

    %% Document Formatting
    class FormatManager {
        -pdfGenerator: PDFGenerator
        -styleApplicator: StyleApplicator
        -tocGenerator: TOCGenerator
        +formatDocument(content: Content): FormattedDocument
        -validateFormatting(): boolean
    }

    class PDFGenerator {
        -pdfConfig: PDFConfig
        -layoutManager: LayoutManager
        +generatePDF(document: Document): PDF
        -applyPDFStyles(): void
    }

    %% Quality Control
    class QualityController {
        -structureValidator: StructureValidator
        -contentValidator: ContentValidator
        -formatValidator: FormatValidator
        +validateDocument(document: Document): ValidationResult
        -generateQualityReport(): QualityReport
    }

    class DocumentValidator {
        -validationRules: ValidationRules
        -qualityChecker: QualityChecker
        +validate(document: Document): ValidationResult
        -checkConsistency(): boolean
    }

    %% Relationships
    DocumentController *-- ContentAssembler
    DocumentController *-- VisualizationManager
    DocumentController *-- FormatManager
    DocumentController *-- QualityController

    VisualizationManager *-- MermaidGenerator
    VisualizationManager *-- ChartGenerator
    VisualizationManager *-- MetricsVisualizer

    ContentAssembler --> RAGEnhancer
    RAGEnhancer *-- TextEnhancer

    FormatManager *-- PDFGenerator
    QualityController *-- DocumentValidator

    %% Dependencies
    ContentAssembler ..> VisualizationManager: uses
    RAGEnhancer ..> ContentAssembler: enhances
    DocumentValidator ..> FormatManager: validates