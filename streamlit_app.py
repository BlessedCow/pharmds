import streamlit as st

from app.service import analyze_text

st.set_page_config(page_title="PharmDS (Educational)", layout="wide")
st.title("PharmDS")
st.caption("EDUCATIONAL ONLY. NOT FOR DIAGNOSTIC OR CLINICAL USE.")

drug_text = st.text_area(
    "Drugs (one per line, or comma/space separated)",
    height=140,
    placeholder="quetiapine\nclarithromycin",
)

col1, col2, col3 = st.columns(3)
with col1:
    qt_risk = st.checkbox("QT risk factors", value=False)
with col2:
    bleeding_risk = st.checkbox("Bleeding risk factors", value=False)
with col3:
    domain = st.text_input("Domains (e.g.all, pk, pd, cyp,pd)", value="all")

run = st.button("Analyze", type="primary")

if run:
    res = analyze_text(
        drug_text,
        qt_risk=qt_risk,
        bleeding_risk=bleeding_risk,
        domain=domain,
        as_json_payload=False,
    )

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

    st.success(
        f"Drugs: {len(payload['drug_ids'])} | "
        f"Pairs: {len(pair_reports)} | "
        f"Domains: {', '.join(selected_domains)}"
    )

    # Regimen summary (only for 3+ drugs)
    if regimen_summary:
        st.subheader("Regimen Summary (all drugs)")
        st.write(
            f"Overall: severity={regimen_summary['overall_severity'].value} | "
            f"class={regimen_summary['overall_rule_class'].value}"
        )
        flags = regimen_summary.get("regimen_flags", [])
        if flags:
            st.write("Flags:")
            for flag in flags:
                st.write(f"- {flag.get('message', '')}")

    # Quick, simple pair list (sanity output)
    st.subheader("Pair Summary")
    if not pair_reports:
        st.info("No rule-based interactions detected in selected domains (educational scope).")
        st.stop()

    for rep in pair_reports:
        d1 = facts.drugs[rep.drug_1].generic_name
        d2 = facts.drugs[rep.drug_2].generic_name
        title = (
            f"{d1} + {d2} | "
            f"severity={rep.overall_severity.value} | "
            f"class={rep.overall_rule_class.value}"
        )

        with st.expander(title, expanded=False):
            if rep.pk_hits:
                st.markdown("### PK section (directional)")
                if rep.pk_summary:
                    st.write(f"PK summary: {rep.pk_summary}")

                for h in rep.pk_hits:
                    st.write(f"- [{h.severity.value} | {h.rule_class.value}] {h.name}")

                    A = facts.drugs[h.inputs["A"]].generic_name
                    B = facts.drugs[h.inputs["B"]].generic_name
                    st.write(f"  Affected: {A} | Interacting: {B}")

                    tmpl = templates.get(h.rule_id, "")
                    if tmpl:
                        from reasoning.explain import render_explanation

                        st.write("  Explanation:")
                        st.write(render_explanation(tmpl, facts, h))

                    from reasoning.explain import render_rationale

                    rat = render_rationale(facts, h)
                    if rat:
                        st.write("  Rationale:")
                        st.code(rat)

                    if h.actions:
                        st.write("  Suggested actions:")
                        for a in h.actions:
                            st.write(f"  - {a}")

            if rep.pd_hits:
                st.markdown("### PD section (shared domain)")
                for h in rep.pd_hits:
                    st.write(f"- [{h.severity.value} | {h.rule_class.value}] {h.name}")

                    tmpl = templates.get(h.rule_id, "")
                    if tmpl:
                        from reasoning.explain import render_explanation

                        st.write("  Explanation:")
                        st.write(render_explanation(tmpl, facts, h))

                    from reasoning.explain import render_rationale

                    rat = render_rationale(facts, h)
                    if rat:
                        st.write("  Rationale:")
                        st.code(rat)

                    if h.actions:
                        st.write("  Suggested actions:")
                        for a in h.actions:
                            st.write(f"  - {a}")

            # References (rule-level)
            refs = []
            for h in (rep.pk_hits or []) + (rep.pd_hits or []):
                refs.extend(h.references or [])

            uniq = {(r.get("source", ""), r.get("citation", ""), r.get("url", "")) for r in refs}
            if uniq:
                st.markdown("### References (rule-level)")
                for source, citation, url in sorted(uniq):
                    if url:
                        st.write(f"- {source}: {citation} ({url})")
                    else:
                        st.write(f"- {source}: {citation}")