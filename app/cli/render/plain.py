from __future__ import annotations

from core.evidence.completeness import (
    BACKFILL_PRIORITY_CONFIDENCE,
    BACKFILL_PRIORITY_CONFLICT,
    BACKFILL_PRIORITY_MISSING,
    BACKFILL_PRIORITY_UNDETERMINED,
    GAP_CLASSIFICATIONS,
)
from core.evidence.human_rendering import (
    build_human_evidence_lines_for_rule_hit,
)
from core.evidence.loader import get_source_by_id
from core.mechanisms.effect_labels import (
    PUBLIC_EFFECT_LABELS,
    effect_display_label,
)
from core.mechanisms.result_summary import ResultSummary
from core.models import Facts
from reasoning.explain import render_explanation, render_rationale
from reasoning.rationale import action_rationale, severity_rationale

DEFAULT_AGGREGATE_SUMMARY_LIMIT = 5
DEFAULT_PUBLIC_RESULT_SUMMARY_LIMIT = 5
PLAIN_EMPTY_DETAILS_MESSAGE = "No pairwise detail rows to display."
PLAIN_AGGREGATE_HINT_MESSAGE = (
    "Use --show-aggregate-summaries to inspect mechanism-level aggregate concerns."
)

def _format_public_summary_label(value: object) -> str:
    text = str(value or "").strip()

    if not text:
        return "Not available"

    labels = {
        "high_caution": "High caution",
        "not_available": "Not available",
        "legacy_rule": "Legacy rule",
        "not_applicable": "Not applicable",
    }

    return labels.get(text, text.replace("_", " ").capitalize())


def _enum_value(value: object) -> str:
    return str(getattr(value, "value", value))


def _is_gap_classification(classification: str) -> bool:
    return classification in GAP_CLASSIFICATIONS


def _format_effect_value(effect_id: str | None) -> str:
    if not effect_id:
        return "unspecified effect"

    label = effect_display_label(effect_id)
    if label == effect_id:
        return effect_id

    return f"{effect_id} ({label})"


def _format_effect_values(effect_ids: tuple[str, ...]) -> str:
    if not effect_ids:
        return "none"

    return ", ".join(_format_effect_value(effect_id) for effect_id in effect_ids)


def _format_text_values(values: tuple[str, ...]) -> str:
    if not values:
        return "none"

    return ", ".join(values)


def _format_evidence_conflict_reasons(values: tuple[str, ...]) -> str:
    if not values:
        return "none"

    labels = {
        "claim_disagreement": "claim disagreement",
        "confidence": "confidence limitations",
        "coverage": "coverage gaps",
        "source_mismatch": "mixed source types",
    }

    return ", ".join(
        labels.get(value, value.replace("_", " "))
        for value in values
    )


def _format_evidence_source_label(source_id: str) -> str:
    source = get_source_by_id(source_id)

    if not source:
        return source_id

    title = source.get("title") or source_id
    source_type = source.get("source_type")

    if source_type:
        return f"{title} ({source_type})"

    return str(title)


def _format_source_ids(source_ids: tuple[str, ...]) -> str:
    if not source_ids:
        return "none"

    noun = "source" if len(source_ids) == 1 else "sources"
    labels = [
        _format_evidence_source_label(source_id)
        for source_id in source_ids
    ]

    return f"{len(source_ids)} {noun}: " + ", ".join(labels)


def _public_pd_effect_phrase(effect_id: str, effect_label: str) -> str:
    if effect_label == effect_id:
        return f"{effect_label}-related pharmacodynamic effect"

    return f"{effect_label} pharmacodynamic effect"


def _format_public_effect_text(text: str) -> str:
    out = text

    for effect_id in sorted(PUBLIC_EFFECT_LABELS, key=len, reverse=True):
        effect_label = effect_display_label(effect_id)
        out = out.replace(
            f"{effect_id}-related pharmacodynamic effect",
            _public_pd_effect_phrase(effect_id, effect_label),
        )
        out = out.replace(effect_id, effect_label)

    return out


