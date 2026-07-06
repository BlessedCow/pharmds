from __future__ import annotations

from pathlib import Path

from rich.console import Console

from app.cli.commands import (
    handle_evidence_gap_command,
    handle_mechanism_debug_command,
    handle_output_command,
)
from app.cli.parser import build_parser
from app.cli.runtime import (
    build_cli_pair_reports,
    build_cli_session,
    build_cli_summaries,
    resolve_aggregate_summary_limit,
)

console = Console()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "pharmds.sqlite3"
RULE_DIR = BASE_DIR / "rules" / "rule_defs"

DEFAULT_PUBLIC_RESULT_SUMMARY_LIMIT = 5

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    session = build_cli_session(args, db_path=DB_PATH)

    drug_names = session.drug_names
    drug_ids = session.drug_ids
    patient_flags = session.patient_flags
    facts = session.facts

    if handle_evidence_gap_command(args, facts):
        return

    if handle_mechanism_debug_command(
        args,
        facts,
        drug_ids,
        rule_dir=RULE_DIR,
    ):
        return

    selected, templates, pair_reports = build_cli_pair_reports(
        args,
        facts=facts,
        drug_ids=drug_ids,
        rule_dir=RULE_DIR,
    )
    
    regimen_summary, pipeline, public_result_summaries = build_cli_summaries(
        args,
        facts=facts,
        drug_ids=drug_ids,
        pair_reports=pair_reports,
    )
    aggregate_summary_limit = resolve_aggregate_summary_limit(args)

    handle_output_command(
        args,
        facts=facts,
        pair_reports=pair_reports,
        templates=templates,
        selected=selected,
        drug_names=drug_names,
        patient_flags=patient_flags,
        regimen_summary=regimen_summary,
        public_result_summaries=public_result_summaries,
        console=console,
        aggregate_summary_limit=aggregate_summary_limit,
    )


if __name__ == "__main__":
    main()
