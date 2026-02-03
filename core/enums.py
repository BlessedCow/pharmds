# enzyme names, effect types, severity bins

from __future__ import annotations

from enum import Enum


class TI(str, Enum):
    wide = "wide"
    moderate = "moderate"
    narrow = "narrow"


class Strength(str, Enum):
    weak = "weak"
    moderate = "moderate"
    strong = "strong"


class Role(str, Enum):
    substrate = "substrate"
    inhibitor = "inhibitor"
    inducer = "inducer"


class Severity(str, Enum):
    info = "info"
    caution = "caution"
    major = "major"
    contraindicated = "contraindicated"


class Domain(str, Enum):
    PK = "PK"
    PD = "PD"


class RuleClass(str, Enum):
    avoid = "avoid"
    adjust_monitor = "adjust_monitor"
    caution = "caution"
    info = "info"
