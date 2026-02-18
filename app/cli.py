from __future__ import annotations

import argparse
import difflib
import sqlite3
import sys
from itertools import combinations
from pathlib import Path

from core.constants import normalize_pd_effect_id, normalize_transporter_id
from core.enums import Domain
from core.exceptions import UnknownDrugError
from core.models import Drug, EnzymeRole, Facts, PDEffect, TransporterRole
from reasoning.combine import build_pair_reports
from reasoning.explain import render_explanation, render_rationale
from rules.engine import evaluate_all, load_rules, rule_mechanisms

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
RULE_DIR = BASE_DIR / "rules" / "rule_defs"


def _parse_drug_tokens(text: str) -> list[str]:
    """Parse drug tokens from free-form text.

    Supports:
    - one drug per line
    - comma-separated lists
    - whitespace-separated lists
    - comments starting with '#'
    """
    out: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        # Allow comma-separated values.
        line = line.replace(",", " ")
        out.extend([p for p in line.split() if p])

    return out


def _read_drug_tokens_from_file(path: str) -> list[str]:
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise SystemExit(f"--file not found: {p}") from e
    return _parse_drug_tokens(text)


def _read_drug_tokens_from_stdin() -> list[str]:
    return _parse_drug_tokens(sys.stdin.read())


def _collect_drug_inputs(
    positional: list[str] | None,
    file_paths: list[str] | None,
) -> list[str]:
    """Collect drug names from positional args, one/more files, and/or stdin.

    Rules:
    - If --file is provided, read each file ("-" means stdin).
    - Positional args are appended after file inputs.
    - If neither positional nor --file is given, and stdin is not a TTY,
      read from stdin (pipe-friendly default).
    """
    drugs: list[str] = []

    file_paths = file_paths or []
    if file_paths:
        for fp in file_paths:
            if fp == "-":
                drugs.extend(_read_drug_tokens_from_stdin())
            else:
                drugs.extend(_read_drug_tokens_from_file(fp))
    else:
        # No --file: if nothing positional and input is piped, read stdin.
        if not (positional or []) and not sys.stdin.isatty():
            drugs.extend(_read_drug_tokens_from_stdin())

    drugs.extend(positional or [])

    # De-duplicate while preserving order.
    seen: set[str] = set()
    out: list[str] = []
    for d in drugs:
        dd = d.strip()
        if not dd:
            continue
        key = dd.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(dd)

    return out


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def resolve_drug_ids(conn: sqlite3.Connection, names: list[str]) -> list[str]:
    out: list[str] = []
    unknown: list[str] = []

    for raw in names:
        q = raw.strip().lower()

        row = conn.execute(
            "SELECT id FROM drug WHERE lower(generic_name)=?", (q,)
        ).fetchone()
        if row:
            out.append(row["id"])
            continue

        row = conn.execute(
            "SELECT drug_id FROM drug_alias WHERE alias=?", (q,)
        ).fetchone()
        if row:
            out.append(row["drug_id"])
            continue

        unknown.append(raw)

    if unknown:
        known_terms = _fetch_known_drug_terms(conn)
        sug_map = {}
        for tok in unknown:
            sug = _suggest_drug_terms(tok, known_terms, limit=5)
            if sug:
                sug_map[tok] = sug
        raise UnknownDrugError(unknown, suggestions=sug_map)

    return out


def load_facts(
    conn: sqlite3.Connection, drug_ids: list[str], patient_flags: dict[str, bool]
) -> Facts:
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
                transporter_id=normalize_transporter_id(r["transporter_id"]),
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
                effect_id=normalize_pd_effect_id(r["pd_effect_id"]),
                direction=r["direction"],
                magnitude=r["magnitude"],
                mechanism_note=r["mechanism_note"],
            )
        )

    return facts