def _format_evidence_gap_item(item: dict) -> str:
    source_types = ", ".join(item.get("source_types") or ["no_source"])
    confidence = item.get("confidence_level") or "none"

    return (
        f"{item['drug_id']} -> {item['effect_id']}: "
        f"{item['classification']} "
        f"(coverage={item['coverage_status']}, "
        f"confidence={confidence}, "
        f"claims={item['claim_count']}, "
        f"source_types={source_types})"
    )


def _format_evidence_backfill_task(task: dict[str, object]) -> str:
    missing_source_types = task.get("missing_source_types") or []
    if not isinstance(missing_source_types, list):
        missing_source_types = []

    missing_sources = ", ".join(str(source) for source in missing_source_types)
    missing_sources = missing_sources or "none"
    confidence = task.get("confidence_level") or task.get("confidence_status")

    return (
        "- "
        f"[{task.get('priority')}] "
        f"{task.get('drug_id')} -> {task.get('effect_id')}: "
        f"{task.get('classification')} "
        f"(coverage={task.get('coverage_status')}, "
        f"confidence={confidence or 'none'}, "
        f"claims={task.get('claim_count')}, "
        f"missing_sources={missing_sources}). "
        f"{task.get('suggested_next_action')}"
    )


def _append_evidence_backfill_task_group(
    lines: list[str],
    title: str,
    grouped_tasks: object,
) -> None:
    lines.extend(["", title])

    if not isinstance(grouped_tasks, dict) or not grouped_tasks:
        lines.append("  none")
        return

    for key, tasks in sorted(grouped_tasks.items()):
        lines.append(f"  {key}:")

        if not isinstance(tasks, list):
            continue

        for task in tasks:
            if isinstance(task, dict):
                lines.append(f"    {_format_evidence_backfill_task(task)}")


def _append_evidence_backfill_plan(
    lines: list[str],
    report: dict,
) -> None:
    backfill_plan = report.get("backfill_plan") or {}
    if not isinstance(backfill_plan, dict):
        return

    tasks = backfill_plan.get("tasks") or []
    lines.extend(["", "Backfill planning report:"])

    if not tasks:
        lines.append("  No backfill tasks found.")
        return

    priority_counts = backfill_plan.get("priority_counts") or {}
    if not isinstance(priority_counts, dict):
        priority_counts = {}

    priority_order = (
        BACKFILL_PRIORITY_MISSING,
        BACKFILL_PRIORITY_CONFLICT,
        BACKFILL_PRIORITY_UNDETERMINED,
        BACKFILL_PRIORITY_CONFIDENCE,
    )

    lines.append(f"  Total backfill tasks: {backfill_plan.get('total_tasks', 0)}")
    lines.extend(["", "Priority counts:"])

    for priority in priority_order:
        count = priority_counts.get(priority, 0)
        if count:
            lines.append(f"  {priority}: {count}")

    lines.extend(["", "Prioritized tasks:"])

    for task in tasks:
        if isinstance(task, dict):
            lines.append(f"  {_format_evidence_backfill_task(task)}")

    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by priority:",
        backfill_plan.get("by_priority"),
    )
    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by PD effect:",
        backfill_plan.get("by_pd_effect"),
    )
    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by drug:",
        backfill_plan.get("by_drug"),
    )
    _append_evidence_backfill_task_group(
        lines,
        "Backfill tasks by missing source type:",
        backfill_plan.get("by_source_type"),
    )
    

