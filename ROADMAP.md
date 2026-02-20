# PharmDS Roadmap

This document outlines planned and exploratory directions for the
PharmDS project.\
It is not a commitment or timeline, and priorities may change as the
project evolves.

PharmDS is currently in **v0.x (active early development)**. Stability,
APIs, and rule schemas may change.

------------------------------------------------------------------------

## Current State

PharmDS supports structured, deterministic PK and PD modeling with
explainable rule evaluation.

### Implemented Capabilities

### Pharmacokinetics (PK)

-   Phase I (CYP) interaction modeling\
-   Phase II (UGT) interaction modeling\
-   Transporter-aware PK (P-gp, BCRP, OATP)\
-   Composite mechanism detection (e.g., CYP + transporter effects)\
-   Directional modeling (affected vs interacting drug)

### Pharmacodynamics (PD)

-   Deterministic overlap logic using shared effect domains\
-   Additive QT prolongation detection\
-   Additive CNS depression detection\
-   Additive serotonergic stacking\
-   Additive stimulant and sympathomimetic stacking\
-   Cardiovascular axis modeling (hypertension, tachycardia, sympathetic
    stimulation)

### Output and UX

-   Rich formatted CLI output (`--format rich`)\
-   Domain filtering (`--domain`)\
-   Structured rule definitions with explicit severity and rule class\
-   Validation-driven seeding and reproducible database builds

Current development prioritizes correctness, explainability, and
reduction of alert fatigue.

------------------------------------------------------------------------

## Near-Term Focus (v0.x)

These items improve stability and signal-to-noise quality.

-   Refine PD overlap tuning to reduce redundant alerts\
-   Improve rule combination and severity escalation logic\
-   Strengthen rule validation and test coverage\
-   Expand structured output formats (e.g., JSON mode for downstream
    tooling)\
-   Improve CLI ergonomics and error handling\
-   Improve explanation template consistency across domains

------------------------------------------------------------------------

## Mid-Term Exploration (Pre--v1.0)

These areas may be explored as the core stabilizes.

-   Optional patient-context modifiers:
    -   Age
    -   Renal function
    -   Hepatic function
    -   QT risk factors
-   Dose-aware or conditional interaction logic\
-   Rule grouping or domain clustering (e.g., suppress subdomains when
    umbrella domain fires)\
-   Rule authoring and review tooling\
-   Initial Web UI for interactive exploration\
-   Internal ontology refinement and normalization improvements

------------------------------------------------------------------------

## Longer-Term Possibilities

These items are speculative and dependent on scope and resources.

-   Broader drug coverage\
-   Formalized pharmacologic ontology layer\
-   Interaction graph visualization\
-   Educational export formats (teaching mode)\
-   Integration with curated external data sources (where permitted)\
-   Interoperability with other clinical or educational tools

------------------------------------------------------------------------

## Non-Goals

To keep scope clear, PharmDS explicitly does **not** aim to:

-   Replace clinical judgment or prescribing decisions\
-   Act as a diagnostic or treatment recommendation system\
-   Provide patient-specific medical advice

------------------------------------------------------------------------

## Contribution Principles

PharmDS prioritizes:

-   Explicit, traceable logic\
-   Deterministic behavior\
-   Explainability over black-box prediction\
-   Conservative safety defaults\
-   Structural correctness over breadth

Contributions aligned with these principles are encouraged.
