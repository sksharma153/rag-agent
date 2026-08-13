from dataclasses import dataclass, field
from typing import Optional, Any

@dataclass
class RetrievedChunk:
    id: str
    text: str
    score: float
    metadata: dict[str, Any]