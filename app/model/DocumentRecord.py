from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DocumentRecord:
    document_id: str
    filename: str
    content_hash: str
    created_at: datetime
    chunk_count: int