from datetime import datetime, timezone
from google.cloud import bigquery

class BigQueryChunkStorage:
    def __init__(
            self,
            project_id: str,
            dataset_id: str,
            document_table: str = "documents",
            chunk_table: str = "chunks",
    ):
        if not project_id:
            raise ValueError(
                "GCP project ID is required"
            )

        self.client = bigquery.Client(
            project=project_id,
        )
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.document_table = document_table
        self.chunk_table = chunk_table

    @property
    def documents_table_ref(self) -> str:
        return (
            f"{self.project_id}.{self.dataset_id}.{self.document_table}"
        )

    @property
    def chunk_table_ref(self) -> str:
        return (
            f"{self.project_id}.{self.dataset_id}.{self.chunk_table}"
        )

    def insert_document(
            self,
            document_id: str,
            tenant_id: str,
            filename: str,
            content_hash: str,
            gcs_url: str,
            mime_type: str | None = None,
            chunk_count: int = 0,
    ):
        row = {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "filename": filename,
            "content_hash": content_hash,
            "gcs_url": gcs_url,
            "mime_type": mime_type,
            "chunk_count": chunk_count,
            "status": "INDEXED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        errors = (
            self.client.insert_rows_json(
                self.documents_table_ref,[row]
            )
        )

        if errors:
            raise RuntimeError(
                f"BigQuery document insert failed:\n{errors}",
            )

    def insert_chunks(
            self,
            chunks: list,
    ):
        if not chunks:
            return
        rows = []
        created_at = datetime.now(timezone.utc).isoformat()

        for chunk in chunks:
            metadata = (
                chunk.metadata or {}
            )

            rows.append(
                {
                    "tenant_id": metadata.get("tenant_id"),
                    "document_id": metadata.get("document_id"),
                    "chunk_id": chunk.id,
                    "chunk_index": metadata.get("chunk_index"),
                    "heading": metadata.get("heading"),
                    "text": chunk.text,
                    "content_hash": metadata.get("content_hash"),
                    "filename": metadata.get("filename"),
                    "created_at": created_at,
                }
            )

        errors = (
            self.client.insert_rows_json(
                self.chunk_table_ref, rows
            )
        )

        if errors:
            raise RuntimeError(
                f"BigQuery chunk insert failed:\n{errors}",
            )
