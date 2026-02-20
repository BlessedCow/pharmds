from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
SCHEMA_PATH = BASE_DIR / "data" / "schema.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


def upsert(conn: sqlite3.Connection, sql: str, params: tuple) -> None:
    conn.execute(sql, params)


def seed(conn: sqlite3.Connection) -> None:
    # Enzymes
    enzymes = [
        ("CYP3A4", "CYP", "Major drug-metabolizing enzyme; many substrates."),
        ("CYP2C9", "CYP", "Important for warfarin and NSAIDs."),
        (
            "CYP2C19",
            "CYP",
            "Relevant for clopidogrel activation and some SSRIs/benzos.",
        ),
        (
            "CYP2D6",
            "CYP",
            "Relevant for codeine/tramadol activation, many antidepressants.",
        ),
        ("CYP1A2", "CYP", "Affected by inhibitors and smoking induction (later)."),
        ("CYP2B6", "CYP", "Primary pathway for bupropion metabolism (educational)."),
        (
            "UGT1A1",
            "UGT",
            "Phase II glucuronidation enzyme; clinically important for select substrates.",
        ),
        (
            "UGT2B7", 
            "UGT", 
            "Phase II glucuronidation enzyme; relevant for some opioids (educational)."
        ),
    ]
    for e in enzymes:
        upsert(
            conn,
            "INSERT OR REPLACE INTO enzyme(id,family,description) VALUES(?,?,?)",
            e,
        )

    # Transporters
    transporters = [
        (
            "P-gp",
            "P-glycoprotein (ABCB1); efflux transporter affecting absorption and elimination.",
        ),
        ("OATP1B1", "Hepatic uptake transporter (SLCO1B1)."),
        ("BCRP", "Breast Cancer Resistance Protein (ABCG2); efflux transporter."),
    ]
    for t in transporters:
        upsert(
            conn,
            "INSERT OR REPLACE INTO transporter(id,description) VALUES(?,?)",
            t,
        )

    # PD effects
    pd_effects = [
        ("QT_prolongation", "Potential to prolong QT interval / torsades risk domain."),
        ("CNS_depression", "Sedation/respiratory depression/falls risk domain."),
        ("serotonergic", "Serotonin excess/serotonin syndrome risk domain."),
        ("bleeding", "Bleeding risk domain."),
        ("anticholinergic", "Anticholinergic burden domain."),
        ("hypotension", "Orthostasis/hypotension domain."),
        ("bradycardia", "Heart rate lowering / symptomatic bradycardia risk domain."),
        (
            "serotonin_syndrome",
            "Serotonin toxicity syndrome risk domain (educational).",
        ),
        ("hypoglycemia", "Hypoglycemia risk domain."),
        ("anticholinergic", "Anticholinergic burden domain."),
        ("cardiovascular", "Cardiovascular effects (educational)."),
        ("CNS_stimulation", "CNS stimulation/agitation/insomnia risk domain."),
        ("hypertension", "Blood pressure elevation / hypertension risk domain."),
        ("tachycardia", "Heart rate elevation / tachycardia risk domain."),
        ("sympathetic_stimulation", "Sympathomimetic stimulation (BP/HR/agitation) risk domain."),
    ]
    for pe in pd_effects:
        upsert(conn, "INSERT OR REPLACE INTO pd_effect(id,description) VALUES(?,?)", pe)

    # Drug curation (source of truth)
    from core.constants import normalize_pd_effect_id, normalize_transporter_id
    from data.curation.validate import assert_valid_drugs_curation
    from data.loaders import load_drugs_curation

    assert_valid_drugs_curation()

    curation = load_drugs_curation()
    drugs = curation.get("drugs", [])

    for d in drugs:
        drug_id = d["id"]
        upsert(
            conn,
            "INSERT OR REPLACE INTO drug(id,generic_name,drug_class,therapeutic_index,notes) VALUES(?,?,?,?,?)",
            (
                drug_id,
                d["generic_name"],
                d.get("drug_class"),
                d["therapeutic_index"],
                d.get("notes"),
            ),
        )

        # Aliases
        for alias in d.get("aliases", []) or []:
            upsert(
                conn,
                "INSERT OR IGNORE INTO drug_alias(drug_id,alias) VALUES(?,?)",
                (drug_id, str(alias).strip().lower()),
            )

        # Enzyme roles
        for r in d.get("enzymes", []) or []:
            upsert(
                conn,
                "INSERT OR REPLACE INTO drug_enzyme_role(drug_id,enzyme_id,role,strength,fraction_metabolized,notes) VALUES(?,?,?,?,?,?)",
                (
                    drug_id,
                    r["enzyme_id"],
                    r["role"],
                    r.get("strength"),
                    r.get("fraction_metabolized"),
                    r.get("notes"),
                ),
            )

        # Transporter roles
        for r in d.get("transporters", []) or []:
            t_id = normalize_transporter_id(r["transporter_id"])
            upsert(
                conn,
                "INSERT OR REPLACE INTO drug_transporter_role(drug_id,transporter_id,role,strength,notes) VALUES(?,?,?,?,?)",
                (
                    drug_id,
                    t_id,
                    r["role"],
                    r.get("strength"),
                    r.get("notes"),
                ),
            )

        # PD effects
        for e in d.get("pd_effects", []) or []:
            pe_id = normalize_pd_effect_id(e["effect_id"])
            upsert(
                conn,
                "INSERT OR REPLACE INTO drug_pd_effect(drug_id,pd_effect_id,direction,magnitude,mechanism_note) VALUES(?,?,?,?,?)",
                (
                    drug_id,
                    pe_id,
                    e["direction"],
                    e["magnitude"],
                    e.get("mechanism_note"),
                ),
            )

        # Optional parameters
        params = d.get("parameters")
        if isinstance(params, dict):
            upsert(
                conn,
                "INSERT OR REPLACE INTO parameter_set(drug_id,prodrug,active_metabolite,renal_clearance_flag,half_life_bucket,notes) VALUES(?,?,?,?,?,?)",
                (
                    drug_id,
                    1 if params.get("prodrug") else 0,
                    1 if params.get("active_metabolite") else 0,
                    1 if params.get("renal_clearance_flag") else 0,
                    params.get("half_life_bucket"),
                    params.get("notes"),
                ),
            )


def main() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = connect(DB_PATH)
    apply_schema(conn)
    seed(conn)
    conn.commit()
    conn.close()
    print(f"Seeded {DB_PATH}")


if __name__ == "__main__":
    main()
