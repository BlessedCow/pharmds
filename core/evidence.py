# citations + confidence representation

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Reference:
    source: str  # e.g. "FDA label", "Guideline"
    citation: str  # short human string
    url: str | None = None


# In v0, references live inside rule JSON as {source,citation,url}
# and are passed through unchanged.
