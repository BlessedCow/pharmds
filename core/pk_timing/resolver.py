from __future__ import annotations

from collections.abc import Iterable

from core.pk_timing.data import PK_TIMING_DATA
from core.pk_timing.models import PharmacokineticTiming
from core.pk_timing.steady_state import estimate_steady_state


def resolve_pk_timing(
    drug_id: str,
    *,
    route: str | None = None,
    release_type: str | None = None,
    data: Iterable[PharmacokineticTiming] = PK_TIMING_DATA,
) -> PharmacokineticTiming | None:
    normalized_drug_id = _normalize_optional_value(drug_id)
    normalized_route = _normalize_optional_value(route)
    normalized_release_type = _normalize_optional_value(release_type)

    matches = [
        timing
        for timing in data
        if _normalize_optional_value(timing.drug_id) == normalized_drug_id
    ]

    if not matches:
        return None

    exact_match = _find_exact_match(
        matches,
        route=normalized_route,
        release_type=normalized_release_type,
    )
    if exact_match is not None:
        return _with_derived_steady_state(exact_match)

    route_match = _find_route_match(
        matches,
        route=normalized_route,
    )
    if route_match is not None:
        return _with_derived_steady_state(route_match)

    return _with_derived_steady_state(matches[0])


def _find_exact_match(
    matches: list[PharmacokineticTiming],
    *,
    route: str | None,
    release_type: str | None,
) -> PharmacokineticTiming | None:
    if route is None or release_type is None:
        return None

    for timing in matches:
        if (
            _normalize_optional_value(timing.route) == route
            and _normalize_optional_value(timing.release_type) == release_type
        ):
            return timing

    return None


def _find_route_match(
    matches: list[PharmacokineticTiming],
    *,
    route: str | None,
) -> PharmacokineticTiming | None:
    if route is None:
        return None

    for timing in matches:
        if _normalize_optional_value(timing.route) == route:
            return timing

    return None


def _with_derived_steady_state(
    timing: PharmacokineticTiming,
) -> PharmacokineticTiming:
    if timing.steady_state is not None:
        return timing

    steady_state = estimate_steady_state(timing.half_life)

    if steady_state is None:
        return timing

    return PharmacokineticTiming(
        drug_id=timing.drug_id,
        route=timing.route,
        formulation=timing.formulation,
        release_type=timing.release_type,
        half_life=timing.half_life,
        tmax=timing.tmax,
        onset=timing.onset,
        duration=timing.duration,
        steady_state=steady_state,
        steady_state_basis="derived_from_half_life",
        active_metabolites=timing.active_metabolites,
        notes=timing.notes,
    )


def _normalize_optional_value(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()

    if not normalized:
        return None

    return normalized