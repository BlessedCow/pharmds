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
        ("CYP2C19", "CYP", "Relevant for clopidogrel activation and some SSRIs/benzos."),
        ("CYP2D6", "CYP", "Relevant for codeine/tramadol activation, many antidepressants."),
        ("CYP1A2", "CYP", "Affected by inhibitors and smoking induction (later)."),
    ]
    for e in enzymes:
        upsert(conn, "INSERT OR REPLACE INTO enzyme(id,family,description) VALUES(?,?,?)", e)

    # Transporters
    transporters = [
        ("P-gp", "P-glycoprotein (ABCB1); influences absorption/efflux of select drugs."),
    ]
    for t in transporters:
        upsert(conn, "INSERT OR REPLACE INTO transporter(id,description) VALUES(?,?)", t)

    # PD effects
    pd_effects = [
        ("QT_prolongation", "Potential to prolong QT interval / torsades risk domain."),
        ("CNS_depression", "Sedation/respiratory depression/falls risk domain."),
        ("serotonergic", "Serotonin excess/serotonin syndrome risk domain."),
        ("bleeding", "Bleeding risk domain."),
        ("anticholinergic", "Anticholinergic burden domain."),
        ("hypotension", "Orthostasis/hypotension domain."),
    ]
    for pe in pd_effects:
        upsert(conn, "INSERT OR REPLACE INTO pd_effect(id,description) VALUES(?,?)", pe)

    # Drugs (16)
    drugs = [
        ("midazolam", "midazolam", "benzodiazepine", "moderate", "Educational CYP3A4 substrate anchor."),
        ("clarithromycin", "clarithromycin", "macrolide antibiotic", "moderate", "Educational strong CYP3A4 inhibitor anchor."),
        ("rifampin", "rifampin", "rifamycin antibiotic", "moderate", "Educational strong inducer anchor; time-course note important."),
        ("fluconazole", "fluconazole", "azole antifungal", "moderate", "Educational CYP2C9/2C19 inhibitor anchor."),
        ("warfarin", "warfarin", "anticoagulant", "narrow", "Narrow TI. Classic CYP2C9 interaction patterns."),
        ("digoxin", "digoxin", "cardiac glycoside", "narrow", "Transporter-centric (P-gp substrate) interactions; narrow TI."),
        ("clopidogrel", "clopidogrel", "antiplatelet", "moderate", "Prodrug activation via CYP2C19; inhibition reduces efficacy."),
        ("tramadol", "tramadol", "opioid analgesic", "moderate", "Mixed mechanism; CYP2D6 activation + serotonergic risk."),
        ("sertraline", "sertraline", "SSRI", "moderate", "Serotonergic PD stacking anchor."),
        ("amitriptyline", "amitriptyline", "TCA", "moderate", "Anticholinergic + QT + CYP2D6 substrate patterns."),
        ("quetiapine", "quetiapine", "atypical antipsychotic", "moderate", "CYP3A4 substrate; CNS depression/hypotension."),
        ("diazepam", "diazepam", "benzodiazepine", "moderate", "CNS depression stacking; some CYP2C19 relevance."),
        ("citalopram", "citalopram", "SSRI", "moderate", "QT domain anchor."),
        ("ondansetron", "ondansetron", "antiemetic", "moderate", "QT domain co-prescription anchor."),
        ("celecoxib", "celecoxib", "NSAID", "moderate", "CYP2C9 substrate; teaching point for inhibition."),
        ("ciprofloxacin", "ciprofloxacin", "fluoroquinolone antibiotic", "moderate", "CYP1A2 inhibitor anchor (for later)."),
    ]
    for d in drugs:
        upsert(conn, "INSERT OR REPLACE INTO drug(id,generic_name,drug_class,therapeutic_index,notes) VALUES(?,?,?,?,?)", d)

    # Aliases (keep small; users can extend)
    aliases = [
        ("midazolam", "versed"),
        ("clarithromycin", "biaxin"),
        ("rifampin", "rifadin"),
        ("fluconazole", "diflucan"),
        ("warfarin", "coumadin"),
        ("digoxin", "lanoxin"),
        ("clopidogrel", "plavix"),
        ("tramadol", "ultram"),
        ("sertraline", "zoloft"),
        ("amitriptyline", "elavil"),
        ("quetiapine", "seroquel"),
        ("diazepam", "valium"),
        ("citalopram", "celexa"),
        ("ondansetron", "zofran"),
        ("celecoxib", "celebrex"),
        ("ciprofloxacin", "cipro"),
    ]
    for drug_id, alias in aliases:
        upsert(conn, "INSERT OR IGNORE INTO drug_alias(drug_id,alias) VALUES(?,?)", (drug_id, alias.lower()))

    # Enzyme roles
    roles = [
        # CYP3A4 anchor set
        ("midazolam", "CYP3A4", "substrate", None, 0.6, "Classic CYP3A4 substrate (educational)."),
        ("clarithromycin", "CYP3A4", "inhibitor", "strong", None, "Strong CYP3A4 inhibition (educational)."),
        ("rifampin", "CYP3A4", "inducer", "strong", None, "Strong induction; delayed onset/offset (educational)."),
        ("quetiapine", "CYP3A4", "substrate", None, 0.5, "Predominantly CYP3A4 clearance (educational)."),

        # CYP2C9
        ("warfarin", "CYP2C9", "substrate", None, 0.5, "S-warfarin relevance (educational)."),
        ("fluconazole", "CYP2C9", "inhibitor", "moderate", None, "Inhibits CYP2C9 (educational)."),
        ("celecoxib", "CYP2C9", "substrate", None, 0.4, "CYP2C9 substrate (educational)."),

        # CYP2C19 (activation)
        ("clopidogrel", "CYP2C19", "substrate", None, 0.5, "Represents activation pathway (educational)."),
        ("fluconazole", "CYP2C19", "inhibitor", "moderate", None, "Inhibits CYP2C19 (educational)."),
        ("diazepam", "CYP2C19", "substrate", None, 0.3, "CYP2C19 contributes to clearance (educational)."),

        # CYP2D6 (activation)
        ("tramadol", "CYP2D6", "substrate", None, 0.4, "Represents activation pathway (educational)."),
        ("amitriptyline", "CYP2D6", "substrate", None, 0.3, "CYP2D6 contributes (educational)."),
    ]
    for drug_id, enzyme_id, role, strength, fm, notes in roles:
        upsert(
            conn,
            """
            INSERT OR REPLACE INTO drug_enzyme_role(drug_id,enzyme_id,role,strength,fraction_metabolized,notes)
            VALUES(?,?,?,?,?,?)
            """,
            (drug_id, enzyme_id, role, strength, fm, notes),
        )

    # Transporter roles
    t_roles = [
        ("digoxin", "P-gp", "substrate", None, "P-gp substrate (educational)."),
        ("clarithromycin", "P-gp", "inhibitor", "moderate", "May inhibit P-gp (educational). Keep conservative."),
    ]
    for drug_id, transporter_id, role, strength, notes in t_roles:
        upsert(
            conn,
            """
            INSERT OR REPLACE INTO drug_transporter_role(drug_id,transporter_id,role,strength,notes)
            VALUES(?,?,?,?,?)
            """,
            (drug_id, transporter_id, role, strength, notes),
        )

    # PD profiles
    pd_profiles = [
        ("warfarin", "bleeding", "increase", "high", "Anticoagulant effect domain."),
        ("clopidogrel", "bleeding", "increase", "medium", "Antiplatelet effect domain."),
        ("celecoxib", "bleeding", "increase", "low", "NSAID-related bleeding risk domain (educational)."),

        ("diazepam", "CNS_depression", "increase", "high", "Sedation/resp depression domain."),
        ("midazolam", "CNS_depression", "increase", "high", "Sedation/resp depression domain."),
        ("quetiapine", "CNS_depression", "increase", "medium", "Sedation domain."),
        ("quetiapine", "hypotension", "increase", "medium", "Orthostasis domain."),

        ("sertraline", "serotonergic", "increase", "medium", "SSRI serotonin domain."),
        ("citalopram", "serotonergic", "increase", "medium", "SSRI serotonin domain."),
        ("tramadol", "serotonergic", "increase", "medium", "Serotonin-reuptake component domain."),
        ("amitriptyline", "serotonergic", "increase", "low", "Serotonergic component domain."),

        ("citalopram", "QT_prolongation", "increase", "high", "QT domain."),
        ("ondansetron", "QT_prolongation", "increase", "medium", "QT domain."),
        ("amitriptyline", "QT_prolongation", "increase", "medium", "QT domain."),

        ("amitriptyline", "anticholinergic", "increase", "high", "Anticholinergic burden domain."),
    ]
    for drug_id, eff, direction, mag, note in pd_profiles:
        upsert(
            conn,
            """
            INSERT OR REPLACE INTO drug_pd_effect(drug_id,pd_effect_id,direction,magnitude,mechanism_note)
            VALUES(?,?,?,?,?)
            """,
            (drug_id, eff, direction, mag, note),
        )

    # Parameter sets
    params = [
        ("clopidogrel", 1, 0, 0, "long", "Prodrug flag for activation logic."),
        ("tramadol", 0, 1, 1, "medium", "Active metabolite concept + renal relevance (educational)."),
    ]
    for drug_id, prodrug, active_met, renal_flag, hl, notes in params:
        upsert(
            conn,
            """
            INSERT OR REPLACE INTO parameter_set(drug_id,prodrug,active_metabolite,renal_clearance_flag,half_life_bucket,notes)
            VALUES(?,?,?,?,?,?)
            """,
            (drug_id, prodrug, active_met, renal_flag, hl, notes),
        )

    conn.commit()


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(DB_PATH)
    apply_schema(conn)
    seed(conn)
    conn.close()
    print(f"Seeded database at: {DB_PATH}")


if __name__ == "__main__":
    main()