def render_public_result_summaries(
    summaries: list[ResultSummary],
    top: int | None = DEFAULT_PUBLIC_RESULT_SUMMARY_LIMIT,
) -> str:
    """Render public result summaries for default plain CLI output."""
    if not summaries:
        return "No key interaction summaries."

    if top is not None and top > 0:
        visible_summaries = summaries[:top]
    else:
        visible_summaries = summaries

    hidden_count = len(summaries) - len(visible_summaries)
    lines = []

    for summary in visible_summaries:
        drugs = ", ".join(summary.drugs) if summary.drugs else "none"

        lines.append(f"- {summary.title}")
        lines.append(f"  drugs: {drugs}")
        lines.append(
            f"  concern_type: {_format_public_summary_label(summary.concern_type)}"
        )
        lines.append(
            f"  severity: {_format_public_summary_label(summary.severity_label)}"
        )
        lines.append(
            f"  evidence: {_format_public_summary_label(summary.evidence_label)}"
        )
        lines.append(f"  explanation: {summary.explanation}")
        lines.append("")

    if hidden_count > 0:
        noun = "summary" if hidden_count == 1 else "summaries"
        lines.append(
            f"... {hidden_count} key interaction {noun} hidden. "
            "Use --top 0 to show all."
        )

    return "\n".join(lines).rstrip()


def render_plain_regimen_summary(regimen_summary: dict) -> str:
      """Render regimen-level summary for default plain CLI output."""
      if not regimen_summary:
          return ""

      hit_counts = regimen_summary.get("hit_counts", {})
      flags = regimen_summary.get("regimen_flags", [])
      pd_stacks = regimen_summary.get("pd_stacks", [])
      top_pairs = regimen_summary.get("top_pairs", [])

      lines = [
          "Regimen Summary",
          f"overall_severity: {_enum_value(regimen_summary.get('overall_severity'))}",
          f"overall_class: {_enum_value(regimen_summary.get('overall_rule_class'))}",
      ]

      overview = regimen_summary.get("overview")
      if overview:
          lines.append(f"overview: {overview}")

      pairwise_summary = regimen_summary.get("pairwise_summary")
      if pairwise_summary:
          lines.append(f"pairwise_section: {pairwise_summary}")

      cumulative_summary = regimen_summary.get("cumulative_concern_summary")
      if cumulative_summary:
          lines.append(f"regimen_wide_section: {cumulative_summary}")

      lines.extend(
          [
              f"drugs: {regimen_summary.get('n_drugs', 0)}",
              (
                  "pairs_with_pairwise_hits: "
                  f"{regimen_summary.get('pair_count_with_hits', 0)}"
              ),
              (
                  "pairwise_hits: "
                  f"{hit_counts.get('total', 0)} "
                  f"(PK={hit_counts.get('pk', 0)}, PD={hit_counts.get('pd', 0)})"
              ),
              f"regimen_wide_flags: {len(flags)}",
          ]
      )

      if flags:
          lines.append("")
          lines.append("Regimen-wide educational flags:")
          for flag in flags[:5]:
              lines.append(f"- {flag.get('message', '')}")

      if pd_stacks:
          lines.append("")
          lines.append("Regimen-wide repeated PD concern domains:")
          for stack in pd_stacks[:5]:
              drug_names = ", ".join(
                  drug["drug_name"] for drug in stack.get("drugs", [])
              )
              lines.append(
                  f"- {stack['label']}: {stack['count']} drugs "
                  f"(max={stack['max_magnitude']}) - {drug_names}"
              )

      if top_pairs:
          lines.append("")
          lines.append("Pairwise concern highlights:")
          for pair in top_pairs[:3]:
              lines.append(
                  f"- {pair['drug_1']['name']} + {pair['drug_2']['name']}: "
                  f"{pair['severity']} | {pair['class']} "
                  f"({pair['total_hits']} hits)"
              )

      return "\n".join(lines)

