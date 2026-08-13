from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class ParsedDocument:
    filename: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)