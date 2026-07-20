from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from core.pk_timing.models import PharmacokineticTiming
from core.pk_timing.resolver import resolve_pk_timing
from core.pk_timing.serialize import serialize_pk_timing


def build_pk_timing_context(
    drug_ids: Iterable[str],
    *,
    route: str | None = None,
    release_type: str | None = None,
    data: Iterable[PharmacokineticTiming] | None = None,
) -> list[dict[str, Any]]:
    context = []

    for drug_id in drug_ids:
        timing = _resolve_timing(
            drug_id,
            route=route,
            release_type=release_type,
            data=data,
        )

        context.append(
            {
                "drug_id": drug_id,
                "timing": serialize_pk_timing(timing),
            }
        )

    return context


def _resolve_timing(
    drug_id: str,
    *,
    route: str | None,
    release_type: str | None,
    data: Iterable[PharmacokineticTiming] | None,
) -> PharmacokineticTiming | None:
    if data is None:
        return resolve_pk_timing(
            drug_id,
            route=route,
            release_type=release_type,
        )

    return resolve_pk_timing(
        drug_id,
        route=route,
        release_type=release_type,
        data=data,
    )
