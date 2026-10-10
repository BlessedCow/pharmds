# Getting started with PharmDS

**[Overview](README.md)** · **[Architecture](ARCHITECTURE.md)** · **[Roadmap](ROADMAP.md)**

This guide covers a local Windows development setup, the web app, command line analysis, curation tools, and repository checks. Run commands from the project root, where `README.md` lives.

## Before you begin

| Requirement | Used for |
| :--- | :--- |
| Python **3.11+** | API, CLI, curation editors, seeding, and tests. |
| Node.js and npm | React development server and production build. |
| PowerShell | The commands below use Windows paths. |

### Install dependencies

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm --prefix web ci
```

`requirements-dev.txt` includes runtime dependencies and test tools. The frontend uses `web/package-lock.json` for a reproducible install.

### Prepare the local database

A fresh checkout needs the generated SQLite database:

```powershell
.\.venv\Scripts\python.exe -m data.seed_sqlite
```

> [!CAUTION]
> Seeding **replaces** `data/pharmds.sqlite3`. Starting pytest also deletes and rebuilds it. Back up any local only database edits and put changes you want to keep in curated JSON before either command.

## Run the web app

Open **two PowerShell terminals** in the project root.

| Terminal | Command |
| :--- | :--- |
| **1 · API** | `.\.venv\Scripts\python.exe -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8010` |
| **2 · Frontend** | `npm --prefix web run dev` |

| Open in your browser | URL |
| :--- | :--- |
| PharmDS interface | **http://127.0.0.1:5173/** |
| Interactive API reference | **http://127.0.0.1:8010/docs** |

The API root `http://127.0.0.1:8010/` returns 404 by design. Vite forwards frontend `/api` requests to the API on port 8010. If that port is occupied, change the Uvicorn port and the target in `web/vite.config.ts` together.

## Analyze from a terminal

The command line tool does not require the frontend server:

```powershell
.\.venv\Scripts\python.exe -m app.cli fluvoxamine tizanidine --details --format rich
.\.venv\Scripts\python.exe -m app.cli --help
```

| Option | Use |
| :--- | :--- |
| `--format plain` | Readable text; the default. |
| `--format rich --details` | Tables and full pairwise details. |
| `--format json` | Structured output for another tool. |
| `--domain` | Limit results to a supported interaction domain. |
| `--file PATH` | Supply a list of substances from a file. |

Use `--help` for the complete and current option list. The example names are present in the curated catalog.

## Curate medications

There are **two desktop editors** for the same underlying data:

| Editor | Launch command | Guide |
| :--- | :--- | :--- |
| Original GUI | `.\.venv\Scripts\python.exe -m tools.curation_gui` | [Original GUI](docs/curation_gui.md) |
| Curation Studio | `.\.venv\Scripts\python.exe -m tools.curation_studio` | [Studio](docs/curation_studio.md) |

Both edit `data/curation/drugs.json` and provide a sourced PK editor for `data/curation/pk_observations.json`. Each window loads its own copy, so avoid editing the same medication in both at once. Read the [strength options](docs/strength_options.md) and [PK observations](docs/pk_observations.md) guides before entering product or measurement data.

### Know which files are authoritative

| File or folder | What it holds | Keep in Git? |
| :--- | :--- | :--- |
| `data/curation/drugs.json` | Profiles, formulations, and curated product strengths. | Yes |
| `data/curation/pk_observations.json` | Source specific PK measurements and context. | Yes |
| `data/evidence/`, `rules/rule_defs/` | Evidence records and interaction definitions. | Yes |
| `data/curation/` manifests and backfill inputs | Curation and import inputs. | Yes |
| `data/pharmds.sqlite3` | Rebuilt local database. | No |
| `reference/expanded_*.json`, `evidence_gap_report.json` | Generated snapshots and reports. | No |

`.gitignore` leaves local generated files in place while excluding them from future Git adds. Already tracked files require `git rm --cached <path>` to stop tracking them without deleting the local copy.

A labeled product strength is **not** a prescribed dose. A PK observation is tied to its source, formulation, analyte, population, and conditions; it is not a universal patient concentration prediction. See [regimen timing](docs/regimen_timing.md) for the scope of educational timing calculations.

## Check your changes

```powershell
.\.venv\Scripts\python.exe -m pytest -n auto -q
.\.venv\Scripts\python.exe -m ruff check .
npm --prefix web run build
```

Run the Python checks after curation, rule, or service edits; build the frontend after changes to `web/`. Tests regenerate the local database as noted above.

## Find the right document

| Need | Document |
| :--- | :--- |
| Add a drug or rule | [Adding a drug](docs/ADDING_A_DRUG.txt) · [Adding a rule](docs/ADDING_A_RULE.txt) |
| Understand analysis ownership | [Architecture](ARCHITECTURE.md) |
| See planned work | [Roadmap](ROADMAP.md) |
| Review limitations | [Safety](docs/safety.md) · [Disclaimer](DISCLAIMER.txt) |
| Contribute to the project | [Contributing](CONTRIBUTING.md) |

Most `docs/*.md` and `docs/*.txt` files are guidance or source review history and have no direct runtime effect. **Four Markdown audits are read by tests:** `docs/audits/composite_rule_parity.md`, `pairwise_comparison_harness.md`, `explicit_pair_rule_gap_audit.md`, and `pd_threshold_suppression_parity.md`. Keep them if you run the full suite. `docs/__init__.py` is a Python package marker. Older scope and coverage documents may contain historical counts; curated JSON is the current source of truth.
