from __future__ import annotations

from typing import Any


def contributor_pd_submission(
    *,
    source_id: str = "source_dailymed_fluconazole_label",
    evidence_type: str = "drug_label",
    evidence_notes: str = "Contributor-submitted label evidence.",
    contributor_id: str = "project_maintainer",
    contributor_role: str = "maintainer",
    submitted_at: str = "2026-05-13",
) -> dict[str, Any]:
    """Build an independent contributor PD effect submission for validation tests."""
    return {
        "claim_type": "pd_effect",
        "subject": {"entity_type": "drug", "id": "fluconazole"},
        "predicate": "has_pd_effect",
        "object": {"effect_id": "QT_prolongation"},
        "evidence": [
            {
                "source_id": source_id,
                "evidence_type": evidence_type,
                "supports_claim": True,
                "confidence": "moderate",
                "notes": evidence_notes,
            }
        ],
        "contributor": {
            "id": contributor_id,
            "role": contributor_role,
            "submitted_at": submitted_at,
        },
        "review": {"status": "submitted"},
    }
