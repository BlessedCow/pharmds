import sys
from types import SimpleNamespace

sys.modules.setdefault("streamlit", SimpleNamespace())

from app.streamlit_ui.debug import (  # noqa: E402
    mechanism_debug_expander_label,
    mechanism_debug_json_payload,
)


def test_mechanism_debug_expander_label_names_pipeline_source():
    assert mechanism_debug_expander_label() == "Mechanism Pipeline: Full JSON"


def test_mechanism_debug_json_payload_returns_pipeline_json_only():
    payload = {
        "pair_reports": [object()],
        "mechanism_pipeline_json": {"effects": []},
    }

    assert mechanism_debug_json_payload(payload) == {"effects": []}


def test_mechanism_debug_json_payload_uses_empty_dict_for_missing_or_invalid_json():
    assert mechanism_debug_json_payload({}) == {}
    assert mechanism_debug_json_payload({"mechanism_pipeline_json": []}) == {}