def render_plain_pairwise_details(
      facts: Facts,
      pair_reports,
      templates: dict[str, str],
      *,
      show_evidence: bool = False,
  ) -> str:
      """Render full pairwise details for plain CLI output."""
      reports = list(pair_reports)
      lines: list[str] = ["Pairwise Details"]

      if not reports:
          lines.append(PLAIN_EMPTY_DETAILS_MESSAGE)
          lines.append(PLAIN_AGGREGATE_HINT_MESSAGE)
          return "\n".join(lines)

      for rep in reports:
          d1 = facts.drugs[rep.drug_1].generic_name
          d2 = facts.drugs[rep.drug_2].generic_name

          lines.append("=" * 80)
          lines.append(f"{d1} + {d2}")
          lines.append(
              f"Overall: severity={rep.overall_severity.value} | "
              f"class={rep.overall_rule_class.value}"
          )
          lines.append("")

          if rep.pk_hits:
              lines.append("PK section (directional):")
              if rep.pk_summary:
                  lines.append(f"PK summary: {rep.pk_summary}")
              for h in rep.pk_hits:
                  a_drug = facts.drugs[h.inputs["A"]].generic_name
                  b_drug = facts.drugs[h.inputs["B"]].generic_name
                  lines.append(
                      f"- [{h.severity.value} | {h.rule_class.value}] {h.name}"
                )
                  lines.append(f"  Affected: {a_drug} | Interacting: {b_drug}")

                  tmpl = templates.get(h.rule_id, "")
                  if tmpl:
                      ex = render_explanation(tmpl, facts, h)
                      lines.append(f"  Explanation: {ex}")

                  rat = render_rationale(facts, h)
                  if rat:
                      lines.append("  Rationale:")
                      for line in rat.splitlines():
                          lines.append(f"   {line}")

                  lines.append("  Severity rationale:")
                  lines.append(f"   {severity_rationale(h.severity)}")

                  lines.append("  Action rationale:")
                  lines.append(f"   {action_rationale(h.rule_class)}")

                  if h.actions:
                      lines.append("  Suggested actions:")
                      for action in h.actions:
                          lines.append(f"   - {action}")

                  lines.append("")

          if facts.pd_effects:
              lines.append("PD effects (by drug):")
              for drug_id, effects in facts.pd_effects.items():
                  effect_ids = sorted({effect.effect_id for effect in effects})
                  lines.append(f"- {drug_id}: {', '.join(effect_ids)}")
              lines.append("")

          if rep.pd_hits:
              lines.append("PD section (shared domain):")
              for h in rep.pd_hits:
                  lines.append(
                      f"- [{h.severity.value} | {h.rule_class.value}] {h.name}"
                  )

                  tmpl = templates.get(h.rule_id, "")
                  if tmpl:
                      ex = render_explanation(tmpl, facts, h)
                      lines.append(f"  Explanation: {ex}")

                  rat = render_rationale(facts, h)
                  if rat:
                      lines.append("  Rationale:")
                      for line in rat.splitlines():
                          lines.append(f"   {line}")

                  lines.append("  Severity rationale:")
                  lines.append(f"   {severity_rationale(h.severity)}")

                  lines.append("  Action rationale:")
                  lines.append(f"   {action_rationale(h.rule_class)}")

                  if h.actions:
                      lines.append("  Suggested actions:")
                      for action in h.actions:
                          lines.append(f"   - {action}")

                  if show_evidence:
                      evidence_lines = build_human_evidence_lines_for_rule_hit(
                          facts,
                          h,
                      )
                      if evidence_lines:
                          lines.append("  Evidence:")
                          for line in evidence_lines:
                              lines.append(f"   {line}")

                  lines.append("")

          refs: list[dict[str, str]] = []
          for h in (rep.pk_hits or []) + (rep.pd_hits or []):
              refs.extend(h.references)

          uniq = {
              (r.get("source", ""), r.get("citation", ""), r.get("url", ""))
              for r in refs
          }
          if uniq:
              lines.append("References (rule-level):")
              for source, citation, url in sorted(uniq):
                  if url:
                      lines.append(f"- {source}: {citation} ({url})")
                  else:
                      lines.append(f"- {source}: {citation}")
              lines.append("")

      lines.append("=" * 80)
      lines.append(
          "Footer: This output is an educational mechanistic explanation. "
          "Verify with primary sources."
      )

      return "\n".join(lines)


