from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from app.cli.facts import connect, load_facts
from app.cli.inputs import (
    _collect_drug_inputs,
    _format_unknown_drug_message,
    resolve_drug_ids,
)
from app.cli.runtime.options import build_patient_flags
from core.exceptions import UnknownDrugError


@dataclass(frozen=True)
class CliSession:
    drug_names: list[str]
    drug_ids: list[str]
    patient_flags: dict[str, bool]
    facts: object


def build_cli_session(
    args,
    *,
    db_path: Path,
) -> CliSession:
    drug_names = _collect_drug_inputs(args.drugs, args.file)
    if len(drug_names) < 2:
        raise SystemExit(
            "Provide at least two drugs, or use --file / stdin for a list."
        )

    conn = connect(db_path)

    try:
        drug_ids = resolve_drug_ids(conn, drug_names)
    except UnknownDrugError as e:
        for tok in e.unknown:
            opts = e.suggestions.get(tok, ())
            print(_format_unknown_drug_message(tok, opts), file=sys.stderr)

        print(
            "Tip: common separators such as spaces, hyphens, slashes, and "
            "underscores are treated the same.",
            file=sys.stderr,
        )
        raise SystemExit(2) from e

    patient_flags = build_patient_flags(args)
    facts = load_facts(conn, drug_ids, patient_flags)

    return CliSession(
        drug_names=drug_names,
        drug_ids=drug_ids,
        patient_flags=patient_flags,
        facts=facts,
    )