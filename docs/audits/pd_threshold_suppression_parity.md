# PD threshold and suppression parity audit

This audit records old pharmacodynamic threshold and suppression behavior before mechanism pipeline migration.

The mechanism pipeline remains comparative here. This audit does not migrate ownership or change public wording.

## Old rule behavior

Old PD overlap rules use `min_magnitude` to decide whether both drugs meet the minimum PD effect threshold for a rule.

Examples:

| Rule ID | Effect | Required magnitude |
| --- | --- | --- |
| `PD_QT_ADDITIVE` | `QT_prolongation` | `medium` |
| `PD_QT_PROLONGATION_ADDITIVE_HIGH` | `QT_prolongation` | `high` |
| `PD_SEROTONERGIC_ADDITIVE` | `serotonergic` | `medium` |
| `PD_CNS_DEP_ADDITIVE` | `CNS_depression` | `medium` |

A low plus medium pair may still create a mechanism pipeline shared-effect candidate, but the old PD rule does not fire unless both drugs meet the old rule threshold.

## QT suppression behavior

When `PD_QT_PROLONGATION_ADDITIVE_HIGH` applies to the same pair, old rule output suppresses the generic `PD_QT_ADDITIVE` rule.

This prevents duplicate QT alerts for the same pair.

## Current mechanism pipeline comparison

The mechanism pipeline currently detects shared PD effects without applying the old rule-engine `min_magnitude` threshold.

That means the mechanism pipeline can record a shared QT, serotonergic, or CNS depression concept for pairs that old PD rules currently suppress.

This is useful for mechanism visibility, but it is not yet equivalent to old public pairwise output.

## Migration implication

Before mechanism pipeline output owns PD pairwise output, migration needs one of these approaches:

- preserve old `min_magnitude` threshold behavior in the mechanism policy or arbitration layer
- preserve old QT high-risk suppression behavior so generic QT output does not duplicate high QT output
- keep mechanism-only shared-effect output separate from old pairwise public rule output