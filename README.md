# Pharmacology Decision-Support Tool (Educational)

**EDUCATIONAL ONLY – NOT FOR DIAGNOSTIC OR CLINICAL USE**

This project is a Python-based pharmacology decision-support tool designed to analyze drug–drug interactions, with a primary focus on pharmacokinetics (PK), including CYP enzyme inhibition, induction, and substrate relationships.

It is intended for education, internal discussion, and learning, not for prescribing, diagnosis, or clinical decision-making.

============================================================

## FEATURES
- Command-line interface (CLI)
- Directional PK interaction analysis (inhibitor → substrate)
- Severity classification (minor, moderate, major)
- Clear explanations and mechanistic rationale
- Educational suggested actions (monitoring, adjustment considerations)
- Extensible architecture for future PK/PD logic

============================================================

## EXAMPLE OUTPUT

```
EDUCATIONAL ONLY - NOT DIAGNOSTIC

clarithromycin + quetiapine
Overall: severity=major | class=adjust_monitor

PK section (directional):
- [major | adjust_monitor] Strong CYP3A4 inhibition increases exposure of CYP3A4 substrates
  Affected: quetiapine | Interacting: clarithromycin
  Explanation: clarithromycin is a strong CYP3A4 inhibitor and quetiapine is a CYP3A4 substrate.
  Suggested actions:
   - Consider alternative to the CYP3A4 inhibitor when feasible
   - Monitor for dose-related adverse effects
```

============================================================

## INSTALLATION

Requirements:
- Python 3.9 or higher
- Virtual environment recommended

Setup:
1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies from requirements.txt

============================================================

## USAGE

Run the CLI with two drug names:

`python -m app.cli quetiapine clarithromycin`

The order of drugs does not matter. The tool determines interaction directionality internally.

============================================================

## PROJECT STRUCTURE

```
app/
 ├── cli.py            CLI entry point
 ├── engine/           Core interaction logic
 ├── data/             Drug and enzyme reference data
 ├── rules/            PK/PD interaction rules
 └── utils/            Helpers and formatting

tests/
 └── test_interactions.py
```

============================================================

## DESIGN PHILOSOPHY
- Explainable pharmacology, not black-box scoring
- Explicit PK mechanisms (CYPs, transporters)
- Conservative severity classification
- Educational framing at every output level

============================================================

## **DISCLAIMER**

This software is provided for educational purposes only.
It is not a medical device and must not be used for diagnosis, treatment, or patient care.

Always consult qualified healthcare professionals and authoritative references for clinical decisions.
