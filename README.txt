RAG Agent - Project README

1. Project Overview

This project is a Retrieval-Augmented Generation (RAG) application that
allows customers to upload documents and ask questions about their
content.

The system uses:

-   Docling for document parsing
-   Header-based chunking
-   Local sentence-transformer embeddings
-   ChromaDB for vector search
-   BM25 for keyword search
-   Reciprocal Rank Fusion (RRF) for hybrid retrieval
-   Ollama for local LLM generation
-   FastAPI for the REST API
-   Tenant-aware retrieval for multi-customer document isolation

The current architecture is designed so that document ingestion and
question answering are separate flows.

------------------------------------------------------------------------

2. High-Level Architecture

There are two major flows.

Document Ingestion Flow

    Customer uploads document
            |
            v
    IngestionService
            |
            v
    DoclingParser
            |
            v
    ParsedDocument
            |
            v
    HeaderChunker
            |
            v
    DocumentChunk[]
            |
            v
    LocalEmbedding
            |
       +----+----+
       |         |
       v         v
    Chroma     BM25
       |         |
       +----+----+
            |
       Persistent indexes

Question / Chat Flow

    Customer question
            |
            v
         chat.py
            |
            v
       RagService
            |
            v
    RetrievalService
            |
            v
    HybridRetriever
        |          |
        v          v
     Chroma       BM25
        |          |
        +----+-----+
             |
             v
            RRF
             |
             v
       Relevant chunks
             |
             v
       PromptBuilder
             |
             v
         OllamaLLM
             |
             v
           Answer

A reranker is planned as the next retrieval improvement:

    Hybrid Retrieval
          |
          v
         RRF
          |
          v
    Reranker
          |
          v
      Top chunks
          |
          v
    PromptBuilder
          |
          v
       Ollama

------------------------------------------------------------------------

3. Project Structure

    rag-agent/
    |
    +-- app/
    |   |
    |   +-- api/
    |   |   +-- chat.py
    |   |
    |   +-- model/
    |   |   +-- document.py
    |   |   +-- chunk.py
    |   |
    |   +-- parsers/
    |   |   +-- docling_parser.py
    |   |
    |   +-- chunking/
    |   |   +-- header_chunker.py
    |   |
    |   +-- embeddings/
    |   |   +-- base_embedding.py
    |   |   +-- local_embedding.py
    |   |
    |   +-- vectorstore/
    |   |   +-- base_vectorstore.py
    |   |   +-- chroma_vectorstore.py
    |   |
    |   +-- retrieval/
    |   |   +-- bm25_retriever.py
    |   |   +-- hybrid_retriever.py
    |   |
    |   +-- services/
    |   |   +-- ingestion_service.py
    |   |   +-- retrieval_service.py
    |   |   +-- rag_service.py
    |   |
    |   +-- prompts/
    |   |   +-- prompt_builder.py
    |   |
    |   +-- llm/
    |       +-- ollama_llm.py
    |
    +-- data/
    |   +-- bm25/
    |
    +-- tests / test_*.py
    |
    +-- README.txt

------------------------------------------------------------------------

4. Responsibility of Each Class

chat.py

The FastAPI API layer.

Responsibilities:

-   Receive HTTP requests
-   Extract the question
-   Obtain the current tenant
-   Call RagService
-   Return the response

Example:

    @router.post("")
    def chat(
        request: ChatRequest,
        tenant_id: str = Depends(get_current_tenant)
    ):
        return rag_service.ask(
            question=request.question,
            tenant_id=tenant_id,
        )

The customer does not need to provide tenant_id manually.

------------------------------------------------------------------------

IngestionService

The main orchestrator for document ingestion.

Responsibilities:

1.  Generate document_id
2.  Calculate content_hash
3.  Parse the document
4.  Add document metadata
5.  Create chunks
6.  Assign deterministic chunk IDs
7.  Generate embeddings
8.  Store chunks in Chroma
9.  Add chunks to BM25

Document identity is generated here.

Example:

    document_id = str(uuid.uuid4())

Chunk IDs are based on:

    document_id:chunk_index

