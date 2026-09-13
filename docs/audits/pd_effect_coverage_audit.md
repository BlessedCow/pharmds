# PD Effect Coverage Audit

This audit compares curated drug PD effects with generic PD overlap rules,
explicit PD pair rules, concept-family mappings, and documented non-generic
coverage classifications.

## Summary

- Curated PD effect IDs: 43
- Direct generic-rule coverage: 33
- Concept-family mappings: 6
- Explicit pair effect IDs: 1
- Documented non-generic concepts: 4
- Undocumented curated effects: 0

## Concept-family mappings

- `blood_pressure_increase` -> `hypertension`
- `hypertension_risk` -> `hypertension`
- `lithium_increase_risk` -> `lithium_level_increase_risk`
- `seizure_threshold` -> `seizure_risk`
- `sympathomimetic_activity` -> `sympathetic_stimulation`
- `tachycardia_risk` -> `tachycardia`

## Documented non-generic concepts

### `cholinergic_modulation`

This is a broad mechanistic tag with mixed directionality. Simple overlap does
not imply a predictable additive clinical interaction.

### `hypersensitivity_risk`

Hypersensitivity to unrelated agents is not assumed to be generically additive.
Any clinically meaningful interaction should be represented with agent-specific
or mechanism-specific evidence.

### `nAChR_antagonism`

This is a receptor-mechanism tag rather than a standalone adverse-effect
endpoint. Overlap alone does not justify a generic interaction alert.

### `renal_function`

This tag currently mixes impaired renal function risk with renal elimination
context and contains both increase and decrease directions. It requires a more
specific renal model rather than simple overlap.

## Directly covered curated effects

- `CNS_depression`
- `CNS_stimulation`
- `D2_blockade`
- `EPS_risk`
- `QT_prolongation`
- `activation_agitation_risk`
- `alpha1_antagonism`
- `anticholinergic_effects`
- `bleeding`
- `bradycardia`
- `constipation_risk`
- `h1_antagonism`
- `hyperkalemia_risk`
- `hypertension`
- `hypokalemia_risk`
- `insomnia_risk`
- `intracranial_hypertension_risk`
- `mania_activation_risk`
- `nausea`
- `neurotoxicity_risk`
- `noradrenergic_effects`
- `opioid_antagonist`
- `orthostatic_hypotension`
- `photosensitivity_risk`
- `respiratory_depression`
- `sedation`
- `seizure_risk`
- `serotonergic`
- `serotonin_syndrome`
- `sympathetic_stimulation`
- `tachycardia`
- `urinary_retention_risk`
- `withdrawal_risk`

## Explicit pair effect coverage

- `seizure_risk`

## Undocumented effects

- None
