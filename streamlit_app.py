import streamlit as st

from app.service import analyze_text
from app.streamlit_ui.aggregate_summary import render_public_result_summaries
from app.streamlit_ui.controls import render_analysis_controls
from app.streamlit_ui.debug import render_mechanism_debug_json
from app.streamlit_ui.pair_summary import render_pair_summary
from app.streamlit_ui.regimen_summary import render_regimen_summary

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

    payload = res.payload
    facts = payload["facts"]
    pair_reports = payload["pair_reports"]
    templates = payload["templates"]
    selected_domains = payload["selected_domains"]
    regimen_summary = payload.get("regimen_summary")
    public_result_summaries = payload.get("public_result_summaries", [])
    aggregate_concern_summaries = payload.get("aggregate_concern_summaries", [])

    st.success(
        f"Drugs: {len(payload['drug_ids'])} | "
        f"Pairs: {len(pair_reports)} | "
        f"Domains: {', '.join(selected_domains)}"
    )

    render_public_result_summaries(
        public_result_summaries,
        aggregate_concern_summaries,
    )

    render_mechanism_debug_json(payload)

    render_regimen_summary(regimen_summary)

    render_pair_summary(facts, pair_reports, templates)