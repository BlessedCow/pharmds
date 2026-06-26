# Composite rule parity audit

This audit records old composite PK and PK-to-PD behavior before mechanism pipeline migration.

The mechanism pipeline remains comparative here. This audit does not replace composite rules or change public wording.

## Locked behaviors

| Behavior | Old output | Mechanism pipeline comparison | Migration implication |
| --- | --- | --- | --- |
| CYP plus P-gp exposure increase | `PK_DUAL_MECH_INCREASE` can appear with the underlying PK hits. | `object_exposure_increase_cluster` groups the object drug with both `CYP3A4` and `P-gp` targets. | Migration must preserve the dual-mechanism concept without duplicating generic and composite output unexpectedly. |
| CYP plus UGT or UGT plus P-gp exposure increase | Existing composite helpers can emit `PK_DUAL_MECH_INCREASE_CYP_UGT` or `PK_DUAL_MECH_INCREASE_UGT_PGP`. | Mechanism aggregates group exposure-increase targets by object drug. | Composite IDs remain old rule ownership until a mechanism-owned policy exists. |
| Three or more exposure-increase mechanisms | Existing composite helper can emit `PK_MULTI_MECH_INCREASE`. | Mechanism aggregates can show multiple targets for one object drug even when old pairwise output does not emit the composite rule. | Mechanism visibility is not the same as public rule output ownership. |
| PK exposure increase amplifies CNS depression | `COMP_PK_UP_CNS_DEP` appears as old PD composite output when exposure increases for a drug with medium or high CNS depression effect. | Mechanism pipeline currently records the PK exposure increase but does not model this PK-to-PD amplification as a policy result. | Migration needs explicit PK-to-PD amplification policy before ownership can move. |

## Current parity baseline

- `tacrolimus` plus `clarithromycin` locks CYP plus P-gp dual-mechanism behavior.
- `methadone` plus `clarithromycin` locks PK exposure increase plus CNS depression amplification behavior.
- `alprazolam` plus `clarithromycin` locks PK-to-PD CNS amplification without relying on a separate shared PD rule.
- `vortioxetine` plus `fluconazole` plus `bupropion` locks the difference between mechanism multi-target visibility and old public composite output.