def _fetch_known_drug_terms(conn: sqlite3.Connection) -> list[str]:
    """
    Return a list of known drug terms users might type:
    - generic names (lowercased)
    - aliases (already stored lowercased in DB by your resolver expectations)
    """
    terms: list[str] = []

    rows = conn.execute("SELECT generic_name FROM drug").fetchall()
    for r in rows:
        s = (r["generic_name"] or "").strip().lower()
        if s:
            terms.append(s)

    # If your schema uses a different table/column name, adjust here.
    rows = conn.execute("SELECT alias FROM drug_alias").fetchall()
    for r in rows:
        s = (r["alias"] or "").strip().lower()
        if s:
            terms.append(s)

    # de-duplicate while keeping stable ordering
    seen = set()
    out = []
    for t in terms:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _suggest_drug_terms(
    token: str, known_terms: list[str], limit: int = 5
) -> tuple[str, ...]:
    """
    Suggest close matches for a token from known terms.

    Uses difflib to keep it local and dependency-free.
    """
    q = (token or "").strip().lower()
    if not q:
        return tuple()

    matches = difflib.get_close_matches(q, known_terms, n=limit, cutoff=0.6)
    return tuple(matches)


def _sev_rank(sev: str) -> int:
    # Match Severity values: info/caution/major/contraindicated
    order = {"info": 0, "caution": 1, "major": 2, "contraindicated": 3}
    return order.get(sev, 0)


def _build_reports_for_all_pairs(facts, hits, templates, drug_ids):
    pairs = list(combinations(drug_ids, 2))
    return build_pair_reports(
        facts=facts,
        hits=hits,
        rule_templates=templates,
        pairs=pairs,
    )


def _parse_domain_selection(domain_arg: str) -> list[str]:
    raw = (domain_arg or "all").strip().lower()
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    selected: list[str] = []

    def add(x: str) -> None:
        if x not in selected:
            selected.append(x)

    for p in parts:
        if p == "all":
            add("cyp")
            add("ugt")
            add("pgp")
            add("bcrp")
            add("oatp")
            add("pd")
        elif p == "pk":
            add("cyp")
            add("ugt")
            add("pgp")
            add("bcrp")
            add("oatp")
        elif p == "pd":
            add("pd")
        elif p == "cyp":
            add("cyp")
        elif p == "pgp":
            add("pgp")
        elif p == "bcrp":
            add("bcrp")
        elif p == "oatp":
            add("oatp")
        elif p == "ugt":
            add("ugt")
        else:
            raise SystemExit(
                "Unknown --domain option. Use: all, pk, pd, cyp, ugt, pgp, bcrp, oatp"
            )

    if not selected:
        selected = ["cyp", "ugt", "pgp", "bcrp", "oatp", "pd"]

    return selected


def filter_rules_for_selected_domains(rules_all, selected: list[str]):
    """
    Filter rules for the CLI-selected domains.

    Here, 'domains' are user-facing slices based on rule mechanism tags:
      - cyp: CYP-mediated PK rules
      - pgp: P-gp transporter PK rules
      - pd:  PD effect stacking rules
    """
    selected_set = set(selected)
    out = []

    for r in rules_all:
        mechs = set(rule_mechanisms(r))
        if mechs & selected_set:
            out.append(r)

    return out


