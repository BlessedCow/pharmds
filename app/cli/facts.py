from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from core.constants import normalize_pd_effect_id, normalize_transporter_id
from core.models import (
    AbsorptionRole,
    Drug,
    EnzymeRole,
    Facts,
    PDEffect,
    TransporterRole,
)


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def load_facts(
    conn: sqlite3.Connection,
    drug_ids: list[str],
    patient_flags: dict[str, bool],
) -> Facts:
    facts = Facts(patient_flags=patient_flags)

    for drug_id in drug_ids:
        row = conn.execute("SELECT * FROM drug WHERE id=?", (drug_id,)).fetchone()
        facts.drugs[drug_id] = Drug(
            id=row["id"],
            generic_name=row["generic_name"],
            drug_class=row["drug_class"],
            therapeutic_index=row["therapeutic_index"],
            notes=row["notes"],
        )

    rows = conn.execute(
        """
        SELECT * FROM drug_enzyme_role
        WHERE drug_id IN ({})
        """.format(",".join("?" * len(drug_ids))),
        tuple(drug_ids),
    ).fetchall()
    for row in rows:
        facts.enzyme_roles.setdefault(row["drug_id"], []).append(
            EnzymeRole(
                enzyme_id=row["enzyme_id"],
                role=row["role"],
                strength=row["strength"],
                fraction_metabolized=row["fraction_metabolized"],
                notes=row["notes"],
            )
        )

    rows = conn.execute(
        """
        SELECT * FROM drug_transporter_role
        WHERE drug_id IN ({})
        """.format(",".join("?" * len(drug_ids))),
        tuple(drug_ids),
    ).fetchall()
    for row in rows:
        facts.transporter_roles.setdefault(row["drug_id"], []).append(
            TransporterRole(
                transporter_id=normalize_transporter_id(row["transporter_id"]),
                role=row["role"],
                strength=row["strength"],
                notes=row["notes"],
            )
        )

    rows = conn.execute(
        """
        SELECT * FROM drug_pd_effect
        WHERE drug_id IN ({})
        """.format(",".join("?" * len(drug_ids))),
        tuple(drug_ids),
    ).fetchall()
    for row in rows:
        facts.pd_effects.setdefault(row["drug_id"], []).append(
            PDEffect(
                effect_id=normalize_pd_effect_id(row["pd_effect_id"]),
                direction=row["direction"],
                magnitude=row["magnitude"],
                mechanism_note=row["mechanism_note"],
            )
        )

    _load_absorption_roles(facts, drug_ids)
    return facts


def _load_absorption_roles(facts: Facts, drug_ids: list[str]) -> None:
    path = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "curation"
        / "absorption_roles.json"
    )
    content = json.loads(path.read_text(encoding="utf-8"))
    selected = set(drug_ids)
    for entry in content["roles"]:
        drug_id: str = entry["drug_id"]
        if drug_id not in selected:
            continue
        role = AbsorptionRole(
            mechanism=entry["mechanism"],
            target=entry["target"],
            evidence_refs=tuple(entry.get("evidence_refs", [])),
        )
        facts.absorption_roles.setdefault(drug_id, []).append(role)
