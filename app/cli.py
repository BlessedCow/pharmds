from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple

from core.models import Drug, EnzymeRole, TransporterRole, PDEffect, Facts
from rules.engine import load_rules, evaluate_all
from reasoning.combine import build_pair_reports
from reasoning.explain import render_explanation, render_rationale
# from core.models import PairReport

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
RULE_DIR = BASE_DIR / "rules" / "rule_defs"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def resolve_drug_ids(conn: sqlite3.Connection, names: List[str]) -> List[str]:
    out: List[str] = []
    for raw in names:
        q = raw.strip().lower()
        row = conn.execute("SELECT id FROM drug WHERE lower(generic_name)=?", (q,)).fetchone()
        if row:
            out.append(row["id"])
            continue
        row = conn.execute("SELECT drug_id FROM drug_alias WHERE alias=?", (q,)).fetchone()
        if row:
            out.append(row["drug_id"])
            continue
        raise SystemExit(f"Unknown drug: {raw}")
    return out


def load_facts(conn: sqlite3.Connection, drug_ids: List[str], patient_flags: Dict[str, bool]) -> Facts:
    facts = Facts(patient_flags=patient_flags)

    # Drugs
    for did in drug_ids:
        r = conn.execute("SELECT * FROM drug WHERE id=?", (did,)).fetchone()
        facts.drugs[did] = Drug(
            id=r["id"],
            generic_name=r["generic_name"],
            drug_class=r["drug_class"],
            therapeutic_index=r["therapeutic_index"],
            notes=r["notes"],
        )

    # Enzyme roles
    rows = conn.execute(
        """
        SELECT * FROM drug_enzyme_role
        WHERE drug_id IN ({})
        """.format(",".join("?" * len(drug_ids))),
        tuple(drug_ids),
    ).fetchall()
    for r in rows:
        facts.enzyme_roles.setdefault(r["drug_id"], []).append(
            EnzymeRole(
                enzyme_id=r["enzyme_id"],
                role=r["role"],
                strength=r["strength"],
                fraction_metabolized=r["fraction_metabolized"],
                notes=r["notes"],
            )
        )

    # Transporter roles
    rows = conn.execute(
        """
        SELECT * FROM drug_transporter_role
        WHERE drug_id IN ({})
        """.format(",".join("?" * len(drug_ids))),
        tuple(drug_ids),
    ).fetchall()
    for r in rows:
        facts.transporter_roles.setdefault(r["drug_id"], []).append(
            TransporterRole(
                transporter_id=r["transporter_id"],
                role=r["role"],
                strength=r["strength"],
                notes=r["notes"],
            )
        )

    # PD effects
    rows = conn.execute(
        """
        SELECT * FROM drug_pd_effect
        WHERE drug_id IN ({})
        """.format(",".join("?" * len(drug_ids))),
        tuple(drug_ids),
    ).fetchall()
    for r in rows:
        facts.pd_effects.setdefault(r["drug_id"], []).append(
            PDEffect(
                effect_id=r["pd_effect_id"],
                direction=r["direction"],
                magnitude=r["magnitude"],
                mechanism_note=r["mechanism_note"],
            )
        )

    return facts


def main() -> None:
    p = argparse.ArgumentParser(description="Educational PK/PD interaction reasoner (rule-based).")
    p.add_argument("drugs", nargs="+", help="Drug names (generic or alias). Example: warfarin fluconazole")
    p.add_argument("--qt-risk", action="store_true", help="Patient has QT risk factors (educational flag).")
    p.add_argument("--bleeding-risk", action="store_true", help="Patient has bleeding risk factors (educational flag).")
    args = p.parse_args()

    conn = connect(DB_PATH)
    drug_ids = resolve_drug_ids(conn, args.drugs)

    patient_flags = {
        "qt_risk": bool(args.qt_risk),
        "bleeding_risk": bool(args.bleeding_risk),
    }
    facts = load_facts(conn, drug_ids, patient_flags)

    rules = load_rules(RULE_DIR)
    hits = evaluate_all(rules, facts, drug_ids)

    templates = {r.id: r.explanation_template for r in rules}
    reports = build_pair_reports(facts, hits, templates)
    # findings = [r for r in reports if r.overall_severity == Severity.EDUCATIONAL]

    if not reports:
        print("No rule-based interactions detected for this set (educational scope).")
        return

    print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")
    for rep in reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name

        print("=" * 80)
        print(f"{d1} + {d2}")
        print(f"Overall: severity={rep.overall_severity.value} | class={rep.overall_rule_class.value}")
        print()
        
        if rep.pk_hits:
            print("PK section (directional):")
            for h in rep.pk_hits:
                A = facts.drugs[h.inputs["A"]].generic_name
                B = facts.drugs[h.inputs["B"]].generic_name
                print(f"- [{h.severity.value} | {h.rule_class.value}] {h.name}")
                print(f"  Affected: {A} | Interacting: {B}")
                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    print(f"  Explanation: {render_explanation(tmpl, facts, h)}")
                rat = render_rationale(facts, h)
                if rat:
                    print("  Rationale:")
                    for line in rat.splitlines():
                        print(f"   {line}")
                if h.actions:
                    print("  Suggested actions:")
                    for a in h.actions:
                        print(f"   - {a}")
                print()

        if rep.pd_hits:
            print("PD section (shared domain):")
            for h in rep.pd_hits:
                A = facts.drugs[h.inputs["A"]].generic_name
                B = facts.drugs[h.inputs["B"]].generic_name
                print(f"- [{h.severity.value} | {h.rule_class.value}] {h.name}")
                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    print(f"  Explanation: {render_explanation(tmpl, facts, h)}")
                rat = render_rationale(facts, h)
                if rat:
                    print("  Rationale:")
                    for line in rat.splitlines():
                        print(f"   {line}")
                if h.actions:
                    print("  Suggested actions:")
                    for a in h.actions:
                        print(f"   - {a}")
                print()

        # References (unique)
        refs = []
        for h in (rep.pk_hits + rep.pd_hits):
            refs.extend(h.references)
        uniq = {(r.get("source",""), r.get("citation",""), r.get("url","")) for r in refs}
        if uniq:
            print("References (rule-level):")
            for source, citation, url in sorted(uniq):
                if url:
                    print(f"- {source}: {citation} ({url})")
                else:
                    print(f"- {source}: {citation}")
        print()

    print("=" * 80)
    print("Footer: This output is an educational mechanistic explanation. Verify with primary sources.\n")
    
if __name__ == "__main__":
    main()