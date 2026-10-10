"""Public-facing result summaries.

This module converts internal/debug mechanism objects into a smaller
end-user-facing summary shape.

It intentionally avoids exposing pipeline internals such as aggregate members,
evidence traces, arbitration details, policy results, or scored concerns.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from core.mechanisms.aggregate_evidence import (
    EVIDENCE_STATUS_COMPLETE,
    EVIDENCE_STATUS_NOT_APPLICABLE,
)
from core.mechanisms.aggregate_summary import AggregateConcernSummary
from core.mechanisms.aggregation import (
    AGGREGATE_OBJECT_EXPOSURE_DECREASE,
    AGGREGATE_OBJECT_EXPOSURE_INCREASE,
    AGGREGATE_SAFETY_CONCERN,
    AGGREGATE_SHARED_PD_EFFECT,
    AGGREGATE_TOLERABILITY_CONCERN,
)
from core.mechanisms.candidates import (
    CANDIDATE_ABSORPTION_INTERFERENCE,
    CANDIDATE_PD_SHARED_EFFECT,
)
from core.mechanisms.effect_labels import (
    PUBLIC_EFFECT_LABELS,
    effect_display_label,
)
from core.mechanisms.finding_identity import PDFindingIdentity, PKFindingIdentity
from core.mechanisms.pipeline import MechanismPipelineResult
from core.mechanisms.registry import (
    MECHANISM_ABSORPTION_INTERFERENCE,
    MECHANISM_ABSORPTION_SUSCEPTIBLE,
)
from core.mechanisms.rule_coverage import pd_rule_identity, pk_rule_identity
from core.models import PairReport, RuleHit

RESULT_SOURCE_AGGREGATE = "aggregate_summary"
RESULT_SOURCE_RULE = "rule_hit"

EVIDENCE_LABEL_NOT_AVAILABLE = "not_available"
EVIDENCE_LABEL_LEGACY_RULE = "rule_engine"

@dataclass(frozen=True)
class ResultSummary:
    """Small public summary suitable for future UI/default output."""

    source: str
    title: str
    drugs: tuple[str, ...]
    concern_type: str
    severity_label: str
    evidence_label: str
    explanation: str


def build_public_result_summaries(
    pipeline: MechanismPipelineResult,
    pair_reports: list[PairReport] | None = None,
) -> list[ResultSummary]:
    """Build public summaries from aggregate summaries and pair rule hits."""
    public_aggregate_summaries = _consolidate_public_aggregate_summaries(
        list(pipeline.aggregate_concern_summaries),
    )
    if pair_reports:
        public_aggregate_summaries = _reconcile_absorption_summaries(
            public_aggregate_summaries, pipeline, pair_reports
        )
        public_aggregate_summaries = _reconcile_pk_summaries(
            public_aggregate_summaries, pair_reports
        )
        public_aggregate_summaries = _reconcile_pd_summaries(
            public_aggregate_summaries, pair_reports
        )
    summaries = [
        aggregate_summary_to_result_summary(summary)
        for summary in public_aggregate_summaries
    ]

    if pair_reports:
        summaries.extend(
            build_legacy_rule_result_summaries(pair_reports)
        )

    return dedupe_result_summaries(summaries)


def _reconcile_pk_summaries(
    summaries: list[AggregateConcernSummary],
    pair_reports: list[PairReport],
) -> list[AggregateConcernSummary]:
    """Hide an exposure aggregate only when every member has a matching rule.

    Aggregates combine targets and precipitants for the same affected drug.
    Keeping a partly covered aggregate preserves the uncovered mechanism.
    The original pipeline and its evidence remain available in detail.
    """
    covered: set[PKFindingIdentity] = set()
    for report in pair_reports:
        for hit in report.pk_hits:
            identity = pk_rule_identity(report, hit)
            if identity is not None:
                covered.add(identity)

    return [
        summary
        for summary in summaries
        if not (
            not _has_evidence_limitation(summary)
            and summary.aggregate.aggregate_type
            in {AGGREGATE_OBJECT_EXPOSURE_INCREASE, AGGREGATE_OBJECT_EXPOSURE_DECREASE}
            and summary.aggregate.members
            and all(
                (identity := PKFindingIdentity.from_policy(member)) is not None
                and identity in covered
                for member in summary.aggregate.members
            )
        )
    ]


def _reconcile_pd_summaries(
    summaries: list[AggregateConcernSummary],
    pair_reports: list[PairReport],
) -> list[AggregateConcernSummary]:
    """Prefer matching curated pair rules for fully covered shared PD effects."""
    covered: set[PDFindingIdentity] = set()
    for report in pair_reports:
        for hit in report.pd_hits:
            identity = pd_rule_identity(report, hit)
            if identity is not None:
                covered.add(identity)

    return [
        summary
        for summary in summaries
        if not (
            not _has_evidence_limitation(summary)
            and summary.aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT
            and summary.aggregate.effect_id is not None
            and summary.aggregate.members
            and all(
                member.candidate_type == CANDIDATE_PD_SHARED_EFFECT
                and (identity := PDFindingIdentity.from_policy(member)) is not None
                and identity.effect_id == summary.aggregate.effect_id
                and identity in covered
                for member in summary.aggregate.members
            )
        )
    ]


def _has_evidence_limitation(summary: AggregateConcernSummary) -> bool:
    evidence = summary.evidence_summary
    return (
        summary.evidence_conflict_level != "none"
        or (
            evidence is not None
            and evidence.overall_evidence_status
            not in {EVIDENCE_STATUS_COMPLETE, EVIDENCE_STATUS_NOT_APPLICABLE}
        )
    )


def _reconcile_absorption_summaries(
    summaries: list[AggregateConcernSummary],
    pipeline: MechanismPipelineResult,
    pair_reports: list[PairReport],
) -> list[AggregateConcernSummary]:
    """Prefer a curated rule when it covers the same absorption evidence.

    Mixed-mechanism aggregates remain visible to avoid concealing a distinct
    exposure concern. Mechanism pipeline results and evidence are unchanged.
    """
    rule_pairs = {
        (frozenset((report.drug_1, report.drug_2)), hit.rule_id)
        for report in pair_reports
        for hit in _pair_report_hits(report)
    }
    effects: dict[tuple[str, str, str | None], set[str]] = {}
    for effect in pipeline.effects:
        key = (effect.source_drug, effect.mechanism, effect.target)
        effects.setdefault(key, set()).update(effect.evidence_refs)
    covered_pairs: set[frozenset[str]] = set()
    for candidate in pipeline.candidates:
        if candidate.candidate_type != CANDIDATE_ABSORPTION_INTERFERENCE:
            continue
        agent_refs = effects.get(
            (
                candidate.precipitant_drug,
                MECHANISM_ABSORPTION_INTERFERENCE,
                candidate.target,
            ),
            set(),
        )
        object_refs = effects.get(
            (
                candidate.object_drug,
                MECHANISM_ABSORPTION_SUSCEPTIBLE,
                candidate.target,
            ),
            set(),
        )
        pair = frozenset((candidate.precipitant_drug, candidate.object_drug))
        if any((pair, rule_id) in rule_pairs for rule_id in agent_refs & object_refs):
            covered_pairs.add(pair)

    return [
        summary
        for summary in summaries
        if not (
            not _has_evidence_limitation(summary)
            and summary.aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_DECREASE
            and summary.aggregate.members
            and all(
                member.candidate_type == CANDIDATE_ABSORPTION_INTERFERENCE
                and frozenset(
                    (member.precipitant_drug, member.object_drug)
                ) in covered_pairs
                for member in summary.aggregate.members
            )
        )
    ]


def _consolidate_public_aggregate_summaries(
    summaries: list[AggregateConcernSummary],
) -> list[AggregateConcernSummary]:
    """Hide broad PD policy summaries already represented by shared effects.

    Safety/tolerability aggregate summaries are useful when they add a broader
    regimen-level concern. When every PD effect in one of those summaries is
    already represented by a shared-PD-effect summary for the same drug set and
    policy concern, the broad summary is redundant in public output.
    """
    shared_effects: set[tuple[str, tuple[str, ...], str]] = set()

    for summary in summaries:
        aggregate = summary.aggregate
        if (
            aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT
            and aggregate.effect_id
        ):
            shared_effects.add(
                (
                    aggregate.effect_id,
                    tuple(aggregate.drugs),
                    aggregate.policy_concern,
                )
            )

    out: list[AggregateConcernSummary] = []

    for summary in summaries:
        aggregate = summary.aggregate

        if aggregate.aggregate_type not in {
            AGGREGATE_SAFETY_CONCERN,
            AGGREGATE_TOLERABILITY_CONCERN,
        }:
            out.append(summary)
            continue

        effect_ids = {
            member.effect_id
            for member in aggregate.members
            if member.effect_id
        }

        if not effect_ids:
            out.append(summary)
            continue

        drugs = tuple(aggregate.drugs)
        fully_represented = all(
            (
                effect_id,
                drugs,
                aggregate.policy_concern,
            )
            in shared_effects
            for effect_id in effect_ids
        )

        if fully_represented:
            continue

        out.append(summary)

    return out


def aggregate_summary_to_result_summary(
    summary: AggregateConcernSummary,
) -> ResultSummary:
    """Convert one aggregate concern summary into a public result summary."""
    aggregate = summary.aggregate

    return ResultSummary(
        source=RESULT_SOURCE_AGGREGATE,
        title=_aggregate_summary_title(summary),
        drugs=tuple(aggregate.drugs),
        concern_type=aggregate.policy_concern,
        severity_label=_aggregate_severity_label(summary),
        evidence_label=_aggregate_evidence_label(summary),
        explanation=_public_explanation(
            summary.narrative
            or _aggregate_fallback_explanation(summary),
        ),
    )


def build_legacy_rule_result_summaries(
    pair_reports: list[PairReport],
) -> list[ResultSummary]:
    """Convert pair rule hits into public result summaries."""
    summaries = []

    for report in pair_reports:
        for hit in _pair_report_hits(report):
            summaries.append(
                legacy_rule_hit_to_result_summary(report, hit)
            )

    return summaries


def legacy_rule_hit_to_result_summary(
    report: PairReport,
    hit: RuleHit,
) -> ResultSummary:
    """Convert one pair rule hit into a public result summary."""
    return ResultSummary(
        source=RESULT_SOURCE_RULE,
        title=hit.name,
        drugs=_legacy_rule_drugs(report, hit),
        concern_type=_value(hit.domain),
        severity_label=_value(hit.severity),
        evidence_label=EVIDENCE_LABEL_LEGACY_RULE,
        explanation=_legacy_rule_explanation(report, hit),
    )


def result_summary_to_json_dict(summary: ResultSummary) -> dict[str, Any]:
    """Convert a public result summary to a JSON-safe dict."""
    return {
        "source": summary.source,
        "title": summary.title,
        "drugs": list(summary.drugs),
        "concern_type": summary.concern_type,
        "severity_label": summary.severity_label,
        "evidence_label": summary.evidence_label,
        "explanation": summary.explanation,
    }


def result_summaries_to_json_dicts(
    summaries: list[ResultSummary],
) -> list[dict[str, Any]]:
    """Convert public result summaries to JSON-safe dicts."""
    return [
        result_summary_to_json_dict(summary)
        for summary in summaries
    ]


def dedupe_result_summaries(
    summaries: list[ResultSummary],
) -> list[ResultSummary]:
    """Deduplicate public result summaries preserving first-seen order."""
    seen: set[tuple[str, str, tuple[str, ...], str]] = set()
    out = []

    for summary in summaries:
        key = (
            summary.source,
            summary.title,
            summary.drugs,
            summary.concern_type,
        )
        if key in seen:
            continue

        seen.add(key)
        out.append(summary)

    return out


def _aggregate_summary_title(summary: AggregateConcernSummary) -> str:
    aggregate = summary.aggregate

    if aggregate.aggregate_type == AGGREGATE_SHARED_PD_EFFECT:
        effect_id = aggregate.effect_id or aggregate.anchor
        effect_label = _effect_display_label(effect_id)
        return f"Shared {effect_label} concern"

    if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_INCREASE:
        return f"{aggregate.anchor} exposure increase concern"

    if aggregate.aggregate_type == AGGREGATE_OBJECT_EXPOSURE_DECREASE:
        return f"{aggregate.anchor} exposure decrease concern"

    if aggregate.effect_id:
        effect_label = _effect_display_label(aggregate.effect_id)
        return f"{effect_label} concern"

    return f"{aggregate.policy_concern} concern"


def _effect_display_label(effect_id: str | None) -> str:
    return effect_display_label(effect_id)

def _public_explanation(explanation: str) -> str:
    out = explanation

    for effect_id in sorted(PUBLIC_EFFECT_LABELS, key=len, reverse=True):
        effect_label = _effect_display_label(effect_id)
        out = out.replace(
            f"{effect_id}-related pharmacodynamic effect",
            _public_pd_effect_phrase(effect_id, effect_label),
        )
        out = _replace_public_effect_id(
            out,
            effect_id=effect_id,
            effect_label=effect_label,
        )

    return out


def _replace_public_effect_id(
    text: str,
    *,
    effect_id: str,
    effect_label: str,
) -> str:
    if effect_id == "bleeding":
        return re.sub(
            r"\bbleeding\b(?!\s+risk\b)",
            effect_label,
            text,
        )

    return text.replace(effect_id, effect_label)

def _public_pd_effect_phrase(effect_id: str, effect_label: str) -> str:
    if effect_label == effect_id:
        return f"{effect_label}-related pharmacodynamic effect"

    return f"{effect_label} pharmacodynamic effect"


def _aggregate_severity_label(summary: AggregateConcernSummary) -> str:
    severity = summary.severity_annotation

    if not severity or not severity.strongest_preliminary_severity:
        return "unspecified"

    return str(severity.strongest_preliminary_severity)


def _aggregate_evidence_label(summary: AggregateConcernSummary) -> str:
    evidence = summary.evidence_summary

    if not evidence or not evidence.overall_evidence_status:
        return EVIDENCE_LABEL_NOT_AVAILABLE

    return str(evidence.overall_evidence_status)


def _aggregate_fallback_explanation(
    summary: AggregateConcernSummary,
) -> str:
    aggregate = summary.aggregate
    drugs = _human_join(tuple(aggregate.drugs))

    return (
        f"{drugs} are grouped as a {aggregate.policy_concern}. "
        "This summary is educational and not diagnostic."
    )


def _pair_report_hits(report: PairReport) -> list[RuleHit]:
    return list(report.pk_hits or []) + list(report.pd_hits or [])


def _legacy_rule_drugs(
    report: PairReport,
    hit: RuleHit,
) -> tuple[str, ...]:
    inputs = hit.inputs or {}
    drugs = []

    for key in ("A", "B"):
        value = inputs.get(key)
        if isinstance(value, str) and value:
            drugs.append(value)

    if drugs:
        return tuple(dict.fromkeys(drugs))

    return (report.drug_1, report.drug_2)


def _legacy_rule_explanation(report: PairReport, hit: RuleHit) -> str:
    inputs = hit.inputs or {}
    mapping = {
        "A_name": str(inputs.get("A") or report.drug_1),
        "B_name": str(inputs.get("B") or report.drug_2),
    }
    mapping.update(
        (key, str(value))
        for key, value in inputs.items()
        if key not in {"A", "B"}
    )

    def render(text: str) -> str:
        for key, value in mapping.items():
            text = text.replace("{" + key + "}", value)
        return text

    if hit.rationale:
        return " ".join(render(str(item)) for item in hit.rationale if item)

    if hit.actions:
        actions = "; ".join(render(str(item)) for item in hit.actions if item)
        return f"Legacy rule action context: {actions}"

    return "Legacy rule summary. This summary is educational and not diagnostic."


def _human_join(items: tuple[str, ...]) -> str:
    if not items:
        return "The selected drugs"

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} and {items[1]}"

    return f"{', '.join(items[:-1])}, and {items[-1]}"


def _value(item) -> str:
    if hasattr(item, "value"):
        return str(item.value)

    return str(item)
