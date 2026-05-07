
# PharmDS — Pharmacology Decision-Support Tool

  

## EDUCATIONAL ONLY. NOT FOR DIAGNOSTIC OR CLINICAL USE

  

PharmDS is a Python-based, rule-driven pharmacology decision-support system that provides mechanistic, explainable analysis of drug-drug interactions.

 
The project prioritizes clarity, traceability, determinism, and conservatism over prediction. It is intended for education, internal discussion, learning, and software experimentation. It is not intended for prescribing, diagnosis, treatment, or real-world clinical decision making.

---
 
## Core Capabilities

### Pharmacokinetics (PK)

- Command line interface (CLI)

- Directional pharmacokinetic interaction modeling

- Phase I enzyme support, including CYP pathways

- Phase II enzyme support, including UGT pathways

- Transporter-aware PK modeling:

- Efflux transporters: P-gp/ABCB1, BCRP/ABCG2

- Uptake transporters: OATP/SLCO families

- Family-based transporter rules

- Composite mechanism detection, such as CYP plus transporter effects

- PK-driven PD amplification logic

- Affected/interacting drug directionality in detailed output

  

### Pharmacodynamics (PD)

- Deterministic PD overlap modeling

- Additive QT prolongation detection

- Additive CNS depression detection

- Additive sedation and H1 antagonism detection

- Additive serotonergic stacking

- Additive nausea/GI intolerance detection

- Additive cardiovascular, stimulant, orthostasis, and anticholinergic domains

- Explicit severity and action classification

- Rule-specific explanations, rationales, suggested actions, and references

- Normalized severity and action rationales in rich and JSON output

- Test-driven rule engine with negative tests to reduce noisy alerting

  

### Regimen-Level Analysis

For regimens with three or more drugs, PharmDS can summarize risk across the entire medication list, not only pair-by-pair.

 
Regimen summaries include:

  

- Number of drugs analyzed

- Overall regimen severity

- Overall regimen action class

- Pairwise hit counts

- PK vs PD hit counts

- Hit counts by severity and action class

- Repeated PD risk domains across the regimen

- Top interaction pairs by severity and hit count

- Regimen-level flags for selected high-risk stacks

  

This helps distinguish isolated pairwise interactions from broader patterns such as repeated sedation, QT burden, or CNS depression.

  

---

  

## Expanded PD Ontology

  

PharmDS uses structured PD domains to support additive overlap logic without hardcoding every possible drug pair.

  

Current PD domains include examples such as:

  

-  `CNS_depression`

-  `sedation`

-  `h1_antagonism`

-  `alpha1_antagonism`

-  `orthostatic_hypotension`

-  `QT_prolongation`

-  `serotonergic`

-  `serotonin_syndrome`

-  `bleeding`

-  `nausea`

-  `activation_agitation_risk`

-  `insomnia_risk`

-  `mania_activation_risk`

-  `seizure_risk`

-  `seizure_threshold`

-  `anticholinergic_effects`

-  `cholinergic_modulation`

-  `nAChR_antagonism`

-  `noradrenergic_effects`

-  `hypertension_risk`

-  `tachycardia_risk`

-  `bradycardia`

-  `hypoglycemia`

-  `cardiovascular`

  

These domains allow the engine to detect shared pharmacodynamic burden using structured drug facts and reusable rules.

  

---

  

## Example Output

  

### Rich Detail Example: PK Interaction

  

```bash

python  -m  app.cli  fluoxetine  bupropion  --detail  --format  rich

```

  

Example output:

  

```text

EDUCATIONAL ONLY - NOT DIAGNOSTIC

  

Interaction Summary (pairwise)

bupropion + fluoxetine

severity=caution | class=adjust_monitor | domains=cyp

  

PK section (directional):

- [caution | adjust_monitor] CYP2D6 inhibition may increase substrate exposure

Affected: fluoxetine | Interacting: bupropion

Explanation: bupropion inhibits CYP2D6 and fluoxetine is a CYP2D6 substrate.

This may increase fluoxetine exposure and raise adverse effect risk.

  

Rationale:

- bupropion inhibits CYP2D6.

- fluoxetine is a CYP2D6 substrate.

- Inhibition may increase fluoxetine exposure and adverse effect risk.

  

Severity rationale:

Caution because the combination may increase risk, but is often manageable

with awareness, patient-specific assessment, or monitoring.

  

Action rationale:

Adjust/monitor action because the combination may require dose review,

closer monitoring, timing separation, or patient-specific mitigation.

  

Suggested actions:

- Monitor for increased adverse effects from the affected drug.

- Consider dose adjustment or alternatives if clinically appropriate.

```

  

### Rich Detail Example: PD Interaction

  

```bash

python  -m  app.cli  vortioxetine  varenicline  --detail  --format  rich

```

  

