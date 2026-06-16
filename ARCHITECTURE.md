# Architecture Notes

## Interaction Analysis Paths

PharmDS currently has two overlapping interaction analysis paths:

- The older rule engine path in `rules/`
- The newer mechanism pipeline path in `core/mechanisms/`

Both paths are still active. This is intentional.

## Older Rule Engine Path

The older rule engine loads JSON rule definitions from `rules/rule_defs/` and evaluates them through `rules.engine`.

Current service flow:

1. Resolve input drug names to drug IDs.
2. Load structured drug facts.
3. Load and filter rules by selected domains.
4. Evaluate rules with `evaluate_all`.
5. Apply composite rule logic from `rules.composite_rules`.
6. Build pairwise reports and optional regimen summaries.

This path currently owns:

- Pairwise rule hits
- PK and PD rule explanations
- Directional PK interaction details
- Rule-level severity and action class output
- Rule references and suggested actions
- Rich CLI pairwise detail output
- Existing pairwise JSON payload fields
- Regimen summaries built from pairwise reports
- Legacy rule fallback summaries in public result summaries

The rule engine remains the primary source for established pairwise interaction behavior.

## Newer Mechanism Pipeline Path

The newer mechanism pipeline is centered in `core/mechanisms/pipeline.py`.

Current pipeline flow:

1. Convert facts into normalized mechanism effects.
2. Find interaction candidates.
3. Apply arbitration.
4. Apply concern policy.
5. Aggregate related concerns.
6. Score concerns.
7. Add preliminary educational severity annotations.
8. Add aggregate evidence summaries.
9. Build aggregate concern summaries.

This path currently owns:

- `mechanism_pipeline_json`
- Mechanism debug payloads
- Aggregate mechanism concerns
- Aggregate severity annotations
- Aggregate evidence summaries
- Aggregate concern summaries
- Public aggregate summaries shown before legacy rule summaries

The mechanism pipeline is currently read-only with respect to the older rule engine. It does not replace rule evaluation yet.

## Current Output Ownership

The service layer runs both paths during analysis.

The older rule engine produces pairwise reports and regimen summaries. The newer mechanism pipeline produces normalized mechanism stages and aggregate summaries. Public result summaries combine both sources: aggregate summaries from the mechanism pipeline first, followed by legacy rule hit summaries from pairwise reports.

This mixed output model is expected for now.

## Migration Direction

The intended direction is to gradually move more explanation, aggregation, evidence, and public summary behavior into the mechanism pipeline where it improves consistency and reduces duplication.

That migration should be incremental. Existing rule behavior should be preserved unless a milestone explicitly changes it. The older rule engine should not be deleted yet because it still owns important pairwise behavior, CLI detail output, JSON compatibility, and tested rule semantics.

Future work should prefer small, verified handoffs from the rule engine into the mechanism pipeline instead of a broad rewrite.