def render_aggregate_concern_summaries(
    pipeline,
    top: int | None = DEFAULT_AGGREGATE_SUMMARY_LIMIT,
):
    """Render joined aggregate concern summaries for CLI debug output."""
    summaries = list(pipeline.aggregate_concern_summaries)

    if not summaries:
        return "No aggregate concern summaries."

    if top is not None and top > 0:
        visible_summaries = summaries[:top]
    else:
        visible_summaries = summaries

    lines = []

    for summary in visible_summaries:
        aggregate = summary.aggregate
        severity = summary.severity_annotation
        evidence = summary.evidence_summary
        drugs = ", ".join(aggregate.drugs) if aggregate.drugs else "none"
        targets = ", ".join(aggregate.targets) if aggregate.targets else "none"
        effect_id = aggregate.effect_id or aggregate.anchor

        lines.append("")
        lines.append(f"- {aggregate.aggregate_type}: {aggregate.anchor}")
        lines.append(f"  drugs: {drugs}")
        lines.append(f"  effect: {_format_effect_value(effect_id)}")
        lines.append(f"  targets: {targets}")
        lines.append(f"  policy_concern: {aggregate.policy_concern}")

        if severity:
            lines.append(
                "  strongest_preliminary_severity: "
                + str(severity.strongest_preliminary_severity)
            )
        else:
            lines.append("  strongest_preliminary_severity: none")

        if evidence:
            evidence_status = evidence.overall_evidence_status
            evidence_gap_count = evidence.evidence_gap_count
            evidence_claim_count = evidence.evidence_claim_count
            evidence_source_ids = evidence.evidence_source_ids
        else:
            evidence_status = "none"
            evidence_gap_count = 0
            evidence_claim_count = 0
            evidence_source_ids = ()

        lines.append(f"  evidence_status: {evidence_status}")
        lines.append(f"  evidence_gap_count: {evidence_gap_count}")
        lines.append(f"  evidence_claim_count: {evidence_claim_count}")
        lines.append(
            "  evidence_source_count: "
            + str(len(evidence_source_ids))
        )
        lines.append(
            "  evidence_sources: "
            + _format_source_ids(evidence_source_ids)
        )

        if summary.patient_risk_modifiers:
            lines.append(
                "  patient_risk_modifiers: "
                + ", ".join(summary.patient_risk_modifiers)
            )
        else:
            lines.append("  patient_risk_modifiers: none")

        if summary.risk_context:
            lines.append("  risk_context: " + summary.risk_context)

        lines.append(
            "  evidence_conflict_level: "
            + str(summary.evidence_conflict_level)
        )

        if summary.evidence_conflict_message:
            lines.append(
                "  evidence_conflict_message: "
                + summary.evidence_conflict_message
            )

        if summary.evidence_conflict_source_ids:
            lines.append(
                "  evidence_conflict_source_ids: "
                + ", ".join(summary.evidence_conflict_source_ids)
            )

        if summary.evidence_conflict_trace_types:
            lines.append(
                "  evidence_conflict_trace_types: "
                + ", ".join(summary.evidence_conflict_trace_types)
            )

        if summary.evidence_conflict_reasons:
            lines.append(
                "  evidence_conflict_reasons: "
                + _format_evidence_conflict_reasons(
                    summary.evidence_conflict_reasons
                )
            )
        
        if summary.narrative:
            lines.append(
                "  narrative: "
                + _format_public_effect_text(summary.narrative)
            )

    hidden_count = len(summaries) - len(visible_summaries)
    if hidden_count > 0:
        noun = "summary" if hidden_count == 1 else "summaries"
        lines.append("")
        lines.append(
            f"... {hidden_count} aggregate concern {noun} hidden. "
            "Use --top 0 to show all."
        )

    return "\n".join(lines)


