from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class DocumentChunk:
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: List[float] | None = None