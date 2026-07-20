from core.pk_timing import (
    PharmacokineticTiming,
    TimingRange,
    build_pk_timing_context,
)


def test_build_pk_timing_context_returns_timing_for_known_drugs() -> None:
    context = build_pk_timing_context(
        ["vortioxetine", "propranolol"],
        route="oral",
        release_type="ir",
    )

    assert context[0]["drug_id"] == "vortioxetine"
    assert context[0]["timing"]["drug_id"] == "vortioxetine"
    assert context[0]["timing"]["route"] == "oral"
    assert context[0]["timing"]["release_type"] == "ir"
    assert context[0]["timing"]["half_life"] == {
        "min_value": 66,
        "max_value": 66,
        "unit": "hours",
    }

    assert context[1]["drug_id"] == "propranolol"
    assert context[1]["timing"]["drug_id"] == "propranolol"
    assert context[1]["timing"]["route"] == "oral"
    assert context[1]["timing"]["release_type"] == "ir"
    assert context[1]["timing"]["steady_state"] == {
        "min_value": 12,
        "max_value": 30,
        "unit": "hours",
    }


def test_build_pk_timing_context_preserves_input_order() -> None:
    context = build_pk_timing_context(
        ["propranolol", "vortioxetine"],
        route="oral",
        release_type="ir",
    )

    assert [item["drug_id"] for item in context] == [
        "propranolol",
        "vortioxetine",
    ]


def test_build_pk_timing_context_returns_none_timing_for_unknown_drugs() -> None:
    context = build_pk_timing_context(
        ["vortioxetine", "notarealdrug"],
        route="oral",
        release_type="ir",
    )

    assert context[0]["timing"] is not None
    assert context[1] == {
        "drug_id": "notarealdrug",
        "timing": None,
    }


def test_build_pk_timing_context_accepts_custom_data() -> None:
    custom_timing = PharmacokineticTiming(
        drug_id="example",
        route="oral",
        release_type="ir",
        half_life=TimingRange(
            min_value=2,
            max_value=3,
            unit="hours",
        ),
    )

    context = build_pk_timing_context(
        ["example"],
        route="oral",
        release_type="ir",
        data=(custom_timing,),
    )

    assert context == [
        {
            "drug_id": "example",
            "timing": {
                "drug_id": "example",
                "route": "oral",
                "formulation": None,
                "release_type": "ir",
                "half_life": {
                    "min_value": 2,
                    "max_value": 3,
                    "unit": "hours",
                },
                "tmax": None,
                "onset": None,
                "duration": None,
                "steady_state": {
                    "min_value": 8,
                    "max_value": 15,
                    "unit": "hours",
                },
                "steady_state_basis": "derived_from_half_life",
                "active_metabolites": [],
                "notes": [],
            },
        }
    ]