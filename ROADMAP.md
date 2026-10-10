# Roadmap

**[Overview](README.md)** · **[Getting started](GETTING_STARTED.md)** · **[Architecture](ARCHITECTURE.md)**

PharmDS is an educational project in active development. This board describes what exists and what to improve next; it does not assign release dates or promise clinical use.

## Shipped foundation

| Area | Current capability |
| :--- | :--- |
| **Interfaces** | React web app, FastAPI, command line tool, original curation GUI, and Curation Studio. |
| **Catalog** | Curated drug facts, formulation matched strength options, sourced PK observations, and evidence records. |
| **Interaction engine** | Deterministic enzyme, transporter, PD, explicit pair, and composite rules with pairwise details and regimen summaries. |
| **Mechanism view** | Aggregate concerns and educational summaries alongside established pairwise findings. |
| **Verification** | Curation, rule, mechanism, parity, and API tests; frontend production build. |

## Priority board

| Priority | Work | What “done” would look like |
| :---: | :--- | :--- |
| **1** | **Source accuracy** | Strengths and PK observations match the exact product, formulation, dose or study condition, analyte, and source; ambiguities are recorded. |
| **2** | **Interaction coverage** | High value relationships have sourced rules and positive **and negative** tests; enzyme and transporter terms stay consistent. |
| **3** | **Result consistency** | Pairwise rule output and aggregate mechanism summaries agree on their shared facts and communicate severity clearly. |
| **4** | **Curation workflow** | Both editors make route, release type, concentration unit, source, and PK context easier to verify before saving. |
| **5** | **Project maintenance** | Historical coverage pages and examples are refreshed; generated artifacts stay local and canonical inputs remain clear. |

Work on the two analysis paths should move in small, tested steps. Pairwise rule behavior remains authoritative for established pair reports until a specific handoff has passed parity checks. The [architecture](ARCHITECTURE.md#how-an-analysis-is-built) explains that boundary.

## Explore later

| Idea | Condition before adopting it |
| :--- | :--- |
| **Conditional regimen reasoning** | The user supplies an actual dose and schedule; product strength alone cannot fill them in. |
| **Evidence and alert review** | Uncertainty and source conflicts remain visible without hiding underlying rule hits. |
| **Educational exports and visualization** | Outputs retain references, assumptions, and the scope of each conclusion. |

## Scope guardrails

The catalog is not a complete prescribing database. Source specific PK values and interaction rules do not account for every patient factor. PharmDS does not diagnose, select therapy, or calculate a safe individualized dose. See the [safety guidance](docs/safety.md) and [disclaimer](DISCLAIMER.txt).
