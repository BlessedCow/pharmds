from __future__ import annotations

from core.pk_timing.models import PharmacokineticTiming, TimingRange

PK_TIMING_DATA = (
    PharmacokineticTiming(
        drug_id="vortioxetine",
        route="oral",
        formulation="tablet",
        release_type="ir",
        half_life=TimingRange(
            min_value=66,
            max_value=66,
            unit="hours",
        ),
        tmax=TimingRange(
            min_value=7,
            max_value=11,
            unit="hours",
        ),
        steady_state=TimingRange(
            min_value=14,
            max_value=14,
            unit="days",
        ),
        steady_state_basis="source_reported",
        notes=(
            "Oral vortioxetine has delayed peak timing and long elimination.",
        ),
    ),
    PharmacokineticTiming(
        drug_id="propranolol",
        route="oral",
        formulation="tablet",
        release_type="ir",
        half_life=TimingRange(
            min_value=3,
            max_value=6,
            unit="hours",
        ),
        tmax=TimingRange(
            min_value=1,
            max_value=4,
            unit="hours",
        ),
        notes=(
            "Immediate-release oral propranolol has earlier peak timing than "
            "many antidepressants.",
        ),
    ),
    PharmacokineticTiming(
        drug_id="propranolol",
        route="oral",
        formulation="capsule",
        release_type="er",
        half_life=TimingRange(
            min_value=8,
            max_value=10,
            unit="hours",
        ),
        tmax=TimingRange(
            min_value=6,
            max_value=10,
            unit="hours",
        ),
        notes=(
            "Extended-release propranolol shifts peak exposure later than "
            "immediate-release propranolol.",
        ),
    ),
    PharmacokineticTiming(
        drug_id="hydroxyzine",
        route="oral",
        formulation="tablet",
        release_type="ir",
        half_life=TimingRange(
            min_value=20,
            max_value=25,
            unit="hours",
        ),
        tmax=TimingRange(
            min_value=2,
            max_value=2,
            unit="hours",
        ),
        notes=(
            "Oral hydroxyzine may have clinically relevant sedating effects "
            "before complete elimination.",
        ),
    ),
    PharmacokineticTiming(
        drug_id="baclofen",
        route="oral",
        formulation="tablet",
        release_type="ir",
        half_life=TimingRange(
            min_value=2,
            max_value=6,
            unit="hours",
        ),
        tmax=TimingRange(
            min_value=2,
            max_value=3,
            unit="hours",
        ),
        notes=(
            "Oral baclofen has relatively short elimination compared with "
            "many centrally acting chronic medications.",
        ),
    ),
)