Example output:

  

```text

PD section (shared domain):

- [caution | adjust_monitor] Additive nausea risk

Explanation: varenicline and vortioxetine can both contribute to nausea or

gastrointestinal intolerance. Combined use may increase additive nausea

burden, especially after initiation or dose changes.

  

Severity rationale:

Caution because the combination may increase risk, but is often manageable

with awareness, patient-specific assessment, or monitoring.

  

Action rationale:

Adjust/monitor action because the combination may require dose review,

closer monitoring, timing separation, or patient-specific mitigation.

  

Suggested actions:

- Use caution when combining agents that may increase nausea.

- Monitor for gastrointestinal intolerance, especially after initiation or dose increases.

- Consider taking medications with food or using supportive strategies if appropriate.

```

  

### JSON Output Example

  

```bash

python  -m  app.cli  quetiapine  hydroxyzine  trazodone  --format  json

```

  

JSON output includes:

  

- Schema version

- Input drug names

- Selected domains

- Patient flags

- Pairwise PK and PD hits

- Explanation text

- Rule rationale lines

- Suggested actions

- Rule references

- Normalized `severity_rationale`

- Normalized `action_rationale`

- Regimen summary for 3+ drugs

  

Example hit shape:

  

```json
{
  "rule_id": "PD_QT_ADDITIVE",
  "name": "Additive QT prolongation risk with multiple QT-prolonging drugs",
  "domain": "PD",
  "severity": "major",
  "class": "avoid",
  "severity_rationale": "Major because the combination may produce clinically meaningful risk and should generally prompt closer monitoring, mitigation, or therapy review.",
  "action_rationale": "Avoid action because the combination may pose enough risk that an alternative, spacing strategy, or prescriber review should be considered.",
  "inputs": {
    "A": "hydroxyzine",
    "B": "trazodone",
    "effect_id": "QT_prolongation"
  },
  "tags": [],
  "explanation": "hydroxyzine and trazodone both have QT-prolongation liability. Using them together can increase QT-related risk. Patient-specific factors strongly modify real-world risk.",
  "rationale": [
    "- Both drugs contribute to QT prolongation risk domain.",
    "- Combined effects can increase torsades risk, especially with additional risk factors."
  ],
  "actions": [
    "Assess patient-specific risk factors for QT prolongation.",
    "Avoid concurrent use of multiple QT-prolonging drugs when possible.",
    "Monitor ECG and electrolytes in high-risk patients."
  ],
  "references": [
    {
      "source": "Educational note",
      "citation": "PD stacking: shared QT domain implies additive risk."
    }
  ],
  "A": {
    "id": "hydroxyzine",
    "name": "hydroxyzine"
  },
  "B": {
    "id": "trazodone",
    "name": "trazodone"
  }
}

---

  

## Installation

  

### Requirements

  

- Python 3.11 or newer

- Virtual environment recommended

  

### Setup

  

Clone the repository:

  

```bash

git  clone  https://github.com/BlessedCow/pharmds.git

cd  pharmds

```

  

Create and activate a virtual environment:

  

```bash

python  -m  venv  .venv

```

  

On Windows PowerShell:

  

```powershell

.\.venv\Scripts\Activate.ps1

```

  

On macOS/Linux:

  

```bash

source  .venv/bin/activate

```

  

Install the project in editable mode:

  

```bash

pip  install  -e  .

```

  

Install development tools if needed:

  

```bash

pip  install  -e  ".[dev]"

```

  

---

  

## Usage

  

Run the CLI with two or more drug names:

  

```bash

python  -m  app.cli  quetiapine  clarithromycin

```

  

Use rich output:

  

```bash

python  -m  app.cli  quetiapine  clarithromycin  --format  rich

```

  

Show detailed rich output:

  

```bash

python  -m  app.cli  quetiapine  clarithromycin  --detail  --format  rich

```

  

Use JSON output:

  

```bash

python  -m  app.cli  quetiapine  clarithromycin  --format  json

```

  

Analyze a three-drug regimen:

  

```bash

python  -m  app.cli  quetiapine  hydroxyzine  trazodone  --detail  --format  rich

```

  

Aliases and brand names are supported when present in the curated data:

  

```bash

python  -m  app.cli  adderall  sudafed

python  -m  app.cli  ativan  robaxin

```

  

---

  

## Domain Filtering

  

Use `--domain` to restrict analysis to a specific mechanism group.

  

```bash

python  -m  app.cli  digoxin  verapamil  --domain  pgp

python  -m  app.cli  rosuvastatin  cyclosporine  --domain  oatp

python  -m  app.cli  irinotecan  atazanavir  --domain  ugt

python  -m  app.cli  citalopram  ondansetron  --domain  pd