Example:

    7697ac3f-0c1f-495f-8677-ba0552f70a38:0
    7697ac3f-0c1f-495f-8677-ba0552f70a38:1
    7697ac3f-0c1f-495f-8677-ba0552f70a38:2

This allows Chroma and BM25 to use the same chunk identity.

------------------------------------------------------------------------

DoclingParser

Responsible only for parsing documents.

Input:

    PDF / DOCX / other supported document

Output:

    ParsedDocument

It should not be responsible for:

-   embeddings
-   vector storage
-   BM25
-   LLM calls

Conceptually:

    Document -> ParsedDocument

------------------------------------------------------------------------

ParsedDocument

A data model representing a parsed document.

Typical information:

    filename
    content
    metadata

Metadata can contain:

    document_id
    tenant_id
    content_hash
    parser information
    extension

------------------------------------------------------------------------

HeaderChunker

Splits the parsed document into smaller searchable sections.

Current approach:

-   Uses Markdown headers
-   Creates chunks around headings

Example:

    Profile Summary
    Technical Skills
    Professional Experience
    Senior Data Engineer

Output:

    DocumentChunk[]

The final deterministic chunk ID is assigned by IngestionService.

------------------------------------------------------------------------

DocumentChunk

Represents one searchable section of a document.

Typical fields:

    id
    text
    metadata
    embedding

Example metadata:

    {
        "document_id": "...",
        "tenant_id": "tenant_001",
        "filename": "Sandeep_resume.pdf",
        "chunk_index": 1,
        "content_hash": "...",
        "extension": ".pdf",
        "parsers": "docling"
    }

------------------------------------------------------------------------

LocalEmbedding

Generates embeddings locally.

The project uses a local sentence-transformer embedding model instead of
the OpenAI embedding API.

This avoids OpenAI API credit usage for embeddings.

The current embedding size is:

    384 dimensions

Conceptually:

    text -> 384-dimensional vector

------------------------------------------------------------------------

ChromaVectorStore

Responsible for vector storage and semantic similarity search.

Responsibilities:

-   Add chunks and embeddings
-   Query by embedding
-   Apply tenant filtering
-   Optionally apply document filtering
-   Return relevant chunks and vector similarity information

Chroma is used for semantic retrieval.

------------------------------------------------------------------------

BM25Retriever

Responsible for lexical / keyword retrieval.

BM25 is useful when exact words matter.

Example question:

    How many years of experience?

BM25 can strongly match terms such as:

    years
    experience

The BM25 index is persisted locally.

Example:

    data/bm25/tenant_001.pkl

When the application starts, the BM25 index can be loaded from disk.

This means BM25 does not need to be rebuilt every time the application
starts.

------------------------------------------------------------------------

HybridRetriever

Combines multiple retrieval strategies.

Current strategies:

    Chroma vector search
    +
    BM25 keyword search

The results are combined using Reciprocal Rank Fusion (RRF).

Conceptually:

    Question
       |
       +----> Chroma
       |
       +----> BM25
              |
              v
             RRF
              |
              v
        Hybrid results

A result can contain:

    chunk
    vector_score
    vector_rank
    bm25_score
    bm25_rank
    hybrid_score

------------------------------------------------------------------------

RetrievalService

Provides a clean retrieval abstraction for the rest of the application.

Current responsibility:

    Question
       |
       v
    HybridRetriever
       |
       v
    Retrieved results

RagService does not need to know whether retrieval is implemented using:

-   Chroma
-   BM25
-   RRF
-   future reranking

This keeps retrieval implementation separate from answer generation.

------------------------------------------------------------------------

PromptBuilder

Builds the prompt sent to the LLM.

It combines:

    Question
    +
    Retrieved document chunks

Conceptually:

    Context:
    ----------------
    relevant chunk 1
    relevant chunk 2
    relevant chunk 3
    ----------------

    Question:
    How many years of experience?

The PromptBuilder should work with DocumentChunk objects rather than
knowing about HybridRetriever’s result dictionaries.

RagService extracts:

    result["chunk"]

before passing chunks to PromptBuilder.

------------------------------------------------------------------------

