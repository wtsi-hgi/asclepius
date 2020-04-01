from dataclasses import dataclass
from typing import Optional, Set

@dataclass(eq=True, frozen=True)
class AVU:
    attribute: str
    value: str
    unit: Optional[str] = None

@dataclass
class Plan:
    path: str
    object_type: str
    metadata: Set[AVU]
