import os
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter
from fastapi.params import Depends

from app.api.chat import bm25_retriever
from app.api.dependencies import get_current_tenant
from app.chunking.header_chunker import HeaderChunker
from app.embeddings.local_embedding import LocalEmbedding
from app.parsers.docling_parser import DoclingParser
from app.retrieval.bm25_retriever import BM25Retriever
from app.services.ingestion_service import IngestionService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("documents")

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

embedding_service = LocalEmbedding()
vectorstore = ChromeVectorStore()
bm25_retriever = BM25Retriever()

ingestion_service = IngestionService(
    parser=DoclingParser(),
    chunker=HeaderChunker(),
    embedding_service=embedding_service,
    vectorstore=vectorstore,
    bm25_retriever=bm25_retriever,
)

@router.post("/upload")
def upload_document(
        file:UploadFile = File(...),
        tenant_id: str = Depends(get_current_tenant),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    file_path = UPLOAD_DIR.joinpath(file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = ingestion_service.ingest(
            str(file_path),
            tenant_id=tenant_id,
        )

        return result

    except Exception as e:

        if file_path.exists():
            os.remove(file_path)

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    finally:
        file.file.close()

@router.get("")
def list_documents():
    return vectorstore.list_documents()

@router.delete("/{document_id}")
def delete_document(document_id: str):

    deleted_count = vectorstore.delete_documents(document_id)

    if deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "document_id": document_id,
        "deleted_chunks": deleted_count,
        "status": "deleted",
    }