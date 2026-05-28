from types import SimpleNamespace

from app.streamlit_ui import controls
from app.streamlit_ui.controls import DEFAULT_DOMAIN, reset_analysis_state


def test_reset_analysis_state_restores_streamlit_session_defaults(monkeypatch):
    fake_streamlit = SimpleNamespace(
        session_state={
            "drug_text": "clarithromycin\nfluconazole",
            "qt_risk": True,
            "bleeding_risk": True,
            "domain": "pd",
            "debug_mechanism_json": True,
            "analysis_result": object(),
        },
    )
    monkeypatch.setattr(controls, "st", fake_streamlit)

    reset_analysis_state()

    assert fake_streamlit.session_state == {
        "drug_text": "",
        "qt_risk": False,
        "bleeding_risk": False,
        "domain": DEFAULT_DOMAIN,
        "debug_mechanism_json": False,
        "analysis_result": None,
    }