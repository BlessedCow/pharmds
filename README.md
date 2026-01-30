
# Pharmacology Decision-Support Tool (Educational)

**EDUCATIONAL ONLY – NOT FOR DIAGNOSTIC OR CLINICAL USE**


This project is a Python-based pharmacology decision-support tool that provides **mechanistic, explainable analysis of drug–drug interactions**, with a primary focus on pharmacokinetics (PK) and selected pharmacodynamic (PD) risk amplification patterns.

The system is designed for **education, internal discussion, and learning**. It is **not** intended for prescribing, diagnosis, or real-world clinical decision-making.

---

## Key Capabilities

- Command-line interface (CLI)
- Directional PK interaction modeling (affected drug → interacting drug)
- Support for **CYP enzymes** and **drug transporters** (e.g., P-gp / ABCB1)
- Family-based transporter rules (future-proofed, not hardcoded)
- Composite mechanism detection (e.g., CYP + transporter effects)
- PD risk amplification driven by PK exposure changes
- Severity and action classification (caution, adjust/monitor, avoid)
- Deterministic, test-driven rule engine
- Fully explainable outputs

--- 

## Example Output

```
clarithromycin + quetiapine
Overall: severity=major | class=adjust_monitor

PK section (directional):
- [major | adjust_monitor] Strong CYP3A4 inhibition increases exposure of CYP3A4 substrates
	Affected: quetiapine | Interacting: clarithromycin
  Explanation: clarithromycin is a strong CYP3A4 inhibitor and quetiapine is a CYP3A4 substrate.
	Rationale:
		- clarithromycin inhibits CYP3A4, a major metabolic pathway for quetiapine.
		- Reduced metabolism can increase quetiapine systemic exposure. 	Suggested actions:
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

---

## Installation

**Requirements**
- Python 3.9 or higher
- Virtual environment recommended

**Setup**
1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies:
```
pip install -r requirements.txt
```

---

## Usage

Run the CLI with two drug names (order does not matter):

```
python -m app.cli quetiapine clarithromycin
```

Optional domain filtering:

```
python -m app.cli digoxin verapamil --domain pgp
python -m app.cli citalopram ondansetron --domain pd
```

Supported domains currently include:
-  `cyp`
-  `pgp` (ABCB1 / P-glycoprotein family)
-  `pd`

---

## Project Structure

```
pharmds/
├── app/ # CLI entry points
├── core/ # Core domain models, enums, evidence types
├── reasoning/ # PK/PD reasoning and explanation logic
├── rules/ # Rule definitions and evaluation engine
├── data/ # Drug, enzyme, transporter data and loaders
├── docs/ # Design notes, scope, and safety documentation
├── tests/ # Unit tests and golden scenario tests
├── README.md
├── ROADMAP.md
├── LICENSE
└── DISCLAIMER.txt

```

---

  
## Design Philosophy

- Mechanistic pharmacology over heuristic scoring
- Explicit directionality and causality
- Conservative severity escalation
- Transporter-aware PK modeling
- Composable logic (PK → PD amplification)
- Educational framing at every layer

---

## Disclaimer

This software is provided **for educational purposes only**.

It is **not a medical device** and must not be used for diagnosis, treatment, prescribing, or patient care.

Always consult qualified healthcare professionals and authoritative references when making clinical decisions.