def main() -> None:
    p = argparse.ArgumentParser(
        description="Educational PK/PD interaction reasoner (rule-based)."
    )
    p.add_argument(
        "drugs",
        nargs="*",
        help=(
            "Drug names (generic or alias). Example: warfarin fluconazole. "
            "For polypharmacy, prefer --file or piping via stdin."
        ),
    )
    p.add_argument(
        "-f",
        "--file",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Read drug names from a file (repeatable). One drug per line, "
            "or comma/whitespace-separated. Use '-' to read from stdin. "
            "If no drugs are provided and stdin is piped, stdin is read automatically."
        ),
    )
    p.add_argument(
        "--format",
        choices=("plain", "rich"),
        default="plain",
        help=(
            "Output format. Use 'rich' for colored tables/panels (requires rich). "
            "Default: plain."
        ),
    )
    p.add_argument(
        "--details",
        action="store_true",
        help=("In rich mode, print full per-pair details after the summary."),
    )
    p.add_argument(
        "--top",
        type=int,
        default=0,
        help=("In rich mode, show only the top N pairs in the summary (0 = all)."),
    )
    p.add_argument(
        "--qt-risk",
        action="store_true",
        help="Patient has QT risk factors (educational flag).",
    )
    p.add_argument(
        "--bleeding-risk",
        action="store_true",
        help="Patient has bleeding risk factors (educational flag).",
    )
    p.add_argument(
        "--domain",
        default="all",
        help=(
            "Comma-separated mechanism filters. "
            "Allowed: cyp, ugt, pgp, bcrp, oatp, pd, pk (alias), all. "
            "Examples: --domain cyp  |  --domain ugt  |  --domain pd  |  "
            "--domain cyp,pd"
        ),
    )
    args = p.parse_args()

    drug_names = _collect_drug_inputs(args.drugs, args.file)
    if len(drug_names) < 2:
        raise SystemExit(
            "Provide at least two drugs, or use --file / stdin for a list."
        )

    conn = connect(DB_PATH)

    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
    except UnknownDrugError as e:
        # Print one line per unknown token for clarity
        for tok in e.unknown:
            opts = e.suggestions.get(tok, ())
            if opts:
                print(
                    f"Drug '{tok}' not found. Did you mean: {', '.join(opts)}?",
                    file=sys.stderr,
                )
            else:
                print(f"Drug '{tok}' not found.", file=sys.stderr)

        print(
            "Tip: use generic names or add aliases in the local database.",
            file=sys.stderr,
        )
        raise SystemExit(2) from e

    patient_flags = {
        "qt_risk": bool(args.qt_risk),
        "bleeding_risk": bool(args.bleeding_risk),
    }
    facts = load_facts(conn, drug_ids, patient_flags)

    selected = _parse_domain_selection(args.domain)

    rules_all = load_rules(RULE_DIR)
    rules = filter_rules_for_selected_domains(rules_all, selected)

    hits = evaluate_all(rules, facts, drug_ids)
    
    for h in hits:
        if h.domain == Domain.PK:
            print("DEBUG PK HIT:", h.rule_id, h.inputs)

    from rules.composite_rules import apply_composites

    hits = apply_composites(facts, hits)

    templates = {r.id: r.explanation_template for r in rules}
    reports = _build_reports_for_all_pairs(facts, hits, templates, drug_ids)

    if not reports:
        domains = ", ".join(selected)
        print(
            "No rule-based interactions detected in selected domains: "
            f"{domains} (educational scope)."
        )
        return

    # RICH MODE
    if args.format == "rich":
        from app.render import (
            build_summary_rows,
            render_rich_details,
            render_rich_summary,
        )

        print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")
        rows = build_summary_rows(facts, reports)
        render_rich_summary(rows, top=args.top)
        
        detail_reports = reports[: args.top] if args.top and args.top > 0 else reports
        render_rich_details(facts, detail_reports, templates)
        
        
        if args.details:
            render_rich_details(facts, reports, templates)

        return

    # PLAIN MODE
    print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")
    for rep in reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name

        print("=" * 80)
        print(f"{d1} + {d2}")
        print(
            f"Overall: severity={rep.overall_severity.value} | "
            f"class={rep.overall_rule_class.value}"
        )
        print()

        if rep.pk_hits:
            print("PK section (directional):")
            if rep.pk_summary:
                print(f"PK summary: {rep.pk_summary}")
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

        refs: list[dict[str, str]] = []
        for h in (rep.pk_hits or []) + (rep.pd_hits or []):
            refs.extend(h.references)

        uniq = {
            (r.get("source", ""), r.get("citation", ""), r.get("url", "")) for r in refs
        }
        if uniq:
            print("References (rule-level):")
            for source, citation, url in sorted(uniq):
                if url:
                    print(f"- {source}: {citation} ({url})")
                else:
                    print(f"- {source}: {citation}")
        print()

    print("=" * 80)
    print(
        "Footer: This output is an educational mechanistic explanation. "
        "Verify with primary sources.\n"
    )


if __name__ == "__main__":
    main()