OllamaLLM

Provides the LLM interface.

The application currently uses Ollama so that answer generation can
happen locally.

Conceptually:

    prompt -> Ollama -> answer

It should not know anything about:

-   document parsing
-   chunking
-   Chroma
-   BM25
-   tenant filtering

------------------------------------------------------------------------

RagService

The main question-answering orchestrator.

Responsibilities:

1.  Receive question and tenant_id
2.  Ask RetrievalService for relevant results
3.  Extract DocumentChunk objects
4.  Build prompt
5.  Call OllamaLLM
6.  Build the API response
7.  Group/deduplicate source documents

Conceptually:

    question
       |
       v
    RetrievalService
       |
       v
    hybrid results
       |
       v
    DocumentChunk[]
       |
       v
    PromptBuilder
       |
       v
    OllamaLLM
       |
       v
    answer + sources

------------------------------------------------------------------------

5. Tenant Isolation

The system is designed for multiple customers/tenants.

The customer should not manually provide tenant_id in the chat request.

FastAPI obtains the tenant using:

    tenant_id: str = Depends(get_current_tenant)

Then:

    rag_service.ask(
        question=request.question,
        tenant_id=tenant_id,
    )

The tenant ID is used during retrieval to ensure that one tenant does
not retrieve another tenant’s documents.

Example metadata:

    tenant_id = "tenant_001"

Chroma retrieval uses tenant filtering.

------------------------------------------------------------------------

6. Document Identity

A document gets one document_id.

Example:

    document_id =
    7697ac3f-0c1f-495f-8677-ba0552f70a38

Each chunk gets a deterministic ID:

    document_id:chunk_index

Example:

    7697ac3f-0c1f-495f-8677-ba0552f70a38:0
    7697ac3f-0c1f-495f-8677-ba0552f70a38:1
    7697ac3f-0c1f-495f-8677-ba0552f70a38:2

This is important because the same chunk should have the same identity
in:

    Chroma
    BM25
    Retrieval results
    Source metadata

------------------------------------------------------------------------

7. Source Response

The LLM may use several chunks from the same document.

For example, retrieval may return:

    chunk 1
    chunk 2
    chunk 5
    chunk 7
    chunk 10

If all chunks belong to the same PDF, the API should not return the PDF
five times.

Sources should be grouped by document.

Preferred response structure:

    {
      "answer": "...",
      "sources": [
        {
          "document_id": "...",
          "filename": "Sandeep_resume.pdf",
          "chunks": [1, 2, 5, 7, 10]
        }
      ]
    }

This keeps the response clean while preserving the chunks used to
generate the answer.

------------------------------------------------------------------------

8. RAG Retrieval Strategy

The current retrieval architecture is hybrid retrieval.

Vector Search

Uses local embeddings and Chroma.

Good for:

-   semantic similarity
-   related concepts
-   different wording with similar meaning

BM25

Good for:

-   exact terms
-   names
-   keywords
-   numbers
-   phrases

RRF

Combines the rankings from both systems.

Example:

    Vector:
        chunk A -> rank 3
        chunk B -> rank 5

    BM25:
        chunk A -> rank 1
        chunk C -> rank 2

RRF combines these rankings to produce a hybrid ranking.

------------------------------------------------------------------------

9. Why We Separate Ingestion and Retrieval

This is very important.

Document ingestion should happen when a document is uploaded.

It should NOT happen every time a customer asks a question.

Incorrect

    /chat
       |
       +-- parse document
       +-- chunk document
       +-- create embeddings
       +-- add to Chroma
       +-- add to BM25
       +-- search
       +-- answer

Correct

    /upload
       |
       +-- parse
       +-- chunk
       +-- embed
       +-- index

    /chat
       |
       +-- search existing indexes
       +-- build context
       +-- answer

This prevents duplicate documents and unnecessary computation.

------------------------------------------------------------------------

10. Persistence

Chroma

Chroma stores vector data persistently.

BM25

The BM25 index is persisted locally.

Example:

    data/bm25/tenant_001.pkl

On application startup:

    BM25Retriever()
          |
          v
    Load tenant_001 index

