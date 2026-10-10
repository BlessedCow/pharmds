# Pairwise Analysis Engine Reconciliation Audit

## Purpose

This audit records observable differences between PharmDS's legacy rule-based pairwise analysis and its mechanism-based analysis pipeline. It provides a reproducible inventory of differences, documents their potential significance, and tracks evidence-supported decisions about whether to retain, correct, or reconcile the behavior.

A discrepancy is **not** proof that either engine is incorrect. Agreement on an interaction concept does not necessarily establish agreement on severity, confidence, evidence provenance, or explanatory language.

## Scope and boundaries

**In scope:** pairwise findings, mechanism concepts, rule identifiers, inclusion and suppression thresholds, severity mapping, evidence provenance, composite PK/PD interactions, negative controls, and order invariance.

**Out of scope:** independent clinical validation of every possible drug pair, patient-specific treatment recommendations, and unvalidated assumptions that either engine is authoritative. Multi-drug regimen interactions are recorded separately unless directly implicated in a pairwise finding.

**Safety boundary:** any proposed change to clinical behavior requires evidence review, regression coverage, and explicit approval; a test passing only establishes consistency with its assertions.

## Reproduction methodology

1. Run both analysis paths against the same normalized drug identities and input context.
2. Capture legacy rule IDs and adapted mechanism concepts as separate sets, without assuming equivalent semantics.
3. Check order invariance by repeating each pair in reverse order.
4. Record legacy-only, mechanism-only, and overlapping concepts, then evaluate severity, evidence, confidence, and narrative independently when mappings exist.
5. Classify each observed difference by its technical cause; reserve clinical correctness judgments until supporting references are reviewed.
6. Add positive and negative controls, preserve the observed behavior in tests, and record any accepted resolution and validation evidence.

Primary regression coverage:

- `tests/mechanisms/test_pairwise_comparison_harness.py`
- `tests/mechanisms/test_pairwise_discrepancy_classification.py`
- `tests/mechanisms/test_pairwise_adapter.py`

## Classification vocabulary

| Classification | Meaning |
| --- | --- |
| Curated pair coverage | A specific legacy pair rule has no recorded mechanism counterpart. |
| Threshold policy difference | Different criteria determine whether a finding is emitted. |
| Mechanism concept difference | Findings use different concepts or policies that cannot be treated as equivalent without review. |
| Composite policy coverage | A cross-domain or amplified-risk finding is present in only one analysis path. |
| Severity discrepancy | Mapped equivalent concerns produce different severity designations. |
| Evidence discrepancy | Mapped concerns differ in supporting sources or provenance. |
| Regression | A change demonstrably contradicts an established, supported expected outcome. |

The first four categories are presently represented in the discrepancy-classification tests. The remaining categories describe future audit dimensions; they are **not** asserted as detected defects.

## Observed discrepancy inventory

These entries are a **non-exhaustive regression inventory**, not adjudicated clinical findings. “Pending review” means that the audit does not yet establish which behavior should be retained.

| ID | Drug pair | Observed difference | Classification | Assessment status |
| --- | --- | --- | --- | --- |
| PER-001 | Doxycycline + calcium carbonate | A curated absorption-related legacy pair rule has no recorded mechanism counterpart. | Curated pair coverage | Pending evidence review |
| PER-002 | Doxycycline + warfarin | A curated anticoagulation-related legacy pair rule has no recorded mechanism counterpart. | Curated pair coverage | Pending evidence review |
| PER-003 | Fluconazole + ondansetron | A mechanism QT concern is emitted where the legacy PD threshold does not produce the corresponding finding. | Threshold policy difference | Pending threshold-policy review |
| PER-004 | Lisdexamfetamine + fluoxetine | A curated legacy pair policy and a mechanism serotonergic concept differ. | Mechanism concept difference | Pending concept-mapping review |
| PER-005 | Alprazolam + clarithromycin | A legacy composite PK-to-CNS amplification rule has no recorded mechanism-policy counterpart. | Composite policy coverage | Pending cross-domain policy review |

### Detailed finding record

For each inventory entry, maintain the following information when verified:

- **Reproduction:** normalized drug IDs, relevant input modifiers, test case, and exact observed outputs.
- **Semantics:** what each rule or concept actually represents; whether findings are comparable.
- **Pharmacology:** hypothesized pathway, evidence-supported exposure/effect change, dose and route considerations, and clinically relevant uncertainty.
- **Evidence:** reference identifiers, source type, publication or revision date, directness of evidence, and conflicting findings.
- **Severity:** definitions used by each engine and justification for any proposed mapping.
- **Decision:** retain distinct policies, add representation, adjust threshold, correct defect, or defer with rationale.
- **Verification:** positive and negative control tests, test command, results, reviewer, and decision date.

Do not populate these fields with speculative values or claim clinical validation from automated tests alone.

## Review criteria

A discrepancy may be resolved only after evaluating:

1. **Mechanistic validity:** whether the asserted pathway is supported for the specific drugs and routes.
2. **Evidence quality:** distinguishing direct clinical evidence from indirect mechanistic inference.
3. **Clinical significance:** magnitude of exposure or effect, context dependence, and the possibility of false-positive alerts.
4. **Policy consistency:** the definition and application of suppression thresholds and severity categories.
5. **Completeness:** whether pair-specific, mechanism-general, and composite interactions each have an appropriate owner.
6. **Traceability:** whether the outcome can be tied to source IDs and repeatable test fixtures.

## Remediation decision log

| Finding ID | Decision | Rationale and evidence IDs | Code/tests | Validation | Status |
| --- | --- | --- | --- | --- | --- |
| PER-001 | Not determined | Evidence review pending | Existing comparison/discrepancy tests | Not clinically adjudicated | Open |
| PER-002 | Not determined | Evidence review pending | Existing comparison/discrepancy tests | Not clinically adjudicated | Open |
| PER-003 | Not determined | Threshold policy review pending | Existing comparison/discrepancy tests | Not clinically adjudicated | Open |
| PER-004 | Not determined | Concept mapping review pending | Existing comparison/discrepancy tests | Not clinically adjudicated | Open |
| PER-005 | Not determined | Composite policy review pending | Existing comparison/discrepancy tests | Not clinically adjudicated | Open |

When a decision is reached, update this table with a dated, reviewable explanation and links to the relevant code, tests, and references. Historical decisions should remain traceable.

## Maintenance expectations

Update the inventory whenever comparison tests reveal a new difference, when mapping policies change, or when evidence changes a prior assessment. Keep public documentation limited to system behavior, evidence, technical reasoning, and reproducible verification; avoid project-planning labels and personal context.
