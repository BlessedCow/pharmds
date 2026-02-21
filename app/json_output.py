from __future__ import annotations

from typing import Any

from core.models import Facts, PairReport, RuleHit
from reasoning.explain import render_explanation, render_rationale

SCHEMA_VERSION = "1.0"


def _val(x: Any) -> Any:
    """Convert enums-like objects to plain JSON-safe values."""
    if hasattr(x, "value"):
        return x.value
    return x


# Severity ordering: lowest risk first (info -> contraindicated)
# Adjust these strings if your enum values differ.
_SEV_RANK = {
    "info": 0,
    "minor": 1,
    "caution": 1,  # if you use 'caution' instead of 'minor'
    "moderate": 2,
    "major": 3,
    "contraindicated": 4,
}


def _sev_rank(sev: Any) -> int:
    s = _val(sev)
    if isinstance(s, str):
        return _SEV_RANK.get(s, 999)
    return 999


def _drug_name(facts: Facts, drug_id: str) -> str:
    return facts.drugs[drug_id].generic_name


def _ref_key(r: Any) -> tuple[str, str, str]:
    """
    References are typically dict-like with keys such as:
      source, citation, url
    but we tolerate anything.
    """
    if isinstance(r, dict):
        source = str(r.get("source", "") or "")
        citation = str(r.get("citation", "") or "")
        url = str(r.get("url", "") or "")
        return (source, citation, url)
    return (str(r), "", "")


def _sorted_list(xs: Any) -> list[Any]:
    if not xs:
        return []
    if isinstance(xs, list):
        return sorted(xs, key=lambda x: str(x))
    return [xs]


def _hit_to_dict(
    facts: Facts,
    h: RuleHit,
    templates: dict[str, str],
) -> dict[str, Any]:
    a_id = (h.inputs or {}).get("A")
    b_id = (h.inputs or {}).get("B")

    explanation = ""
    tmpl = templates.get(h.rule_id, "")
    if tmpl:
        explanation = render_explanation(tmpl, facts, h)

    rat = render_rationale(facts, h)
    rationale_lines = [ln.strip() for ln in rat.splitlines() if ln.strip()] if rat else []

    refs = list(h.references or [])
    refs_sorted = sorted(refs, key=_ref_key)

    out: dict[str, Any] = {
        "rule_id": h.rule_id,
        "name": h.name,
        "domain": _val(h.domain),
        "severity": _val(h.severity),
        "class": _val(h.rule_class),
        "inputs": dict(h.inputs or {}),
        "tags": _sorted_list(list(h.tags or [])),
        "explanation": explanation,
        "rationale": rationale_lines,
        "actions": _sorted_list(list(h.actions or [])),
        "references": refs_sorted,
    }

    # Convenience fields for UI/consumers (also deterministic)
    if isinstance(a_id, str) and a_id in facts.drugs:
        out["A"] = {"id": a_id, "name": _drug_name(facts, a_id)}
    if isinstance(b_id, str) and b_id in facts.drugs:
        out["B"] = {"id": b_id, "name": _drug_name(facts, b_id)}

    return out


def build_json_payload(
    *,
    facts: Facts,
    reports: list[PairReport],
    templates: dict[str, str],
    selected_domains: list[str],
    input_drug_names: list[str],
    patient_flags: dict[str, bool],
) -> dict[str, Any]:
    pairs_out: list[dict[str, Any]] = []

    for rep in reports:
        d1_id = rep.drug_1
        d2_id = rep.drug_2
        d1_name = _drug_name(facts, d1_id)
        d2_name = _drug_name(facts, d2_id)

        pk_hits = [_hit_to_dict(facts, h, templates) for h in (rep.pk_hits or [])]
        pd_hits = [_hit_to_dict(facts, h, templates) for h in (rep.pd_hits or [])]

        # Keep hit order stable even if upstream order changes:
        # sort by severity, then domain, then rule_id (and then A/B if present)
        def _hit_sort_key(hd: dict[str, Any]) -> tuple[int, str, str, str, str]:
            a = (hd.get("A") or {}).get("id", "")
            b = (hd.get("B") or {}).get("id", "")
            return (
                _sev_rank(hd.get("severity")),
                str(hd.get("domain", "")),
                str(hd.get("rule_id", "")),
                str(a),
                str(b),
            )

        pk_hits = sorted(pk_hits, key=_hit_sort_key)
        pd_hits = sorted(pd_hits, key=_hit_sort_key)

        pair_obj: dict[str, Any] = {
            "drug_1": {"id": d1_id, "name": d1_name},
            "drug_2": {"id": d2_id, "name": d2_name},
            "overall": {
                "severity": _val(rep.overall_severity),
                "class": _val(rep.overall_rule_class),
            },
            "pk": {
                "summary": rep.pk_summary,
                "hits": pk_hits,
            },
            "pd": {
                "hits": pd_hits,
            },
        }
        pairs_out.append(pair_obj)

    # Deterministic pair ordering:
    # (severity_rank, drug_1.id, drug_2.id)
    def _pair_sort_key(p: dict[str, Any]) -> tuple[int, str, str]:
        return (
            _sev_rank((p.get("overall") or {}).get("severity")),
            str((p.get("drug_1") or {}).get("id", "")),
            str((p.get("drug_2") or {}).get("id", "")),
        )

    pairs_out = sorted(pairs_out, key=_pair_sort_key)

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "input": {
            "drug_names": list(input_drug_names),
            "selected_domains": list(selected_domains),
            "patient_flags": dict(patient_flags),
        },
        "pairs": pairs_out,
    }
    return payload