This means the BM25 index survives application restarts.

------------------------------------------------------------------------

11. Testing Strategy

Tests should be separated by responsibility.

Examples:

    test_parser.py
    test_chunker.py
    test_embeddings.py
    test_vectorstore.py
    test_bm25_persistence.py
    test_hybrid.py
    test_retrieval.py
    test_rag_service.py

A retrieval test should NOT ingest the same document every time.

Avoid repeatedly calling:

    vectorstore.add_chunks(chunks)

inside retrieval-only tests.

Otherwise the vector store can contain duplicates such as:

    16 chunks
    32 chunks
    48 chunks
    64 chunks
    ...

The document should be indexed once, then queried many times.

------------------------------------------------------------------------

12. Current End-to-End Flow

Upload

    POST /documents
          |
          v
    IngestionService
          |
          +--> document_id
          +--> content_hash
          +--> tenant_id
          |
          v
    DoclingParser
          |
          v
    ParsedDocument
          |
          v
    HeaderChunker
          |
          v
    DocumentChunk[]
          |
          v
    LocalEmbedding
          |
          +------------+
          |            |
          v            v
       Chroma         BM25
          |            |
          +------------+
               |
          Indexed data

Chat

    POST /chat
          |
          v
    get_current_tenant()
          |
          v
    RagService
          |
          v
    RetrievalService
          |
          v
    HybridRetriever
       |         |
       v         v
    Chroma      BM25
       |         |
       +----+----+
            |
            v
           RRF
            |
            v
      Top retrieved chunks
            |
            v
       PromptBuilder
            |
            v
         OllamaLLM
            |
            v
       Answer + Sources

------------------------------------------------------------------------

13. Current Technology Stack

API

    FastAPI
    Uvicorn

Document Processing

    Docling

Embeddings

    Local Sentence Transformer
    384-dimensional embeddings

Vector Database

    ChromaDB

Keyword Retrieval

    BM25

Hybrid Retrieval

    Reciprocal Rank Fusion (RRF)

LLM

    Ollama

Language

    Python

------------------------------------------------------------------------

14. Planned Improvements

The next planned improvement is a local reranker.

Current:

    Chroma
       +
    BM25
       |
       v
      RRF
       |
       v
    Top chunks
       |
       v
    PromptBuilder
       |
       v
    Ollama

Planned:

    Chroma
       +
    BM25
       |
       v
      RRF
       |
       v
    Top candidate chunks
       |
       v
    Local Reranker
       |
       v
    Best chunks
       |
       v
    PromptBuilder
       |
       v
    Ollama

The reranker will evaluate the question together with each candidate
chunk and produce a more precise relevance score.

------------------------------------------------------------------------

15. Important Design Principles

1.  Keep document ingestion separate from question answering.
2.  Keep each class responsible for one main job.
3.  Keep tenant_id internal to the application/authentication layer.
4.  Do not make the customer provide document_id for normal chat.
5.  Use deterministic chunk IDs based on document_id and chunk_index.
6.  Store the same DocumentChunk identity in Chroma and BM25.
7.  Persist BM25 instead of rebuilding it for every process.
8.  Do not index documents during retrieval tests.
9.  Keep retrieval implementation separate from prompt generation.
10. Keep LLM implementation separate from retrieval.
11. Group duplicate source chunks by document in API responses.
12. Add new retrieval techniques such as reranking without changing the
    API layer.

------------------------------------------------------------------------

16. Mental Model

The easiest way to remember the architecture is:

    DOCUMENT SIDE
    =============

    Document
       |
       v
    Parse
       |
       v
    Chunk
       |
       v
    Embed
       |
       +------> Chroma
       |
       +------> BM25


    QUESTION SIDE
    =============

    Question
       |
       v
    Retrieve
       |
       v
    Hybrid Search
       |
       v
    RRF
       |
       v
    Rerank (planned)
       |
       v
    Context
       |
       v
    Prompt
       |
       v
    Ollama
       |
       v
    Answer

The document side builds the searchable knowledge base.

The question side searches that knowledge base and generates the answer.
