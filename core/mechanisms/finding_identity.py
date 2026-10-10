"""Typed identities for equivalent rule and mechanism findings."""

from __future__ import annotations

from dataclasses import dataclass

from core.mechanisms.policy import ConcernPolicyResult


@dataclass(frozen=True)
class PKFindingIdentity:
    object_drug: str
    precipitant_drug: str
    candidate_type: str
    target: str

    @classmethod
    def from_policy(cls, member: ConcernPolicyResult) -> PKFindingIdentity | None:
        if not member.target or not member.candidate_type:
            return None
        return cls(
            member.object_drug,
            member.precipitant_drug,
            member.candidate_type,
            member.target,
        )


@dataclass(frozen=True)
class PDFindingIdentity:
    drugs: frozenset[str]
    effect_id: str

    @classmethod
    def from_policy(cls, member: ConcernPolicyResult) -> PDFindingIdentity | None:
        if not member.effect_id or member.precipitant_drug == member.object_drug:
            return None
        return cls(
            frozenset((member.precipitant_drug, member.object_drug)),
            member.effect_id,
        )
