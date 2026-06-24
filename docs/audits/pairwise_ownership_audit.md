# Pairwise ownership audit

This audit identifies what the older pairwise rule path still owns before any migration work starts.

## Current old pairwise path

1. `rules.engine.load_rules()` loads JSON rule definitions from `rules/rule_defs/`.
2. `rules.engine.evaluate_all()` evaluates ordered drug pairs and returns `RuleHit` objects.
3. `reasoning.combine.build_pair_reports()` groups `RuleHit` objects into `PairReport` objects.
4. CLI, JSON, service, Rich, and Streamlit outputs consume those `PairReport` and `RuleHit` objects.

## Pairwise PK behaviors owned by the old rule engine

The old rule engine still owns these PK behaviors:

- Enzyme substrate plus inhibitor exposure checks.
- Enzyme substrate plus inducer exposure checks.
- Transporter substrate plus inhibitor exposure checks.
- Transporter substrate plus inducer exposure checks.
- Rule-specific strength guards, including moderate-or-strong inhibitor checks and strong inducer checks.
- Therapeutic-index guards for selected object drugs.
- Name guards for selected pairwise exceptions.
- Explicit named drug-pair rules.
- PK direction tags such as `exposure_increase`, `exposure_decrease`, `exposure_change`, `activation_change`, and `activation_decrease`.
- Rule-specific actions, rationale, references, names, severities, classes, and tags.
- Directional PK inputs where `A` is the affected drug and `B` is the interacting drug.

Current PK rule inventory:

- Generic or semi-generic enzyme rules: CYP1A2, CYP2C19, CYP2C9, CYP2D6, CYP3A4, and UGT1A1.
- Drug-specific enzyme rules: tizanidine, clopidogrel, warfarin, tramadol, and methadone-related rules.
- Transporter rules: BCRP, OATP, and P-gp.
- Explicit named pair rules: doxycycline plus amoxicillin, doxycycline plus calcium carbonate, doxycycline plus warfarin, lisdexamfetamine plus fluoxetine, methadone plus carbamazepine, methadone plus fluoxetine, and vibegron plus digoxin.

## Pairwise PD behaviors owned by the old rule engine

The old rule engine still owns these PD behaviors:

- Pairwise additive PD overlap rules.
- Minimum magnitude thresholds per PD effect.
- Symmetric duplicate suppression for PD hits.
- Rule-specific suppression of generic QT additive output when the high-risk QT rule fires for the same pair.
- Rule-specific actions, rationale, references, names, severities, classes, and tags.

Current PD overlap inventory:

- Activation or agitation risk.
- CNS depression, including a high-magnitude rule.
- Alpha-1 antagonism.
- Bleeding.
- Bradycardia.
- CNS stimulation.
- Constipation risk.
- D2 blockade.
- EPS risk.
- H1 antagonism.
- Hypertension.
- Insomnia risk.
- Lithium level increase risk.
- Mania activation risk.
- Nausea.
- Opioid antagonist overlap.
- QT prolongation, including a high-magnitude rule.
- Respiratory depression.
- Sedation.
- Seizure risk.
- Serotonergic burden.
- Serotonin syndrome.
- Sympathetic stimulation.
- Tachycardia.
- Withdrawal risk.

## Outputs that depend on PairReport

`PairReport` is still used for:

- Plain CLI pairwise summaries and details in `app/cli.py`.
- JSON `pairs` output in `app/json_output.py`.
- Service payload fields in `app/service.py`.
- Streamlit pair summaries in `app/streamlit_ui/pair_summary.py`.
- Streamlit result state in `app/streamlit_ui/result_state.py`.
- Regimen summary construction in `reasoning.combine.build_regimen_summary()`.
- Legacy public result summaries in `core/mechanisms/result_summary.py`.
- Tests that assert pairwise JSON, CLI, service, regimen, and public summary contracts.

## Outputs that depend on RuleHit

`RuleHit` is still used for:

- Rule engine output from `rules.engine.evaluate_rule()` and `rules.engine.evaluate_all()`.
- Pair grouping, severity synthesis, class synthesis, hit deduplication, and PK summary construction in `reasoning.combine`.
- JSON hit objects in `app/json_output.py`.
- Rich pairwise rendering in `app/render.py`.
- Evidence lines for legacy PD additive hits in `core/evidence/human_rendering.py`.
- Legacy public result summaries in `core/mechanisms/result_summary.py`.
- Composite rule helpers and rule-focused tests.

## Behaviors the mechanism pipeline already covers

The mechanism pipeline already covers broad versions of these behaviors:

- Enzyme inhibition exposure candidates.
- Enzyme induction exposure candidates.
- Transporter inhibition exposure candidates.
- Transporter induction exposure candidates.
- Shared PD effect candidates.
- Exposure increase and exposure decrease arbitration concerns.
- Additive PD arbitration concerns.
- Aggregate object exposure increase clusters.
- Aggregate object exposure decrease clusters.
- Aggregate shared PD effect clusters.
- Aggregate evidence, severity annotation, public summaries, debug output, and JSON serialization.

## Gaps blocking replacement of the old path

The old path should not be replaced until the mechanism path can preserve or intentionally replace these responsibilities:

- Exact rule inventory parity or an explicit deprecation list.
- Explicit named pair rules that do not fall out of generic mechanism matching.
- Rule-specific strength, therapeutic-index, and name constraints.
- Rule-specific severities, classes, actions, rationale, references, tags, and explanation templates.
- Directional PK display semantics.
- Pairwise JSON `pairs` contract stability.
- CLI plain and Rich pairwise output stability.
- Streamlit pair summary behavior.
- Service payload compatibility for `pair_reports` and public result summaries.
- Regimen summary counts, top-pair ranking, and pairwise hit counts.
- Legacy evidence rendering for `RuleHit` objects.