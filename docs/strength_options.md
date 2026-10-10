# Reference strengths and product composition

The `dosage_options` entries in `data/curation/drugs.json` describe the
**labeled strength of a named product** or the composition of a **named study
formulation**. They do not prescribe a dose, establish safety, or represent all
products on the market. The current [coverage report](strength_coverage.md)
lists 680 sourced options for 105 of 107 substances. The
[first](strength_source_review.md), [second](strength_source_review_2.md),
[third](strength_source_review_3.md), [fourth](strength_source_review_4.md), and [fifth](strength_source_review_5.md) batch source reviews list each added formulation and its labeled amount.
The remaining substances and release variants need a specific product or study
formulation with a verifiable composition.

All cataloged prescription and OTC route and release variants have at least
one sourced strength. The 11 route and release variants still without options
belong to alcohol (oral), heroin (intranasal and inhaled), nonmedical cocaine
(inhaled, IV, and topical), nonoral methamphetamine (intranasal, inhaled,
and IV), LSD (sublingual), and 7-hydroxymitragynine (oral). Their
unregulated preparations vary in purity or lack an identifiable labeled
product; a future batch requires an exact preparation and source.

Each option has a route, release type, dosage form, numeric strength, unit,
product name, and HTTPS source URL. `composition` gives needed context such
as the botanical plant part, extract, and standardized constituent percentage.
For example, a 300 mg KSM-66 capsule is **root extract standardized to 5%
withanolides** in the cited study, not a generic 300 mg ashwagandha capsule.
Ginkgo EGb 761 is leaf extract standardized to both flavonol glycosides and
terpenes. A percentage describes the specified constituent of that product,
not its milligram dose or another product's composition.

Concentrations such as ketamine 10 mg/mL identify vial strength, not an
administration amount. Formulation and release must match the medication's
curated routes. The analysis form shows the reference strength but does not
infer a dose per administration or perform dose-based regimen math from it.
One or more tablets, a measured liquid volume, or part of a dose may be used
clinically; a labeled product strength alone cannot tell us which. The PK
observation collection separately records study doses, conditions,
measurements, and citations.

The amoxicillin entries distinguish 250/500 mg capsules, 500/875 mg tablets,
four mg/5 mL suspension concentrations, and the 775 mg extended release
MOXATAG tablet. The MOXATAG citation is a 2008 historical label; its current
availability is unverified. Amitriptyline tablets have six separately labeled
strengths from 10 through 150 mg. Each option links to the label that reports
its amount, form, and release type. Liquid units specify a volume denominator
and should not be interpreted as an administered dose.

For illicit or unregulated preparations without a standardized product,
street dose ranges are not entered as manufactured strengths. The catalog
includes labeled prescription methamphetamine, ketamine injection, and a
medical cocaine nasal solution, but no street dose ranges. Named study
formulations are explicitly marked as such. Clinical trial doses belong with
their study context in the PK observation collection rather than a generic
Strength dropdown option.

First merge the batch into the local `drugs.json`. This step preserves other
locally added medications and notes, creates a backup, and refuses to replace
an option with the same route, release, form, and strength if its product
metadata conflicts. It can be run again safely:

```powershell
.\.venv\Scripts\python.exe -m tools.apply_strength_backfill
```

Then update an **existing** PharmDS database without replacing drug or patient
rows:

```powershell
.\.venv\Scripts\python.exe -m data.migrate_dosage_options --db data\pharmds.sqlite3
```

The migration validates `drugs.json`, adds the three optional metadata
columns to older strength tables, and inserts or updates options by their
drug, route, release, form, value, and unit. It does not create new drug rows
and does not delete options removed from curation. Run it again after changing
strength entries in the Python curation GUI. A new medication must first be
added to the database by the normal drug seeding workflow.
