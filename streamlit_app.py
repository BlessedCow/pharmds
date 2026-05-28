import streamlit as st

from app.service import analyze_text
from app.streamlit_ui.aggregate_summary import render_public_result_summaries
from app.streamlit_ui.controls import render_analysis_controls
from app.streamlit_ui.debug import render_mechanism_debug_json
from app.streamlit_ui.pair_summary import render_pair_summary
from app.streamlit_ui.regimen_summary import render_regimen_summary
from app.streamlit_ui.result_state import analysis_state_from_payload

st.set_page_config(page_title="PharmDS (Educational)", layout="wide")
st.title("PharmDS")
st.caption("EDUCATIONAL ONLY. NOT FOR DIAGNOSTIC OR CLINICAL USE.")

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

drug_text, qt_risk, bleeding_risk, domain, run = render_analysis_controls()

if run:
    st.session_state["analysis_result"] = analyze_text(
        drug_text,
        qt_risk=qt_risk,
        bleeding_risk=bleeding_risk,
        domain=domain,
        as_json_payload=False,
    )

res = st.session_state["analysis_result"]

if res is not None:
    # analyze_text returns AnalyzeResult(ok: bool, payload: dict)
    if not res.ok:
        payload = res.payload

        if payload.get("error") == "unknown_drug":
            st.error("Unknown drug(s): " + ", ".join(payload.get("unknown", [])))
            sug = payload.get("suggestions", {})
            for tok, opts in sug.items():
                if opts:
                    st.write(f"Suggestions for {tok}: {', '.join(opts)}")
            st.stop()

        st.error(payload.get("error", "Unknown error"))
        st.stop()

    analysis_state = analysis_state_from_payload(res.payload)

    st.success(
        f"Drugs: {len(analysis_state.drug_ids)} | "
        f"Pairs: {len(analysis_state.pair_reports)} | "
        f"Domains: {', '.join(analysis_state.selected_domains)}"
    )

    render_public_result_summaries(
        analysis_state.public_result_summaries,
        analysis_state.aggregate_concern_summaries,
    )

    render_mechanism_debug_json(analysis_state.payload)

    render_regimen_summary(analysis_state.regimen_summary)

    render_pair_summary(
        analysis_state.facts,
        analysis_state.pair_reports,
        analysis_state.templates,
    )