from __future__ import annotations


def build_patient_flags(args) -> dict[str, bool]:
    return {
        "qt_risk": args.qt_risk,
        "bleeding_risk": args.bleeding_risk,
    }