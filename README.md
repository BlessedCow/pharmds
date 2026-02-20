
# PharmDS — Pharmacology Decision-Support Tool

## EDUCATIONAL ONLY. NOT FOR DIAGNOSTIC OR CLINICAL USE

PharmDS is a Python-based, rule-driven pharmacology decision-support
system that provides mechanistic, explainable analysis of drug-drug
interactions.

The project prioritizes clarity, traceability, and conservatism over
prediction.
It is intended for education, internal discussion, and learning, not for
prescribing, diagnosis, or real-world clinical decision making.

------------------------------------------------------------------------

**CORE CAPABILITIES**

**Pharmacokinetics (PK)**

-   Command line interface (CLI)
-   Directional pharmacokinetic interaction modeling
-   Phase I enzyme support (CYP)
-   Phase II enzyme support (UGT)
-   Transporter-aware PK modeling
    -   Efflux: P-gp (ABCB1), BCRP (ABCG2)
    -   Uptake: OATP (e.g., SLCO1B1)
-   Family-based transporter rules
-   Composite mechanism detection (e.g., CYP + transporter effects)
-   PK-driven PD amplification logic

**Pharmacodynamics (PD)**

-   Deterministic PD overlap modeling
-   Additive QT prolongation detection
-   Additive CNS depression detection
-   Additive serotonergic stacking
-   Additive cardiovascular and stimulant stacking
-   Explicit severity and action classification
-   Deterministic, test-driven rule engine

**Expanded PD Ontology**

PharmDS now includes structured stimulant and cardiovascular domains:

-   CNS_stimulation
-   sympathetic_stimulation
-   hypertension
-   tachycardia
-   QT_prolongation
-   CNS_depression
-   serotonergic
-   serotonin_syndrome
-   bleeding
-   bradycardia
-   anticholinergic
-   hypoglycemia
-   cardiovascular

These domains enable clean additive overlap logic without hardcoding drug specific heuristics.

------------------------------------------------------------------------

EXAMPLE OUTPUT

**PK Example**
```
EDUCATIONAL ONLY - NOT DIAGNOSTIC

================================================================================
clarithromycin + quetiapine
Overall: severity=major | class=adjust_monitor

PK section (directional):
PK summary: exposure_increase
- [major | adjust_monitor] Strong CYP3A4 inhibition increases exposure of CYP3A4 substrates
  Affected: quetiapine | Interacting: clarithromycin
  Explanation: clarithromycin is a strong CYP3A4 inhibitor and quetiapine is a CYP3A4 substrate. This can increase quetiapine exposure, raising the risk of dose-related adverse effects.
  Rationale:
   - clarithromycin inhibits CYP3A4, a major metabolic pathway for quetiapine.
   - Reduced metabolism can increase quetiapine systemic exposure and peak concentrations.
  Suggested actions:
   - Consider alternative to the CYP3A4 inhibitor when feasible (educational).
   - If used together, monitor for dose-related adverse effects of the affected drug.
   - Be cautious with sedating or hypotensive substrates.

References (rule-level):
- Educational note: Mechanistic pattern: strong enzyme inhibition + substrate increases exposure.

================================================================================
Footer: This output is an educational mechanistic explanation. Verify with primary sources.
```
**PD Example (QT overlap)**
```
EDUCATIONAL ONLY - NOT DIAGNOSTIC

================================================================================
citalopram + ondansetron
Overall: severity=major | class=avoid

PD section (shared domain):
- [major | avoid] Additive QT prolongation risk with multiple QT-prolonging drugs
  Explanation: citalopram and ondansetron both have QT-prolongation liability. Using them together can increase QT-related risk. Patient-specific factors (electrolytes, baseline QT, bradycardia, other QT drugs) strongly modify real-world risk.
  Rationale:
   - Both drugs contribute to QT prolongation risk domain.
   - Combined effects can increase torsades risk, especially with additional risk factors.
  Suggested actions:
   - Avoid concurrent use of multiple QT-prolonging drugs when possible.
   - Monitor ECG and electrolytes in high-risk patients.
   - Assess patient-specific risk factors for QT prolongation.

References (rule-level):
- Educational note: PD stacking: shared QT domain implies additive risk.

================================================================================
Footer: This output is an educational mechanistic explanation. Verify with primary sources.
```

------------------------------------------------------------------------

INSTALLATION

Requirements: 
- Python 3.11 or newer 
- Virtual environment recommended

Setup: 
1. Clone the repository 
2. Create and activate a virtual environment 
3. Install the project in editable mode:
		`pip install -e .`

------------------------------------------------------------------------

**USAGE**

Run the CLI with two or more drug names:

`python -m app.cli quetiapine clarithromycin`

Aliases and brand names are supported:

`python -m app.cli adderall sudafed`
`python -m app.cli ativan robaxin`

Domain Filtering

-   `python -m app.cli digoxin verapamil –domain pgp`
-   `python -m app.cli rosuvastatin cyclosporine –domain oatp`
-   `python -m app.cli irinotecan atazanavir –domain ugt`
-   `python -m app.cli citalopram ondansetron –domain pd`

Supported domains:

-   `cyp` CYP-mediated PK
-   `ugt` Phase II (UGT) metabolism
-   `pgp` P-glycoprotein
-   `bcrp` BCRP transporter
-   `oatp` OATP transporters
-   `pd` Pharmacodynamic overlap
-   `pk` Alias for all PK mechanisms
-   `all` All domains (default)

------------------------------------------------------------------------

PROJECT STRUCTURE
```
pharmds/
├── app/        CLI entry points and user interaction
├── core/       Core models, enums, normalization utilities
├── reasoning/  PK/PD reasoning and explanation assembly
├── rules/      Rule definitions and evaluation engine
├── data/       Drug, enzyme, transporter data and loaders
├── docs/       Contribution guides and design notes
├── tests/      Unit tests and golden/negative scenarios
├── README.md
├── ROADMAP.md
├── LICENSE
└── DISCLAIMER.txt
```

------------------------------------------------------------------------

DESIGN PHILOSOPHY

-   Mechanistic pharmacology over heuristic scoring
-   Explicit directionality (affected vs interacting drug)
-   Deterministic rule evaluation
-   Structured PD ontology rather than hardcoded drug pairs
-   Conservative severity escalation
-   Transporter and Phase II-aware PK modeling
-   Composable logic (PK → PD amplification)

PharmDS favors explainability and structural correctness over breadth.

------------------------------------------------------------------------

**DISCLAIMER**

**This software is provided for educational purposes only.
It is not a medical device and must not be used for diagnosis,
treatment, prescribing, or patient care.**

**Always consult qualified healthcare professionals and authoritative
references when making clinical decisions.**
