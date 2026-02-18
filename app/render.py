from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from core.constants import TRANSPORTER_PGP
from core.enums import Domain
from core.models import RuleHit

# Keep ranks local to rendering
_SEV_RANK = {"info": 0, "caution": 1, "major": 2, "contraindicated": 3}

# Text styles (fine to include backgrounds here)
_SEV_STYLE = {
    "contraindicated": "bold white on red",
    "major": "bold red",
    "caution": "bold yellow",
    "info": "dim",
}

_CLASS_STYLE = {
    "avoid": "bold red",
    "adjust_monitor": "yellow",
    "caution": "yellow",
    "info": "dim",
}


def _border_style_for_severity(sev: str) -> str:
    """Panel borders should use simple colors (avoid background styles)."""
    return {
        "contraindicated": "red",
        "major": "red",
        "caution": "yellow",
        "info": "dim",
    }.get(sev, "dim")


def _mk_console():
    """
    Force ANSI + colors even when Rich mis-detects TTY on Windows.
    Keep this in one place so summary + details behave identically.
    """
    from rich.console import Console

    return Console(
        force_terminal=True,
        no_color=False,
        color_system="truecolor",
        stderr=False,
    )


@dataclass(frozen=True)
class SummaryRow:
    pair: str
    severity: str
    rule_class: str
    domains: str
    pk_hits: int
    pd_hits: int


def _mechanism_domains_for_hit(h: RuleHit) -> set[str]:
    """
    Convert internal PK/PD domains into mechanism labels for the summary table.
    """
    if h.domain == Domain.PD:
        return {"pd"}

    if h.domain != Domain.PK:
        v = getattr(h.domain, "value", str(h.domain))
        return {str(v).lower()}

    out: set[str] = set()
    inputs = h.inputs or {}

    enzyme_id = inputs.get("enzyme_id")
    if isinstance(enzyme_id, str):
        if enzyme_id.startswith("CYP"):
            out.add("cyp")
        elif enzyme_id.startswith("UGT"):
            out.add("ugt")

    transporter_id = inputs.get("transporter_id")
    if transporter_id == TRANSPORTER_PGP:
        out.add("pgp")
    elif isinstance(transporter_id, str) and transporter_id:
        out.add(transporter_id.lower())

    if not out:
        out.add("pk")

    return out


def _domain_summary(rep: Any) -> str:
    domains: set[str] = set()

    for h in (getattr(rep, "pk_hits", None) or []):
        domains.update(_mechanism_domains_for_hit(h))

    for h in (getattr(rep, "pd_hits", None) or []):
        domains.update(_mechanism_domains_for_hit(h))

    if not domains:
        return "-"

    return ",".join(sorted(domains))


def build_summary_rows(facts: Any, reports: Iterable[Any]) -> list[SummaryRow]:
    rows: list[SummaryRow] = []
    for rep in reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name

        sev = str(rep.overall_severity.value).lower()
        cls = str(rep.overall_rule_class.value).lower()

        rows.append(
            SummaryRow(
                pair=f"{d1}\n+\n{d2}",
                severity=sev,
                rule_class=cls,
                domains=_domain_summary(rep),
                pk_hits=len(rep.pk_hits or []),
                pd_hits=len(rep.pd_hits or []),
            )
        )

    rows.sort(key=lambda r: (_SEV_RANK.get(r.severity, 0), r.pair), reverse=True)
    return rows


def render_rich_summary(rows: list[SummaryRow], top: int = 0) -> None:
    from rich.table import Table
    from rich.text import Text

    console = _mk_console()

    table = Table(title="Interaction Summary (pairwise)", show_lines=False)

    # Let Pair wrap
    table.add_column("Pair", overflow="fold", no_wrap=False)
    # Severity: do NOT ellipsize
    table.add_column("Severity", justify="center", no_wrap=True)
    # Class: can keep no_wrap or allow wrap
    table.add_column("Class", justify="center", no_wrap=True)
    table.add_column("Domains", justify="center", no_wrap=True)
    table.add_column("PK hits", justify="right", no_wrap=True)
    table.add_column("PD hits", justify="right", no_wrap=True)

    view = rows[:top] if top and top > 0 else rows
    for r in view:
        sev_style = _SEV_STYLE.get(r.severity, "")
        sev_text = Text(r.severity, style=sev_style)
        class_text = Text(r.rule_class, style=_CLASS_STYLE.get(r.rule_class, ""))

        # Tint the pair name by overall severity for quick scanning.
        pair_text = Text(r.pair, style=sev_style)

        table.add_row(
            pair_text,
            sev_text,
            class_text,
            r.domains,
            str(r.pk_hits),
            str(r.pd_hits),
        )

    console.print(table)


def render_rich_details(
    facts: Any,
    reports: Iterable[Any],
    templates: dict[str, str],
) -> None:
    from rich.panel import Panel
    from rich.text import Text

    from reasoning.explain import render_explanation, render_rationale

    console = _mk_console()

    for rep in reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name

        sev = str(rep.overall_severity.value).lower()
        cls = str(rep.overall_rule_class.value).lower()

        sev_text_style = _SEV_STYLE.get(sev, "bold")
        border_style = _border_style_for_severity(sev)

        # Keep panel title short to avoid truncation
        title = Text(f"{d1} + {d2}", style=sev_text_style)

        body_lines: list[str] = []
        body_lines.append(f"Overall: severity={sev} | class={cls}")
        body_lines.append("")

        if rep.pk_hits:
            body_lines.append("PK section (directional):")
            if rep.pk_summary:
                body_lines.append(f"PK summary: {rep.pk_summary}")
            for h in rep.pk_hits:
                A = facts.drugs[h.inputs["A"]].generic_name
                B = facts.drugs[h.inputs["B"]].generic_name
                body_lines.append(
                    f"- [{h.severity.value} | {h.rule_class.value}] {h.name}"
                )
                body_lines.append(f"  Affected: {A} | Interacting: {B}")
                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    body_lines.append(
                        f"  Explanation: {render_explanation(tmpl, facts, h)}"
                    )
                rat = render_rationale(facts, h)
                if rat:
                    body_lines.append("  Rationale:")
                    for line in rat.splitlines():
                        body_lines.append(f"   {line}")
                if h.actions:
                    body_lines.append("  Suggested actions:")
                    for a in h.actions:
                        body_lines.append(f"   - {a}")
                body_lines.append("")

        if rep.pd_hits:
            body_lines.append("PD section (shared domain):")
            for h in rep.pd_hits:
                body_lines.append(
                    f"- [{h.severity.value} | {h.rule_class.value}] {h.name}"
                )
                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    body_lines.append(
                        f"  Explanation: {render_explanation(tmpl, facts, h)}"
                    )
                rat = render_rationale(facts, h)
                if rat:
                    body_lines.append("  Rationale:")
                    for line in rat.splitlines():
                        body_lines.append(f"   {line}")
                if h.actions:
                    body_lines.append("  Suggested actions:")
                    for a in h.actions:
                        body_lines.append(f"   - {a}")
                body_lines.append("")

        body = "\n".join(body_lines).strip() if body_lines else "(No details.)"

        console.print(
            Panel(
                body,
                title=title,
                border_style=border_style,
                expand=False,
            )
        )
