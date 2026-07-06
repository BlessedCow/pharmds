from __future__ import annotations

DEFAULT_AGGREGATE_SUMMARY_LIMIT = 5


def build_patient_flags(args) -> dict[str, bool]:
    return {
        "qt_risk": args.qt_risk,
        "bleeding_risk": args.bleeding_risk,
    }


def resolve_aggregate_summary_limit(args) -> int | None:
    if args.top is None:
        return DEFAULT_AGGREGATE_SUMMARY_LIMIT

    if args.top == 0:
        return None

    return args.top