def render_aggregate_evidence_summary(pipeline):
    """Render aggregate evidence summaries for CLI debug output."""
    if not pipeline.aggregate_evidence_summaries:
        return "No aggregate evidence summaries."

    lines = []

    for summary in pipeline.aggregate_evidence_summaries:
        aggregate = summary.aggregate
        drugs = ", ".join(aggregate.drugs)
        effect_id = aggregate.effect_id or aggregate.anchor

        lines.append("")
        lines.append(
            f"- {aggregate.aggregate_type}: {aggregate.anchor}"
            f" | policy_concern={aggregate.policy_concern}"
            f" | drugs={drugs}"
            f" | effect={_format_effect_value(effect_id)}"
        )
        lines.append(
            "  overall_evidence_status: "
            + str(summary.overall_evidence_status)
        )
        lines.append(
            "  evidence_trace_count: "
            + str(summary.evidence_trace_count)
        )

        lines.append(
            "  evidence_trace_types: "
            + _format_text_values(summary.evidence_trace_types)
        )
        lines.append(
            "  evidence_effect_ids: "
            + _format_effect_values(summary.evidence_effect_ids)
        )

        lines.append(
            "  evidence_statuses: "
            + _format_text_values(summary.evidence_statuses)
        )

        lines.append(
            "  evidence_gap_count: "
            + str(summary.evidence_gap_count)
        )
        lines.append(
            "  evidence_claim_count: "
            + str(summary.evidence_claim_count)
        )

        lines.append(
            "  evidence_sources: "
            + _format_source_ids(summary.evidence_source_ids)
        )
        lines.append(
            "  evidence_source_types: "
            + _format_text_values(summary.evidence_source_types)
        )
        lines.append(
            "  evidence_conflict_reasons: "
            + _format_evidence_conflict_reasons(
                summary.evidence_conflict_reasons
            )
        )
        lines.append(
            "  member_without_evidence_trace_count: "
            + str(summary.member_without_evidence_trace_count)
        )

    return "\n".join(lines)


def render_evidence_gap_report(
    report: dict,
    *,
    show_complete: bool = False,
) -> str:
    """Render selected-drug PD evidence coverage gaps for CLI output."""
    lines = [
        "PD Effect Evidence Gaps",
        "",
        f"Total PD effects checked: {report['total_pd_effects']}",
        f"Missing/partial evidence rows: {report['gap_count']}",
        "",
        "Coverage counts:",
    ]

    for key, count in sorted(report["coverage_counts"].items()):
        lines.append(f"  {key}: {count}")

    lines.extend(["", "Confidence counts:"])
    for key, count in sorted(report["confidence_counts"].items()):
        lines.append(f"  {key}: {count}")

    def add_group(title: str, group: dict[str, list[dict]]) -> None:
        lines.extend(["", title])
        if not group:
            lines.append("  none")
            return

        for key, items in sorted(group.items()):
            visible_items = [
                item
                for item in items
                if show_complete
                or _is_gap_classification(item["classification"])
            ]
            if not visible_items:
                continue

            lines.append(f"  {key}:")
            for item in visible_items:
                lines.append(f"    - {_format_evidence_gap_item(item)}")

    add_group("Grouped by PD effect:", report["gaps_by_pd_effect"])
    add_group("Grouped by drug:", report["gaps_by_drug"])
    add_group("Grouped by source type:", report["gaps_by_source_type"])

    if show_complete:
        lines.extend(["", "Complete/moderate/high rows:"])
        complete_items = [
            item
            for item in report["items"]
            if not _is_gap_classification(item["classification"])
        ]
        if not complete_items:
            lines.append("  none")
        for item in complete_items:
            lines.append(f"  - {_format_evidence_gap_item(item)}")

    _append_evidence_backfill_plan(lines, report)

    return "\n".join(lines)

