# dataclasses / pydantic models
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.enums import Domain, RuleClass, Severity


@dataclass(frozen=True)
class Drug:
    id: str
    generic_name: str
    drug_class: str | None
    therapeutic_index: str
    notes: str | None = None


@dataclass(frozen=True)
class EnzymeRole:
    enzyme_id: str
    role: str  # substrate/inhibitor/inducer
    strength: str | None = None  # weak/moderate/strong
    fraction_metabolized: float | None = None
    notes: str | None = None


@dataclass(frozen=True)
class TransporterRole:
    transporter_id: str
    role: str
    strength: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class PDEffect:
    effect_id: str
    direction: str  # increase/decrease
    magnitude: str  # low/medium/high
    mechanism_note: str | None = None


@dataclass
class Facts:
    drugs: dict[str, Drug] = field(default_factory=dict)
    enzyme_roles: dict[str, list[EnzymeRole]] = field(
        default_factory=dict
    )  # drug_id -> roles
    transporter_roles: dict[str, list[TransporterRole]] = field(default_factory=dict)
    pd_effects: dict[str, list[PDEffect]] = field(default_factory=dict)
    patient_flags: dict[str, bool] = field(default_factory=dict)


@dataclass
class RuleHit:
    rule_id: str
    name: str
    domain: Domain
    severity: Severity
    rule_class: RuleClass
    actions: list[str] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)
    references: list[dict[str, str]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class InteractionFinding:
    drug_a: str
    drug_b: str
    domain: Domain
    severity: Severity
    title: str
    summary: str
    explanation: str
    rule_hits: list[RuleHit] = field(default_factory=list)


@dataclass
class PKSummary:
    direction: str  # "increase" | "decrease" | "mixed"
    confidence: str  # "mechanistic" for now
    mechanisms: list[str]  # e.g. ["cyp", "pgp"]
    affected: list[str]  # drug_ids (the A-side affected drugs)


@dataclass
class PairReport:
    drug_1: str  # stable ordering by id
    drug_2: str
    overall_severity: Severity
    overall_rule_class: str  # keep as string or RuleClass
    pk_hits: list[RuleHit] = field(default_factory=list)
    pd_hits: list[RuleHit] = field(default_factory=list)
    pk_summary: PKSummary | None = None
