from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.cli import DB_PATH, connect, load_facts, resolve_drug_ids
from core.mechanisms.pipeline import MechanismPipelineResult, run_mechanism_pipeline
from core.mechanisms.pipeline_json import mechanism_pipeline_to_json_dict
from core.models import Facts


def load_drug_facts(
    drug_names: Sequence[str],
    *,
    patient_flags: dict[str, bool] | None = None,
) -> tuple[list[str], Facts]:
    """Resolve drugs and load curated facts with a closed database connection."""
    conn = connect(DB_PATH)
    try:
        drug_ids = resolve_drug_ids(conn, list(drug_names))
        facts = load_facts(conn, drug_ids, patient_flags=patient_flags or {})
    finally:
        conn.close()
    return drug_ids, facts


def pipeline_for(
    drug_names: Sequence[str],
    *,
    patient_flags: dict[str, bool] | None = None,
) -> MechanismPipelineResult:
    """Build a mechanism pipeline from independently loaded curated facts."""
    drug_ids, facts = load_drug_facts(drug_names, patient_flags=patient_flags)
    return run_mechanism_pipeline(drug_ids, facts)


def pipeline_payload_for(
    drug_names: Sequence[str],
    *,
    patient_flags: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Serialize a pipeline constructed from curated drug facts."""
    return mechanism_pipeline_to_json_dict(
        pipeline_for(drug_names, patient_flags=patient_flags)
    )
