from core.mechanisms.severity import (
    preliminary_severity_rank,
    strongest_preliminary_severity,
)


def test_preliminary_severity_rank_orders_known_labels():
    assert preliminary_severity_rank("caution") < preliminary_severity_rank(
        "high_caution"
    )


def test_preliminary_severity_rank_unknown_label_is_lowest():
    assert preliminary_severity_rank("unknown") == 0


def test_strongest_preliminary_severity_returns_highest_ranked_label():
    assert (
        strongest_preliminary_severity(["caution", "high_caution"])
        == "high_caution"
    )


def test_strongest_preliminary_severity_returns_none_for_empty_input():
    assert strongest_preliminary_severity([]) is None