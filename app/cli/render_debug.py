from __future__ import annotations

from core.mechanisms.debug import (
    DEBUG_MECHANISM_PIPELINE_LABEL,
    DEBUG_OLD_PAIRWISE_LABEL,
    DEBUG_PAIRWISE_MIGRATION_LABEL,
    format_debug_section_title,
    format_old_pairwise_rule_reports,
    format_pairwise_mechanism_concerns,
)
from core.mechanisms.effect_labels import effect_display_label
from core.mechanisms.pairwise_adapter import adapt_mechanism_pipeline_to_pairwise


def _format_effect_label_line(effect_id: str | None) -> str | None:
    if not effect_id:
        return None

    label = effect_display_label(effect_id)
    if label == effect_id:
        return None

    return f"  effect_label: {label}"


def render_severity_annotations(severity_annotations):
    """Render mechanism severity annotations for CLI debug output."""
    if not severity_annotations:
        return "No severity annotations."

    lines = []

    for annotation in severity_annotations:
        scored = annotation.scored

        lines.append(
            f"- {scored.precipitant_drug} + {scored.object_drug}"
            f" | effect={scored.effect_id}"
            f" | concern={scored.policy_concern}"
        )
        lines.append(f"  candidate_type: {scored.candidate_type}")
        lines.append(f"  confidence: {scored.confidence}")
        lines.append(f"  preliminary_severity: {annotation.preliminary_severity}")
        lines.append(f"  severity_reason: {annotation.severity_reason}")
        lines.append(f"  explanation: {scored.explanation}")

        if scored.related_effects:
            related_effects = sorted(
                {
                    effect.strip()
                    for effect_group in scored.related_effects
                    for effect in effect_group.split(",")
                    if effect.strip()
                }
            )
            lines.append("  related_effects: " + ", ".join(related_effects))

        if scored.related_targets:
            lines.append("  related_targets: " + ", ".join(scored.related_targets))

        lines.append("")

    return "\n".join(lines).rstrip()


def render_pairwise_migration_debug(pair_reports, pipeline) -> str:
    """Render old pairwise output beside pairwise-shaped mechanism output."""
    mechanism_concerns = adapt_mechanism_pipeline_to_pairwise(pipeline)

    lines = [
        DEBUG_PAIRWISE_MIGRATION_LABEL,
        "",
        format_debug_section_title(
            DEBUG_OLD_PAIRWISE_LABEL,
            "Rule Reports",
        ),
    ]

    old_lines = format_old_pairwise_rule_reports(list(pair_reports))
    if old_lines:
        lines.extend(f"- {line}" for line in old_lines)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            format_debug_section_title(
                DEBUG_MECHANISM_PIPELINE_LABEL,
                "Pairwise Adapter Concerns",
            ),
        ]
    )

    mechanism_lines = format_pairwise_mechanism_concerns(mechanism_concerns)
    if mechanism_lines:
        lines.extend(f"- {line}" for line in mechanism_lines)
    else:
        lines.append("- none")

    return "\n".join(lines)


def render_severity_comparison(pipeline):
    """Render comparison between aggregate concerns and aggregate severity."""
    if not pipeline.aggregate_severity_annotations:
        return "No aggregate severity annotations."

    lines = []

    for annotation in pipeline.aggregate_severity_annotations:
        aggregate = annotation.aggregate
        drugs = ", ".join(aggregate.drugs)
        effect_id = aggregate.effect_id or aggregate.anchor
        effect_label_line = _format_effect_label_line(effect_id)

        lines.append("")
        lines.append(
            f"- {aggregate.aggregate_type}: {aggregate.anchor}"
            f" | policy_concern={aggregate.policy_concern}"
            f" | drugs={drugs}"
            f" | effect={effect_id}"
        )
        if effect_label_line:
            lines.append(effect_label_line)
        lines.append(
            "  strongest_preliminary_severity: "
            + str(annotation.strongest_preliminary_severity)
        )

        if annotation.contributing_preliminary_severities:
            lines.append(
                "  contributing_preliminary_severities: "
                + ", ".join(annotation.contributing_preliminary_severities)
            )
        else:
            lines.append("  contributing_preliminary_severities: none")

        if annotation.severity_reasons:
            lines.append(
                "  severity_reason: " + " | ".join(annotation.severity_reasons)
                )
        else:
            lines.append("  severity_reason: no matching severity annotation")

    return "\n".join(lines)