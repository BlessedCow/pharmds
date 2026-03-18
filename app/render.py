from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from core.constants import TRANSPORTER_PGP
from core.enums import Domain
from core.models import RuleHit
from reasoning.explain import render_explanation, render_rationale

# Keep ranks local to rendering
_SEV_RANK = {"info": 0, "caution": 1, "major": 2, "contraindicated": 3}

# Text styles
_SEV_STYLE = {
    "contraindicated": "bold white on red",
    "major": "bold red",
    "caution": "bold yellow",
    "info": "dim",
}

PD_EFFECT_STYLES: dict[str, str] = {
    "QT_prolongation": "magenta",
    "serotonin_syndrome": "purple",
    "serotonergic": "purple",
    "h1_antagonism": "bright_yellow",
    "H1_antagonism": "bright_yellow",
    "CNS_depression": "cyan",
    "respiratory_depression": "bright_red",
    "sedation": "cyan",
    "anticholinergic_effects": "bright_magenta",
    "bleeding": "red",
    "bradycardia": "blue",
    "orthostatic_hypotension": "blue",
    "seizure_threshold": "yellow",
    "withdrawal_risk": "yellow",
    "renal_function": "green",
    "lithium_increase_risk": "bright_red",
    "noradrenergic_effects": "bright_blue",
    "alpha1_antagonism": "bright_blue",
    "EPS_risk": "bright_red",
    "D2_blockade": "red",
    "constipation_risk": "yellow",
}

_CLASS_STYLE = {
    "avoid": "bold red",
    "adjust_monitor": "yellow",
    "caution": "yellow",
    "info": "dim",
}

_EFFECT_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_]+\b")

def _table_style(sev: str, cls: str) -> str:
    sev = (sev or "").lower()
    cls = (cls or "").lower()

    # Class override: avoid should always read "danger"
    if cls == "avoid":
        if sev == "contraindicated":
            return "bold red"
        if sev == "major":
            return "bold red3"
        if sev == "caution":
            return "bold red3"
        return "bold red3"

    # Otherwise color primarily by severity (foreground only)
    if sev == "contraindicated":
        return "bold red"
    if sev == "major":
        return "bold red3"
    if sev == "caution":
        return "bold orange1" 
    return "dim"

def _badge_style(sev: str, cls: str) -> str:
    """
    Background-style badge coloring for detailed hit rendering.
    This is intentionally more visually strong than table styling.
    """
    sev = (sev or "").lower()
    cls = (cls or "").lower()

    # Class override first
    if cls == "avoid":
        if sev == "contraindicated":
            return "bold white on red"
        if sev == "major":
            return "bold white on dark_red"
        if sev == "caution":
            return "bold white on red3"
        return "bold white on dark_red"

    # Otherwise severity-driven
    if sev == "contraindicated":
        return "bold white on red"
    if sev == "major":
        return "bold red"
    if sev == "caution":
        return "bold orange1"
    return "dim"

def badge(sev: str, cls: str) -> Text:
    """
    Build a colored "[severity | class]" badge.
    """
    style = _badge_style(sev, cls)
    t = Text()
    t.append("[", style="dim")
    t.append(sev.lower(), style=style)
    t.append(" | ", style="dim")
    t.append(cls.lower(), style=style)
    t.append("]", style="dim")
    return t

def _mk_console() -> Console:
    """
    Force ANSI + colors even when Rich mis-detects TTY on Windows.
    Keep this in one place so summary + details behave identically.
    """
    return Console(
        force_terminal=True,
        no_color=False,
        color_system="truecolor",
        stderr=False,
    )


def _border_style_for_severity(sev: str) -> str:
    """Panel borders should use simple colors (avoid background styles)."""
    return {
        "contraindicated": "red",
        "major": "red",
        "caution": "yellow",
        "info": "dim",
    }.get(sev, "dim")


def styled_effect(effect_id: str) -> Text:
    style = PD_EFFECT_STYLES.get(effect_id, "white")
    return Text(effect_id, style=style)


def join_effects(effect_ids: list[str]) -> Text:
    t = Text()
    for i, eid in enumerate(effect_ids):
        if i:
            t.append(", ", style="dim")
        t.append_text(styled_effect(eid))
    return t


