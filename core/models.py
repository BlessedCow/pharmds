# dataclasses / pydantic models
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from core.enums import Severity, Domain, RuleClass


@dataclass(frozen=True)
class Drug:
    id: str
    generic_name: str
    drug_class: Optional[str]
    therapeutic_index: str
    notes: Optional[str] = None

@dataclass(frozen=True)
class EnzymeRole:
    enzyme_id: str
    role: str  # substrate/inhibitor/inducer
    strength: Optional[str] = None  # weak/moderate/strong
    fraction_metabolized: Optional[float] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class TransporterRole:
    transporter_id: str
    role: str
    strength: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class PDEffect:
    effect_id: str
    direction: str  # increase/decrease
    magnitude: str  # low/medium/high
    mechanism_note: Optional[str] = None


@dataclass
class Facts:
    drugs: Dict[str, Drug] = field(default_factory=dict)
    enzyme_roles: Dict[str, List[EnzymeRole]] = field(default_factory=dict)        # drug_id -> roles
    transporter_roles: Dict[str, List[TransporterRole]] = field(default_factory=dict)
    pd_effects: Dict[str, List[PDEffect]] = field(default_factory=dict)
    patient_flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class RuleHit:
    rule_id: str
    name: str
    domain: Domain
    severity: Severity
    rule_class: RuleClass
    actions: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    rationale: List[str] = field(default_factory=list)
    references: List[Dict[str, str]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class InteractionFinding:
    drug_a: str
    drug_b: str
    domain: Domain
    severity: Severity
    title: str
    summary: str
    explanation: str
    rule_hits: List[RuleHit] = field(default_factory=list)

@dataclass
class PKSummary:
    direction: str            # "increase" | "decrease" | "mixed"
    confidence: str           # "mechanistic" for now
    mechanisms: List[str]     # e.g. ["cyp", "pgp"]
    affected: List[str]       # drug_ids (the A-side affected drugs)

@dataclass
class PairReport:
    drug_1: str                 # stable ordering by id
    drug_2: str
    overall_severity: Severity
    overall_rule_class: str     # keep as string or RuleClass
    pk_hits: List[RuleHit] = field(default_factory=list)
    pd_hits: List[RuleHit] = field(default_factory=list)
    pk_summary: Optional[PKSummary] = None