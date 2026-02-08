# PharmDS --- Pharmacology Decision-Support Tool


## **EDUCATIONAL ONLY. NOT FOR DIAGNOSTIC OR CLINICAL USE**

PharmDS is a Python based, rule driven pharmacology decision support system that provides mechanistic, explainable analysis of drug-drug interactions.

The project prioritizes clarity, traceability, and conservatism over prediction.
It is intended for education, internal discussion, and learning, not for
prescribing, diagnosis, or real-world clinical decision making.

-----------------------------------------------------------------------

**CORE CAPABILITIES**

- Command line interface (CLI)
- Directional pharmacokinetic (PK) interaction modeling
- Phase I enzyme support (CYP)
- Phase II enzyme support (UGT)
- Transporter-aware PK modeling
  - Efflux: P-gp (ABCB1), BCRP (ABCG2)
  - Uptake: OATP (e.g., SLCO1B1)
- Family-based transporter rules (not hardcoded to a single protein)
- Composite mechanism detection (e.g., CYP + transporter effects)
- PK driven PD risk amplification
- Explicit severity and action classification
- Deterministic, test driven rule engine

-----------------------------------------------------------------------

EXAMPLE OUTPUT
```
clarithromycin + quetiapine
Overall: severity=major | class=adjust_monitor

PK section (directional):
- [major | adjust_monitor] Strong CYP3A4 inhibition increases exposure of CYP3A4 substrates
  Affected: quetiapine | Interacting: clarithromycin
  Explanation: clarithromycin is a strong CYP3A4 inhibitor and quetiapine is a CYP3A4 substrate.
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

Footer: This output is an educational mechanistic explanation. Verify with primary sources.
```
-----------------------------------------------------------------------

INSTALLATION

Requirements:
- Python 3.11 or newer
- Virtual environment recommended

Setup:
1. Clone the repository
2. Create and activate a virtual environment
3. Install the project in editable mode:

   `pip install -e .`

-----------------------------------------------------------------------

USAGE

Run the CLI with two or more drug names (order does not matter):

   `python -m app.cli quetiapine clarithromycin`

Domain filtering examples:

-  `python -m app.cli digoxin verapamil --domain pgp`
-  `python -m app.cli rosuvastatin cyclosporine --domain oatp`
-  `python -m app.cli irinotecan atazanavir --domain ugt`
-  `python -m app.cli citalopram ondansetron --domain pd`

Supported domains:
- `cyp`   *CYP mediated PK*
- `ugt`   *Phase II (UGT) metabolism*
- `pgp`   *P-glycoprotein (ABCB1)*
- `bcrp`  *BCRP (ABCG2)*
- `oatp`  *Organic Anion Transporting Polypeptides*
- `pd`    *Pharmacodynamic overlap*
- `pk`    *Alias for all PK mechanisms*
- `all`   *All domains (default)*

-----------------------------------------------------------------------

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
-----------------------------------------------------------------------

DESIGN PHILOSOPHY

- Mechanistic pharmacology over heuristic scoring
- Explicit directionality (affected vs interacting drug)
- Conservative severity escalation
- Transporter and Phase II-aware PK modeling
- Composable logic (PK → PD amplification)
-----------------------------------------------------------------------

**DISCLAIMER**

This software is provided for educational purposes only.

It is not a medical device and must not be used for diagnosis, treatment,
prescribing, or patient care.

Always consult qualified healthcare professionals and authoritative references
when making clinical decisions.
