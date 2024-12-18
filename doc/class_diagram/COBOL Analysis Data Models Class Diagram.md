classDiagram
    %% Core Data Models
    class COBOLProgram {
        +identification: IdentificationDivision
        +environment: EnvironmentDivision
        +data: DataDivision
        +procedure: ProcedureDivision
        +getProgramName(): str
        +getDivisions(): List~Division~
    }

    class Division {
        <<abstract>>
        #name: str
        #content: str
        +getName(): str
        +validate(): bool
    }

    class IdentificationDivision {
        +programId: str
        +author: str
        +installment: str
        +dateWritten: datetime
        +validateProgramId(): bool
    }

    class EnvironmentDivision {
        +sourceComputer: SourceComputer
        +objectComputer: ObjectComputer
        +specialNames: List~SpecialName~
        +validateEnvironment(): bool
    }

    class DataDivision {
        +fileSection: FileSection
        +workingStorage: WorkingStorageSection
        +linkageSection: LinkageSection
        +validateData(): bool
    }

    class ProcedureDivision {
        +sections: List~Section~
        +statements: List~Statement~
        +validateProcedure(): bool
    }

    %% Data Items and Structures
    class DataItem {
        +level: int
        +name: str
        +picture: str
        +usage: str
        +value: str
        +isGroup(): bool
        +validateFormat(): bool
    }

    class Section {
        +name: str
        +paragraphs: List~Paragraph~
        +statements: List~Statement~
        +validateSection(): bool
    }

    class Statement {
        +type: StatementType
        +operands: List~Operand~
        +validateSyntax(): bool
    }

    %% Analysis Results
    class AnalysisResult {
        +id: UUID
        +timestamp: datetime
        +metrics: Dict~str, float~
        +issues: List~Issue~
        +addMetric(name: str, value: float)
        +addIssue(issue: Issue)
    }

    class Issue {
        +type: IssueType
        +severity: Severity
        +location: Location
        +message: str
        +recommendation: str
    }

    %% Relationships
    COBOLProgram *-- Division
    Division <|-- IdentificationDivision
    Division <|-- EnvironmentDivision
    Division <|-- DataDivision
    Division <|-- ProcedureDivision
    DataDivision *-- DataItem
    ProcedureDivision *-- Section
    Section *-- Statement
    AnalysisResult *-- Issue