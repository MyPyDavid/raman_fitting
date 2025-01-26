from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class ExportResult:
    target: Path | None = None
    message: str | None = None


@dataclass
class ExportResultSet:
    results: List[ExportResult] | List = field(default_factory=list)

    def __add__(self, other: "ExportResultSet") -> "ExportResultSet":
        if isinstance(other, ExportResult):
            self.results.append(other)

        if hasattr(other, "results"):
            self.results += other.results
        return self
