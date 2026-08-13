from dataclasses import dataclass
from typing import Any

@dataclass
class Source:
    document: str
    score: float
    metadata: dict[str, Any]

@dataclass
class RagResponse:
    answer: str
    sources: list[Source]