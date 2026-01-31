from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


class PharmDSError(Exception):
    """Base exception for project-level, domain-specific errors."""


@dataclass(frozen=True)
class UnknownDrugError(PharmDSError):
    """Raised when one or more drug names cannot be resolved to known drug IDs."""

    unknown: Tuple[str, ...]

    def __init__(self, unknown: Iterable[str]):
        object.__setattr__(self, "unknown", tuple(unknown))

    def __str__(self) -> str:
        if not self.unknown:
            return "Unknown drug"
        if len(self.unknown) == 1:
            return f"Unknown drug: {self.unknown[0]}"
        joined = ", ".join(self.unknown)
        return f"Unknown drugs: {joined}"
