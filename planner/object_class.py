from dataclasses import dataclass
from typing import Optional, Set

@dataclass(eq=True, frozen=True)
class AVU:
    attribute: str
    value: str
    unit: Optional[str] = None

    def __post_init__(self):
        object.__setattr__(self, 'attribute', str(self.attribute))
        object.__setattr__(self, 'value', str(self.value))
        if self.unit is not None:
            object.__setattr__(self, 'unit', str(self.unit))

@dataclass
class Plan:
    path: str
    is_collection: bool
    metadata: Set[AVU]
