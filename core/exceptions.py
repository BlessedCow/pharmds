from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple


class PharmDSError(Exception):
    """Base exception for project-level, domain-specific errors."""


@dataclass(frozen=True)
class UnknownDrugError(PharmDSError):
    """
    Raised when one or more drug tokens cannot be resolved.

    unknown: the raw tokens the user provided that were not resolved
    suggestions: mapping from unknown token -> tuple of suggested known names/aliases
    """

    unknown: Tuple[str, ...]
    suggestions: Dict[str, Tuple[str, ...]]

    def __init__(
        self,
        unknown: Iterable[str],
        suggestions: Dict[str, Iterable[str]] | None = None,
    ):
        object.__setattr__(self, "unknown", tuple(unknown))
        sug: Dict[str, Tuple[str, ...]] = {}
        if suggestions:
            for k, vals in suggestions.items():
                sug[str(k)] = tuple(vals)
        object.__setattr__(self, "suggestions", sug)

    def __str__(self) -> str:
        if not self.unknown:
            return "Unknown drug"

        if len(self.unknown) == 1:
            tok = self.unknown[0]
            base = f"Drug not found: {tok}"
            opts = self.suggestions.get(tok, ())
            if opts:
                return base + f". Did you mean: {', '.join(opts)}?"
            return base

        joined = ", ".join(self.unknown)
        return f"Drugs not found: {joined}"
