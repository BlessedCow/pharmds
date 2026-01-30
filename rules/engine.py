# rule evaluation + trace
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.enums import Domain, Severity, RuleClass
from core.models import Facts, RuleHit
from data.loaders import load_transporters



@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    domain: Domain
    severity: Severity
    rule_class: RuleClass
    logic: Dict[str, Any]
    explanation_template: str
    references: List[Dict[str, str]]
    # Defaults last
    actions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

TRANSPORTERS = load_transporters()

def rule_mechanisms(rule: Rule) -> List[str]:
    """
    Infer mechanism tags from a rule's logic block.
    Used for CLI filtering (CYP vs P-gp vs PD) without hardcoding rule IDs.
    """
    L = rule.logic or {}
    out: List[str] = []

    if "enzyme" in L:
        out.append("cyp")

    if "transporter" in L:
        t = (L.get("transporter") or {})
        t_id = t.get("id")
        t_family = t.get("family")

        # Support both id-based and family-based transporter rules
        if t_id == "P-gp" or t_family == "ABCB1":
            out.append("pgp")

    if "pd_overlap" in L:
        out.append("pd")

    return out


def load_rules(rule_dir: Path) -> List[Rule]:
    rules: List[Rule] = []
    for p in sorted(rule_dir.glob("*.json")):
        raw = json.loads(p.read_text(encoding="utf-8"))
        rules.append(
            Rule(
                id=raw["id"],
                name=raw["name"],
                domain=Domain(raw["domain"]),
                severity=Severity(raw["severity"]),
                rule_class=RuleClass(raw.get("rule_class", "caution")),
                logic=raw["logic"],
                explanation_template=raw["explanation_template"],
                references=raw.get("references", []),
                actions=raw.get("actions", []),
                tags=raw.get("tags", []),
            )
        )
    return rules

def _strength_ok(actual: Optional[str], required: Optional[str], allowed: Optional[List[str]] = None) -> bool:
    if required is None and not allowed:
        return True

    if actual is None:
        return False

    if allowed:
        return actual in allowed

    return actual == required



def _drug_has_enzyme_role(
    facts: Facts,
    drug_id: str,
    enzyme_id: str,
    role: str,
    strength: Optional[str] = None,
    strength_in: Optional[List[str]] = None,
) -> bool:
    for r in facts.enzyme_roles.get(drug_id, []):
        if r.enzyme_id != enzyme_id:
            continue
        if r.role != role:
            continue
        if not _strength_ok(r.strength, strength, strength_in):
            continue
        return True
    return False

def _drug_has_transporter_role(
    facts: Facts,
    drug_id: str,
    transporter_id: str,
    role: str,
    strength: Optional[str] = None,
    strength_in: Optional[List[str]] = None,
) -> bool:
    for r in facts.transporter_roles.get(drug_id, []):
        if r.transporter_id != transporter_id:
            continue
        if r.role != role:
            continue
        if not _strength_ok(r.strength, strength, strength_in):
            continue
        return True
    return False


def _drug_has_pd_effect(facts: Facts, drug_id: str, effect_id: str, min_magnitude: Optional[str] = None) -> bool:
    order = {"low": 1, "medium": 2, "high": 3}
    for e in facts.pd_effects.get(drug_id, []):
        if e.effect_id != effect_id:
            continue
        if min_magnitude is None:
            return True
        if order.get(e.magnitude, 0) >= order.get(min_magnitude, 0):
            return True
    return False


def _ti_is(facts: Facts, drug_id: str, ti: str) -> bool:
    d = facts.drugs.get(drug_id)
    return bool(d and d.therapeutic_index == ti)


def _patient_flag(facts: Facts, flag: str) -> bool:
    return bool(facts.patient_flags.get(flag, False))

