# Rule Policy

This project is educational and rule-based. Rules must be mechanistic, explainable, and conservative with uncertainty.

## Two separate outputs
- severity: how much harm or treatment failure could plausibly occur
- rule_class: what action posture is appropriate (educational intent)

## severity definitions
- info: mechanistic note; low expected clinical impact
- caution: potential impact; depends strongly on context or is typically mild
- major: plausible meaningful harm or treatment failure, especially without mitigation
- contraindicated: reserved for high-certainty "avoid" combinations with strong supporting sources

## rule_class definitions
- info: educational note, no action posture implied
- caution: consider risk, counsel, check context
- adjust_monitor: typical mitigation exists (monitor, counsel, adjust)
- avoid: strong intent to avoid coadministration (requires strong sources)

## guardrails
- Do not use avoid or contraindicated based on pattern alone.
- For avoid/contraindicated, include references that reflect explicit labeling or guidelines.
- For transporter rules, be conservative about magnitude.

## escalation heuristics (v0)
- narrow therapeutic index substrate + inhibition of important pathway => severity at least major
- strong inhibitor/inducer on major pathway substrate => severity major
- QT overlap medium+medium or medium+high => severity major
- serotonergic overlap => caution by default (unless later rule adds more context)
