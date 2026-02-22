from __future__ import annotations

import sqlite3
from pathlib import Path

import core.constants as c
from data.curation.validate import _load_rule_pd_effect_ids

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
    try:
        conn.execute(sql, params)
    except Exception:
        print("\nFAILED SQL:\n", sql)
        print("PARAMS:\n", params)

        # Extra FK diagnostics for drug_pd_effect
        if "into drug_pd_effect" in sql.lower():
            drug_id, pd_effect_id = params[0], params[1]
            d = conn.execute("SELECT 1 FROM drug WHERE id=?", (drug_id,)).fetchone()
            p = conn.execute(
                "SELECT 1 FROM pd_effect WHERE id=?", (pd_effect_id,)
            ).fetchone()
            print("PARENT drug exists?:", bool(d), "id=", drug_id)
            print("PARENT pd_effect exists?:", bool(p), "id=", pd_effect_id)

        raise


def seed(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")

    # Enzymes (lookup)
    enzymes = [
        ("CYP3A4", "CYP", "Major drug-metabolizing enzyme; many substrates."),
        ("CYP2C9", "CYP", "Important for warfarin and NSAIDs."),
        ("CYP2C19", "CYP", "Relevant for clopidogrel activation and some SSRIs/benzos."),
        ("CYP2D6", "CYP", "Relevant for codeine/tramadol activation, many antidepressants."),
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
            "Phase II glucuronidation enzyme; relevant for some opioids (educational).",
        ),
    ]
    for e in enzymes:
        upsert(conn, "INSERT OR REPLACE INTO enzyme(id,family,description) VALUES(?,?,?)", e)

    # Transporters (lookup)
    transporters = [
        (
            "P-gp",
            "P-glycoprotein (ABCB1); efflux transporter affecting absorption and elimination.",
        ),
        ("OATP1B1", "Hepatic uptake transporter (SLCO1B1)."),
        ("BCRP", "Breast Cancer Resistance Protein (ABCG2); efflux transporter."),
    ]
    for t in transporters:
        upsert(conn, "INSERT OR REPLACE INTO transporter(id,description) VALUES(?,?)", t)

    # PD effects (lookup)
    #
    # IMPORTANT:
    # - drug_pd_effect has an FK to pd_effect(id)
    # - pd_effect.description may be NOT NULL in schema, so always provide a string
    #
    # Seed:
    # 1) known PD IDs from constants
    # 2) PD IDs inferred from PD rules
    # 3) any curated PD IDs we know appear in drugs.json (defensive)
    pd_ids = {v for k, v in vars(c).items() if k.startswith("PD_EFFECT_")}
    pd_ids |= _load_rule_pd_effect_ids()

    # Defensive must-have IDs used in curation (prevents FK failures even if parsing changes)
    pd_ids |= {
        "sedation",
        "respiratory_depression",
        "opioid_antagonist",
        "withdrawal_risk",
        "seizure_risk",
    }

    for eid in sorted(pd_ids):
        upsert(conn, "INSERT OR IGNORE INTO pd_effect(id,description) VALUES(?,?)", (eid, ""))

    # Optional: override descriptions for a curated subset (keeps DB more readable)
    pd_effect_descriptions = [
        ("QT_prolongation", "Potential to prolong QT interval / torsades risk domain."),
        ("CNS_depression", "Sedation/respiratory depression/falls risk domain."),
        ("serotonergic", "Serotonin excess/serotonin syndrome risk domain."),
        ("bleeding", "Bleeding risk domain."),
        ("anticholinergic", "Anticholinergic burden domain."),
        ("hypotension", "Orthostasis/hypotension domain."),
        ("bradycardia", "Heart rate lowering / symptomatic bradycardia risk domain."),
        ("serotonin_syndrome", "Serotonin toxicity syndrome risk domain (educational)."),
        ("hypoglycemia", "Hypoglycemia risk domain."),
        ("cardiovascular", "Cardiovascular effects (educational)."),
        ("CNS_stimulation", "CNS stimulation/agitation/insomnia risk domain."),
        ("hypertension", "Blood pressure elevation / hypertension risk domain."),
        ("tachycardia", "Heart rate elevation / tachycardia risk domain."),
        (
            "sympathetic_stimulation",
            "Sympathomimetic stimulation (BP/HR/agitation) risk domain.",
        ),
        ("sedation", "Sedation/somnolence domain."),
        ("respiratory_depression", "Respiratory depression domain."),
        ("opioid_antagonist", "Opioid antagonism domain."),
        ("withdrawal_risk", "Withdrawal risk domain."),
        ("seizure_risk", "Seizure risk domain."),
    ]
    for pe in pd_effect_descriptions:
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

        # Parent drug row first (FK parent for aliases/roles/pd_effects/parameters)
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

        # Enzyme roles (FK to enzyme + drug)
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

        # Transporter roles (FK to transporter + drug)
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

        # PD effects (FK to pd_effect + drug)
        for e in d.get("pd_effects", []) or []:
            pe_id = normalize_pd_effect_id(e["effect_id"])

            # Just-in-time guarantee: ensure parent exists even if something changes upstream
            upsert(
                conn,
                "INSERT OR IGNORE INTO pd_effect(id,description) VALUES(?,?)",
                (pe_id, ""),
            )

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

        # Optional parameters (FK to drug via drug_id in parameter_set)
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