# enzyme names, effect types, severity bins

from __future__ import annotations

from enum import StrEnum


class TI(str, StrEnum):
    wide = "wide"
    moderate = "moderate"
    narrow = "narrow"


class Strength(StrEnum):
    weak = "weak"
    moderate = "moderate"
    strong = "strong"


class Role(StrEnum):
    substrate = "substrate"
    inhibitor = "inhibitor"
    inducer = "inducer"


class Severity(StrEnum):
    info = "info"
    caution = "caution"
    major = "major"
    contraindicated = "contraindicated"


class Domain(StrEnum):
    PK = "PK"
    PD = "PD"


class RuleClass(StrEnum):
    avoid = "avoid"
    adjust_monitor = "adjust_monitor"
    caution = "caution"
    info = "info"
