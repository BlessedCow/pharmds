# Safety and Scope

This project is an educational, local pharmacology reasoning tool.

## Not for clinical decision-making
- Not diagnostic.
- Not prescribing guidance.
- Not a replacement for clinical judgment, labeling, or guidelines.

## Explainable-by-design
- All outputs must be traceable to explicit rules.
- If a conclusion cannot be explained mechanistically, it should not be emitted.

## Conservative handling of uncertainty
- Avoid precise numeric predictions unless you can cite a defensible, public source and represent uncertainty explicitly.
- Prefer bins (low/medium/high) and qualitative directionality.

## Data sources
- Local SQLite/JSON only.
- No scraping.
- References should be user-curated (e.g., drug labels, guidelines) and stored with rules.
