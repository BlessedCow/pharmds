from __future__ import annotations

import json

from app.cli.render.plain import render_evidence_gap_report
from core.evidence.completeness import build_pd_effect_evidence_gap_report


def handle_evidence_gap_command(args, facts) -> bool:
    if not args.show_evidence_gaps:
        return False

    report = build_pd_effect_evidence_gap_report(facts)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
        return True

    print(
        render_evidence_gap_report(
            report,
            show_complete=args.show_complete_evidence_coverage,
        )
    )
    return True