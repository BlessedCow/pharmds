from __future__ import annotations

import json

from rich.panel import Panel

from app.cli.render.plain import (
    render_plain_pairwise_details,
    render_plain_regimen_summary,
    render_public_result_summaries,
)
from app.cli.render.rich import (
    build_summary_rows,
    render_rich_details,
    render_rich_summary,
)
from app.json_output import build_json_payload


def _render_rich_regimen_summary(console, regimen_summary) -> None:
    sev = regimen_summary["overall_severity"].value
    cls = regimen_summary["overall_rule_class"].value
    flags = regimen_summary.get("regimen_flags", [])
    hit_counts = regimen_summary.get("hit_counts", {})
    pd_stacks = regimen_summary.get("pd_stacks", [])
    top_pairs = regimen_summary.get("top_pairs", [])

    lines = [
        f"Overall (regimen): severity={sev} | class={cls}",
        regimen_summary.get("overview", ""),
        "",
        regimen_summary.get("pairwise_summary", ""),
        regimen_summary.get("cumulative_concern_summary", ""),
        "",
        f"Drugs: {regimen_summary.get('n_drugs', 0)}",
        (
            "Pairs with pairwise hits: "
            f"{regimen_summary.get('pair_count_with_hits', 0)}"
        ),
        (
            "Pairwise hits: "
            f"{hit_counts.get('total', 0)} "
            f"(PK={hit_counts.get('pk', 0)}, PD={hit_counts.get('pd', 0)})"
        ),
        f"Regimen-wide flags: {len(flags)}",
    ]

    if pd_stacks:
        lines.append("")
        lines.append("Regimen-wide repeated PD concern domains:")
        for stack in pd_stacks[:5]:
            drug_names = ", ".join(d["drug_name"] for d in stack.get("drugs", []))
            lines.append(
                f"- {stack['label']}: {stack['count']} drugs "
                f"(max={stack['max_magnitude']})"
                f" - {drug_names}"
            )

    if flags:
        lines.append("")
        lines.append("Regimen-wide educational flags:")
        for flag in flags[:5]:
            lines.append(f"- {flag.get('message', '')}")

    if top_pairs:
        lines.append("")
        lines.append("Pairwise concern highlights:")
        for pair in top_pairs[:3]:
            lines.append(
                f"- {pair['drug_1']['name']} + {pair['drug_2']['name']}: "
                f"{pair['severity']} | {pair['class']} "
                f"({pair['total_hits']} hits)"
            )

    console.print(
        Panel(
            "\n".join(lines),
            title="Regimen Summary (all drugs)",
            expand=True,
        )
    )


def handle_output_command(
    args,
    *,
    facts,
    pair_reports,
    templates,
    selected,
    drug_names,
    patient_flags,
    regimen_summary,
    public_result_summaries,
    console,
) -> None:
    if args.format == "json":
        payload = build_json_payload(
            facts=facts,
            reports=pair_reports,
            templates=templates,
            selected_domains=selected,
            input_drug_names=drug_names,
            patient_flags=patient_flags,
            regimen_summary=regimen_summary,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    if not pair_reports and not public_result_summaries and not regimen_summary:
        domains = ", ".join(selected)
        print(
            "No rule-based interactions detected in selected domains: "
            f"{domains} (educational scope)."
        )
        return

    if args.format == "rich":
        print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")

        if regimen_summary:
            _render_rich_regimen_summary(console, regimen_summary)
            print()

        rows = build_summary_rows(facts, pair_reports)
        render_rich_summary(rows, top=args.top or 0)

        detail_reports = (
            pair_reports[: args.top] if args.top and args.top > 0 else pair_reports
        )
        if args.details:
            render_rich_details(
                facts,
                detail_reports,
                templates,
                show_evidence=args.show_evidence,
            )
        return

    # PLAIN MODE
    print("\nEDUCATIONAL ONLY - NOT DIAGNOSTIC\n")

    if regimen_summary:
        print(render_plain_regimen_summary(regimen_summary))
        print()

    if public_result_summaries:
        print("Key Interaction Summaries")
        print("=========================")
        print()
        print(
            render_public_result_summaries(
                public_result_summaries,
                top=args.top,
            )
        )
        print()

    detail_reports = (
        pair_reports[: args.top] if args.top and args.top > 0 else pair_reports
    )

    if args.details:
        print(
            render_plain_pairwise_details(
                facts,
                detail_reports,
                templates,
                show_evidence=args.show_evidence,
            )
        )