def colorize_effect_tokens(s: str) -> Text:
    """
    Replace any known PD effect IDs found in a string with styled Text.
    Safe to use on arbitrary explanation/rationale lines.
    """
    out = Text()
    pos = 0
    for m in _EFFECT_TOKEN_RE.finditer(s):
        token = m.group(0)
        if token in PD_EFFECT_STYLES:
            if m.start() > pos:
                out.append(s[pos : m.start()])
            out.append_text(styled_effect(token))
            pos = m.end()
    if pos < len(s):
        out.append(s[pos:])
    return out


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

    console = _mk_console()
    table = Table(title="Interaction Summary (pairwise)", show_lines=False)

    # Let Pair wrap
    table.add_column("Pair", overflow="fold", no_wrap=False)
    # Severity
    table.add_column("Severity", justify="center", no_wrap=True)
    # Class
    table.add_column("Class", justify="center", no_wrap=True)
    table.add_column("Domains", justify="center", no_wrap=True)
    table.add_column("PK hits", justify="right", no_wrap=True)
    table.add_column("PD hits", justify="right", no_wrap=True)

    view = rows[:top] if top and top > 0 else rows
    for r in view:
        row_style = _table_style(r.severity, r.rule_class)

        sev_text = Text(r.severity, style=row_style)
        class_text = Text(r.rule_class, style=row_style)
        pair_text = Text(r.pair, style=row_style)  # optional

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
    """
    Rich details renderer used by `--format rich --details`.

    Important: build the panel body as Rich Text so we can colorize effect IDs.
    """
    console = _mk_console()

    for rep in reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name

        sev = str(rep.overall_severity.value).lower()
        cls = str(rep.overall_rule_class.value).lower()

        sev_text_style = _SEV_STYLE.get(sev, "bold")
        border_style = _border_style_for_severity(sev)

        title = Text(f"{d1} + {d2}", style=sev_text_style)

        body = Text()
        body.append(f"Overall: severity={sev} | class={cls}\n\n")

        # PD effects (by drug) - colored
        if getattr(facts, "pd_effects", None):
            body.append("PD effects (by drug):\n")
            for drug_id in sorted(facts.pd_effects):
                effects = facts.pd_effects[drug_id]
                # effects are RuleHit-adjacent objects
                try:
                    effect_ids = sorted({e.effect_id for e in effects})
                except AttributeError:
                    # if dicts sneak in
                    effect_ids = sorted({e["effect_id"] for e in effects})
                body.append(f"- {drug_id}: ")
                body.append_text(join_effects(effect_ids))
                body.append("\n")
            body.append("\n")

        if rep.pk_hits:
            body.append("PK section (directional):\n")
            if rep.pk_summary:
                body.append(f"PK summary: {rep.pk_summary}\n")
            for h in rep.pk_hits:
                A = facts.drugs[h.inputs["A"]].generic_name
                B = facts.drugs[h.inputs["B"]].generic_name
                body.append("- ")
                body.append_text(badge(h.severity.value, h.rule_class.value))
                body.append(f" {h.name}\n")
                body.append(f"  Affected: {A} | Interacting: {B}\n")

                tmpl = templates.get(h.rule_id, "")
                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    body.append("  Explanation: ")
                    ex = render_explanation(tmpl, facts, h)
                    body.append_text(colorize_effect_tokens(ex))
                    body.append("\n")

                rat = render_rationale(facts, h)
                if rat:
                    body.append("  Rationale:\n")
                    for line in rat.splitlines():
                        if line.strip():
                            body.append("   ")
                            body.append_text(colorize_effect_tokens(line.strip()))
                            body.append("\n")

                if h.actions:
                    body.append("  Suggested actions:\n")
                    for a in h.actions:
                        body.append(f"   - {a}\n")

                body.append("\n")

        if rep.pd_hits:
            body.append("PD section (shared domain):\n")
            for h in rep.pd_hits:
                body.append("- ")
                body.append_text(badge(h.severity.value, h.rule_class.value))
                body.append(f" {h.name}\n")

                tmpl = templates.get(h.rule_id, "")
                tmpl = templates.get(h.rule_id, "")
                if tmpl:
                    body.append("  Explanation: ")
                    ex = render_explanation(tmpl, facts, h)
                    body.append_text(colorize_effect_tokens(ex))
                    body.append("\n")

                rat = render_rationale(facts, h)
                if rat:
                    body.append("  Rationale:\n")
                    for line in rat.splitlines():
                        if line.strip():
                            body.append("   ")
                            body.append_text(colorize_effect_tokens(line.strip()))
                            body.append("\n")

                if h.actions:
                    body.append("  Suggested actions:\n")
                    for a in h.actions:
                        body.append(f"   - {a}\n")

                body.append("\n")

        if not body.plain.strip():
            body = Text("(No details.)", style="dim")

        console.print(
            Panel(
                body,
                title=title,
                border_style=border_style,
                expand=False,
            )
        )