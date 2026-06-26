# Pairwise comparison harness audit

This audit records the purpose and boundaries of the pairwise comparison
harness.

The harness compares old pairwise rule output against pairwise-shaped
mechanism pipeline concerns. It does not change public output ownership.

## Harness boundaries

- Old output remains represented by rule IDs from pairwise PK and PD hits.
- Mechanism output is represented by internal pairwise adapter concepts.
- Exact parity scenarios are separated from known migration gaps.
- Known gaps are explicit and intentional.
- No public CLI, Streamlit, or JSON output is changed by this harness.

## Exact parity examples

Exact parity means the old rule output and mechanism-derived concern concept
represent the same educational concern.

Examples include:

- `PK_CYP3A4_STRONG_INHIB` matching a `CYP3A4` exposure-increase concern.
- `PK_CYP2D6_INHIB_SUBSTRATE` matching a `CYP2D6` exposure-increase concern.
- `PD_QT_ADDITIVE` matching a `QT_prolongation` additive PD concern.
- `PD_CNS_DEP_ADDITIVE` matching a `CNS_depression` additive PD concern.

## Known gap examples

Known gaps are expected during migration and should remain visible.

Examples include:

- curated explicit pair rules that have no generic mechanism equivalent
- old PD threshold suppression where the mechanism pipeline records a broader
  shared-effect concept
- old PK-to-PD composite output that is not yet represented by mechanism policy

## Migration implication

This harness gives migration work a controlled comparison layer.

New migration work should add scenarios here before changing output ownership.