def _transporter_ids_for_family(family: str) -> List[str]:
    ids: List[str] = []

    # Case 1: TRANSPORTERS is a dict
    if isinstance(TRANSPORTERS, dict):
        for t_id, t in TRANSPORTERS.items():
            # t might be a dict (new) OR a string (old)
            if isinstance(t, dict):
                if (t.get("family") or "") == family:
                    ids.append(t_id)

        return ids

    # Case 2: TRANSPORTERS is a list
    for t in TRANSPORTERS:
        if isinstance(t, dict) and (t.get("family") or "") == family:
            t_id = t.get("id")
            if t_id:
                ids.append(t_id)

    return ids

def evaluate_rule(rule: Rule, facts: Facts, a: str, b: str) -> Optional[RuleHit]:
    """
    Evaluate a single rule for ordered pair (A=a, B=b).
    Rules are written assuming A is the affected drug and B is the interacting drug.
    """
    L = rule.logic
    inputs: Dict[str, Any] = {"A": a, "B": b}

    # Enzyme pattern
    if "enzyme" in L:
        enzyme_id = L["enzyme"]["id"]
        inputs["enzyme_id"] = enzyme_id

        a_role = L["enzyme"]["A_role"]
        b_role = L["enzyme"]["B_role"]

        a_ok = _drug_has_enzyme_role(facts, a, enzyme_id, a_role)
        b_ok = _drug_has_enzyme_role(
            facts,
            b,
            enzyme_id,
            b_role,
            strength=L["enzyme"].get("B_strength"),
            strength_in=L["enzyme"].get("B_strength_in"),
        )
        if not (a_ok and b_ok):
            return None

    # Transporter pattern
    if "transporter" in L:
        t_block = L["transporter"]
        t_id = t_block.get("id")
        t_family = t_block.get("family")

        if t_id:
            t_ids = [t_id]
            inputs["transporter_id"] = t_id
        elif t_family:
            t_ids = _transporter_ids_for_family(t_family)
            inputs["transporter_family"] = t_family
        else:
            return None

        a_role = t_block["A_role"]
        b_role = t_block["B_role"]

        a_ok = any(_drug_has_transporter_role(facts, a, tid, a_role) for tid in t_ids)
        b_ok = any(
            _drug_has_transporter_role(
                facts,
                b,
                tid,
                b_role,
                strength=t_block.get("B_strength"),
                strength_in=t_block.get("B_strength_in"),
            )
            for tid in t_ids
        )
        if not (a_ok and b_ok):
            return None

    # PD overlap pattern
    if "pd_overlap" in L:
        eff = L["pd_overlap"]["effect_id"]
        inputs["effect_id"] = eff
        min_mag = L["pd_overlap"].get("min_magnitude")
        if not (_drug_has_pd_effect(facts, a, eff, min_mag) and _drug_has_pd_effect(facts, b, eff, min_mag)):
            return None

        # Prevent symmetric duplicates for PD rules
        if a > b:
            return None

    # Therapeutic index guard
    if "A_ti" in L:
        if not _ti_is(facts, a, L["A_ti"]):
            return None

    # Patient flags
    if "requires_patient_flag" in L:
        if not _patient_flag(facts, L["requires_patient_flag"]):
            return None

    rationale = L.get("rationale", [])
    return RuleHit(
        rule_id=rule.id,
        name=rule.name,
        domain=rule.domain,
        severity=rule.severity,
        rule_class=rule.rule_class,
        actions=rule.actions,
        tags=rule.tags,
        inputs=inputs,
        rationale=rationale,
        references=rule.references,
    )


def evaluate_all(rules: List[Rule], facts: Facts, drug_ids: List[str]) -> List[RuleHit]:
    hits: List[RuleHit] = []
    ordered = list(dict.fromkeys(drug_ids))  # de-dupe preserving order

    for i in range(len(ordered)):
        for j in range(i + 1, len(ordered)):
            x = ordered[i]
            y = ordered[j]

            # Evaluate both directions so directional PK rules can match
            for a, b in ((x, y), (y, x)):
                for rule in rules:
                    hit = evaluate_rule(rule, facts, a, b)
                    if hit:
                        hits.append(hit)

    return hits