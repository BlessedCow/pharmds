
PHARMDS – PHARMACOLOGY DECISION-SUPPORT TOOL (EDUCATIONAL)

EDUCATIONAL ONLY – NOT FOR DIAGNOSTIC OR CLINICAL USE


PharmDS is a Python-based pharmacology decision-support project that provides
mechanistic, explainable analysis of drug–drug interactions.

The system focuses on pharmacokinetics (PK) and selected pharmacodynamic (PD)
risk amplification patterns. All logic is rule-based, deterministic, and designed
for education, internal discussion, and learning.

PharmDS is NOT intended for prescribing, diagnosis, or real-world clinical
decision-making.


--------------------------------------------------
KEY CAPABILITIES
--------------------------------------------------

- Command-line interface (CLI)
- Mechanistic, rule-based interaction engine
- Directional PK interaction modeling (affected drug → interacting drug)
- CYP enzyme modeling (inhibition, induction, substrate relationships)
- Drug transporter modeling (e.g., P-gp / ABCB1)
- Family-based transporter logic (not hardcoded to single transporters)
- Composite mechanism detection (e.g., CYP + transporter effects)
- PD risk amplification driven by PK exposure changes
- Severity and action classification (info, caution, adjust/monitor, avoid)
- Fully explainable, human-readable output
- Deterministic behavior with comprehensive test coverage
- Continuous integration with linting and tests


--------------------------------------------------
EXAMPLE OUTPUT
--------------------------------------------------

```
clarithromycin + quetiapine
Overall: severity=major | class=adjust_monitor

PK section (directional):
- [major | adjust_monitor] Strong CYP3A4 inhibition increases exposure of CYP3A4 substrates
  Affected: quetiapine | Interacting: clarithromycin
  Explanation:
    clarithromycin is a strong CYP3A4 inhibitor and quetiapine is a CYP3A4 substrate.
  Rationale:
    - clarithromycin inhibits CYP3A4, a major metabolic pathway for quetiapine.
    - Reduced metabolism can increase quetiapine systemic exposure.
  Suggested actions:
    - Consider alternatives to the inhibitor when feasible (educational).
    - Monitor for dose-related adverse effects.

PD section (derived):
- [major | adjust_monitor] Increased exposure may amplify CNS depression effects
  Rationale:
    - quetiapine has CNS-depressant effects.
    - Increased exposure may amplify sedation-related adverse effects.
  Suggested actions:
    - Use caution with sedation and impairment risk.
    - Monitor for oversedation when applicable.

Footer:
This output is an educational mechanistic explanation.
Verify with primary sources.
```

--------------------------------------------------
INSTALLATION
--------------------------------------------------

Requirements:
- Python 3.11 or higher
- Virtual environment recommended

Setup:

1. Clone the repository
2. Create and activate a virtual environment
3. Install the project in editable mode:

`pip install -e .`


--------------------------------------------------
USAGE
--------------------------------------------------

Run the CLI with two drug names (order does not matter):

`python -m app.cli quetiapine clarithromycin`

Optional domain filtering:

`python -m app.cli digoxin verapamil --domain pgp`
`python -m app.cli citalopram ondansetron --domain pd`

Supported domains:
- `cyp`
- `pgp` (ABCB1 / P-glycoprotein family)
- `pd`


--------------------------------------------------
PROJECT STRUCTURE
--------------------------------------------------
```
pharmds/
├── app/        CLI entry points
├── core/       Core domain models and enums
├── reasoning/  PK/PD reasoning and explanation logic
├── rules/      Rule definitions and evaluation engine
├── data/       Drug, enzyme, and transporter seed data
├── docs/       Design notes and contributor templates
├── tests/      Unit and scenario tests
├── README.md
├── ROADMAP.md
├── CONTRIBUTING.txt
├── LICENSE
└── DISCLAIMER.txt
```

--------------------------------------------------
DESIGN PHILOSOPHY
--------------------------------------------------

- Mechanistic pharmacology over heuristic scoring
- Explicit directionality and causality
- Conservative severity escalation
- Transporter-aware PK modeling
- Composable logic (PK → PD amplification)
- Strong emphasis on explainability
- False-positive avoidance through negative testing
- Educational framing at every layer


--------------------------------------------------
CONTRIBUTING
--------------------------------------------------

Contributions are welcome.

Please see:
- `CONTRIBUTING.txt`
- `docs/ADDING_A_DRUG.txt`
- `docs/ADDING_A_RULE.txt`

All contributions are expected to include tests and remain within the
educational scope of the project.


--------------------------------------------------
DISCLAIMER
--------------------------------------------------

This software is provided for educational purposes only.

It is not a medical device and must not be used for diagnosis, treatment,
prescribing, or patient care.

Always consult qualified healthcare professionals and authoritative references
when making clinical decisions.
