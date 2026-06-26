# Explicit pair rule gap audit

This audit records explicit pair-specific PK rules that should not be assumed to fall out of generic CYP, transporter, or shared PD logic.

The mechanism pipeline remains read-only here. This audit does not migrate ownership or change output behavior.

## Coverage classifications

- `pair_policy_only`: the current generic mechanism facts do not represent the named pair concern.
- `generic_pd_partial`: the current mechanism pipeline detects a related shared PD concern, but not the named pair PK concern.
- `generic_pk_with_pair_policy`: the current mechanism pipeline detects related generic PK and/or PD concepts, but the named pair rule still carries pair-specific educational handling.

## Explicit pair rule inventory

| Rule ID | Pair | Current generic mechanism coverage | Classification | Pair-specific handling still needed |
| --- | --- | --- | --- | --- |
| `PK_DOXYCYCLINE_AMOXICILLIN` | doxycycline plus amoxicillin | No current generic mechanism candidate. | `pair_policy_only` | Curated pair-specific educational handling for reduced doxycycline exposure or antibiotic effect. |
| `PK_DOXYCYCLINE_CALCIUM_CARBONATE` | doxycycline plus calcium carbonate | No current generic mechanism candidate. | `pair_policy_only` | Curated absorption or chelation handling that is not represented by current CYP, transporter, or PD overlap facts. |
| `PK_DOXYCYCLINE_WARFARIN` | doxycycline plus warfarin | No current generic mechanism candidate. | `pair_policy_only` | Curated pair-specific handling for increased warfarin effect or bleeding-related concern. |
| `PK_LISDEXAMFETAMINE_FLUOXETINE` | lisdexamfetamine plus fluoxetine | Generic shared serotonergic PD coverage only. | `generic_pd_partial` | Pair-specific handling for increased stimulant-related effects is still separate from the generic PD overlap. |
| `PK_METHADONE_CARBAMAZEPINE` | methadone plus carbamazepine | Generic enzyme induction candidates and shared CNS depression coverage. | `generic_pk_with_pair_policy` | Pair-specific handling for reduced methadone exposure and possible withdrawal or reduced opioid effect. |
| `PK_METHADONE_FLUOXETINE` | methadone plus fluoxetine | Generic CYP2D6 inhibition candidate and shared serotonergic coverage. | `generic_pk_with_pair_policy` | Pair-specific handling for increased methadone exposure and opioid toxicity-related concern. |
| `PK_VIBEGRON_DIGOXIN` | vibegron plus digoxin | No current generic mechanism candidate. | `pair_policy_only` | Curated pair-specific handling for increased digoxin exposure. |

## Migration implication

These rules should remain owned by the old explicit pair rule path until a dedicated curated pair-specific mechanism or policy layer exists.

Generic mechanism parity alone is not enough for these rules because the rule meaning depends on named-pair educational handling, pair-specific directionality, or a mechanism type that is not currently modeled.