classDiagram
    %% RAG Core Components
    class RAGSystem {
        -config: RAGConfig
        -embedding_model: CustomEmbeddingModel
        -llm: Llama
        -vector_store: VectorStore
        +generate_response(query: str, context: Dict): str
        +add_to_knowledge_base(texts: List~str~): List~str~
    }

    class CustomEmbeddingModel {
        -model: SentenceTransformer
        -config: EmbeddingConfig
        -preprocessors: Dict
        +encode(texts: List~str~, content_type: ContentType): ndarray
        -combine_chunk_embeddings(embeddings: List): ndarray
    }

    class VectorStore {
        <<abstract>>
        +add_texts(texts: List~str~, metadatas: List~Dict~): List~str~
        +similarity_search(query: str, k: int): List~SearchResult~
    }

    %% Context Management
    class ContextManager {
        -max_context_length: int
        -context_store: Dict
        +add_context(session_id: str, context: Dict): void
        +get_context(session_id: str, query: str): List~Dict~
        -optimize_context(session_id: str): void
    }

    class SearchOptimizer {
        -embedding_model: CustomEmbeddingModel
        -cache: Dict
        +optimize_search(query: str, content_type: ContentType): List~SearchResult~
        -expand_query(query: str, contexts: List): str
    }

    %% Prompt Management
    class PromptTemplate {
        -templates: Dict
        +get_prompt(template_key: str, context: Dict): str
        -format_context(context: Dict): str
    }

    class PromptManager {
        -prompt_template: PromptTemplate
        -parameter_validators: Dict
        +generate_prompt(template_name: str, parameters: Dict): str
        -validate_parameters(params: Dict): Dict
    }

    %% Response Handling
    class ResponseHandler {
        <<abstract>>
        +process_response(response: str): ProcessedResponse
        +validate_response(response: Any): bool
    }

    class JSONResponseHandler {
        -schema: Dict
        +process_response(response: str): ProcessedResponse~Dict~
        -validate_against_schema(obj: Dict, schema: Dict): void
    }

    class MarkdownResponseHandler {
        -required_sections: List~str~
        +process_response(response: str): ProcessedResponse~str~
        -extract_sections(markdown_text: str): Dict
    }

    %% Relationships
    RAGSystem *-- CustomEmbeddingModel
    RAGSystem *-- VectorStore
    RAGSystem *-- ContextManager
    RAGSystem *-- PromptManager
    ContextManager -- SearchOptimizer
    PromptManager -- PromptTemplate
    ResponseHandler <|-- JSONResponseHandler
    ResponseHandler <|-- MarkdownResponseHandler