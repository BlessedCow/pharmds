from __future__ import annotations

DEFAULT_AGGREGATE_SUMMARY_LIMIT = 5


def resolve_aggregate_summary_limit(args) -> int | None:
    if args.top is None:
        return DEFAULT_AGGREGATE_SUMMARY_LIMIT

    if args.top == 0:
        return None

    return args.top