```

  

Supported domains:

  

| Domain | Meaning |

|---|---|

| `cyp` | CYP-mediated PK |

| `ugt` | UGT-mediated PK |

| `pgp` | P-glycoprotein |

| `bcrp` | BCRP transporter |

| `oatp` | OATP transporters |

| `pd` | Pharmacodynamic overlap |

| `pk` | Alias for all PK mechanisms |

| `all` | All domains, default |

  

---

  

## Streamlit App

  

If Streamlit is installed, PharmDS can also run as a lightweight web app.

  

```bash

streamlit  run  streamlit_app.py

```

  

The Streamlit interface provides:

  

- Drug input

- Pairwise interaction summaries

- Detailed hit output

- Regimen-level summaries

- Repeated PD risk domains

- Top interaction pairs

  

---

  

## Validation and Testing

  

PharmDS includes validation and test coverage for the rule/data layer.

  

Run the full test suite:

  

```bash

pytest  -q

```

  

Run Ruff:

  

```bash

ruff  check  .

```

  

Auto-fix Ruff issues where possible:

  

```bash

ruff  check  .  --fix

```

  

Validate rule definitions:

  

```bash

python  -m  rules.validate_rules

```

  

The project includes tests for:

  

- Rule evaluation

- Golden interaction scenarios

- Negative/no-hit baseline scenarios

- Rule definition validation

- Regimen summary behavior

- JSON output structure

- Normalized severity/action rationale helpers

- CLI/API-style payload generation

  

These tests are intended to protect against silent rule drift, noisy alerting, and accidental output schema regressions.

  

---

  

## Rule Definition Philosophy

  

Rules are defined as structured JSON files under:

  

```text

rules/rule_defs/

```

  

Rule definitions include:

  

- Stable rule ID

- Human-readable name

- Domain

- Severity

- Action class

- Logic block

- Explanation template

- Suggested actions

- Optional references

- Optional tags

  

Example rule shape:

  

```json

{
  "id": "PD_NAUSEA_ADDITIVE",
  "name": "Additive nausea risk",
  "domain": "PD",
  "severity": "caution",
  "rule_class": "adjust_monitor",
  "actions": [
    "Use caution when combining agents that may increase nausea.",
    "Monitor for gastrointestinal intolerance, especially after initiation or dose increases."
  ],
  "logic": {
    "pd_overlap": {
      "effect_id": "nausea",
      "min_magnitude": "medium"
    }
  },
  "explanation_template": "{A_name} and {B_name} can both contribute to nausea or gastrointestinal intolerance. Combined use may increase additive nausea burden, especially after initiation or dose changes."
}


```

  

Supported rule logic includes:

  

-  `enzyme`

-  `transporter`

-  `pd_overlap`

-  `drug_pair`

  

Transporter rules may target either specific transporter IDs or transporter

families, depending on the mechanism.

  

---

  

## Project Structure

  

```text

pharmds/
├── app/ CLI, rendering, JSON output, and user-facing service helpers
├── core/ Core models, enums, and normalization utilities
├── reasoning/ PK/PD reasoning, summaries, explanation, and rationale helpers
├── rules/ Rule definitions, rule validation, and evaluation engine
├── data/ Curated drug, enzyme, transporter, and PD-effect data
├── docs/ Contribution guides and design notes
├── tests/ Unit tests, golden scenarios, and negative/no-hit baselines
├── streamlit_app.py Streamlit web interface
├── README.md
├── ROADMAP.md
├── LICENSE
└── DISCLAIMER.txt

```
  

---

  

## Design Philosophy

  

PharmDS favors explainability and structural correctness over breadth.


Core principles:

  

- Mechanistic pharmacology over opaque scoring

- Explicit directionality for PK interactions

- Deterministic rule evaluation

- Structured PD ontology instead of ad hoc pair lists

- Conservative severity escalation

- Transporter-aware and Phase II-aware PK modeling

- Reusable rule definitions

- Rule validation before expansion

- Negative tests to reduce alert fatigue

- Regimen-level summaries without replacing pairwise detail

- Educational explanations that separate mechanism, rationale, and suggested actions

---

  

## Current Limitations

  

PharmDS is intentionally conservative and incomplete.

  

Known limitations:

  

- Drug coverage is curated and limited

- Absence of an interaction does not mean absence of risk

- Patient-specific factors are only lightly modeled

- Dose, route, pharmacogenomics, organ impairment, labs, ECG values, and timing are not fully modeled

- Rule references are educational and not a replacement for primary clinical sources

- Output is not clinical advice

  

---

  

## Disclaimer

  

**This software is provided for educational purposes only.**

  

It is not a medical device and must not be used for diagnosis, treatment, prescribing, medication management, or patient care.

  

Always consult qualified healthcare professionals and authoritative references when making clinical decisions.
