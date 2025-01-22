from dataclasses import dataclass, field
from typing import Any, Protocol, Optional


class MonteCarloResult(Protocol):
    def add(self, other: "MonteCarloResult") -> "MonteCarloResult": ...


@dataclass
class MonteCarloJob:
    args: dict[str, Any] = field(default_factory=dict)
    finished_shots: int = 0
    pending_shots: int = 0
    result: Optional[MonteCarloResult] = None

    @property
    def expecting_shots(self) -> int:
        return self.pending_shots + self.finished_shots

    @property
    def shots(self) -> int:
        return self.finished_shots
