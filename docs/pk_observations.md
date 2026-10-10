# Sourced PK observations

`data/curation/pk_observations.json` stores measurements separately from
`data/curation/drugs.json`, product strengths, and a patient's prescribed
regimen. The collection has 162 label observations for 59 substances. A
separate [coverage report](pk_coverage.md) lists each of the 107 substances
and its uncurated route and release combinations. The observations name
their products and reported statistics in their notes.
The bupropion half-life standard deviation is recorded in notes, not
mistaken for a measured minimum or maximum. A mean, median, range, standard
deviation, and percentile interval must stay distinguishable in notes and
study conditions. Other formulations have no source-linked measurement
until separately curated.

Each source needs a stable ID, exact title, HTTPS URL, evidence type
(`prescribing_label`, `clinical_study`, or `review`), and an optional ISO
revision date. Each observation needs its own stable ID and source ID, a
drug ID, route and release type that match a curated formulation, a metric,
minimum and maximum reported values, the population, analyte, and
administration condition. A dose and its unit are required together for
`cmax` and `auc` observations. A product strength is a separate reference
option and does not establish the dose used in a study.

The current canonical metrics and units are:

| Metric | Unit |
| --- | --- |
| `half_life` | `hours` |
| `tmax` | `hours` |
| `bioavailability` | `fraction` (0 to 1) |
| `cmax` | `ng/mL` |
| `auc` | `ng*h/mL` |

Convert reported measurements to these units before curation and keep the
original source available. Preserve distinct observations when studies,
populations, dose, or formulation differ. The loader does not select a
universal value or resolve conflicting sources. The legacy PK timing examples
are not automatically promoted into this collection.

To add the tables and curated observations to an existing SQLite database
without rebuilding its drug rows, run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m data.migrate_pk_observations --db data\pharmds.sqlite3
```

The migration validates the curation file before updating observations and
can be run again. It adds the calculation flag to databases created before
this backfill. `get_pk_observations()` returns every matching measurement
with its source for inspection, rather than choosing a default for clinical
use. `core.pk_math.first_order` provides idealized, traceable fraction
calculations independently of drug interaction severity and patient
concentration estimates.

The API exposes `GET /drugs/{drug_id}/pk-observations` with optional
`route` and `release_type` filters. The drug database panel loads these
records on demand and shows the source URL and label date. The optional
`GET /drugs/{drug_id}/pk-observations/{observation_id}/math?elapsed_hours=24`
returns two educational first-order fraction traces only for a positive,
single-valued sourced half-life explicitly marked `math_eligible` during
curation. New observations default to false. The response includes inputs, formula,
substitution, source ID, assumptions, and limits. It does not infer a
patient's concentration, regimen, or clinical effect.
