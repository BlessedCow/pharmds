# Reviewed catalog notes

The note backfill covers all 107 medications and substances in the supplied
catalog. Each entry has a 41–66 word clinical note. Prescription-drug notes
describe the mechanism or disposition, interaction context, and important
label warnings. Botanical and unregulated-substance notes explain product
variability and the limits of the clinical evidence. These are educational
catalog descriptions, not administration or prescribing advice.

`data/curation/catalog_note_backfill.json` records the note text, the SHA-256
of the previous note, display brand names, and one or more primary sources for
each entry. Most prescription entries link to their DailyMed product label.
Other entries link to original clinical studies or regulator publications.
The cited strength on a dosage option has its own product-specific source;
the note source does not authorize strengths for other forms or products.

From the repository root, merge the reviewed notes into your local catalog:

```powershell
.\.venv\Scripts\python.exe -m tools.apply_catalog_note_backfill
```

The merge updates a note only when it still matches the earlier catalog
version. It reports and preserves locally edited notes and any medications
you added. It fills brand display names only when that field is absent. It
validates the result and creates a timestamped backup before replacing the
file; running it again is safe. If a local note was edited, compare it with
the reviewed note and its source in the JSON ledger, then choose your wording
in the curation GUI.

If you use an existing SQLite database and want these notes reflected in its
`drug` rows, run the targeted update after merging:

```powershell
.\.venv\Scripts\python.exe -m data.migrate_drug_notes --db data\pharmds.sqlite3
```

This only updates notes on existing drug rows. It does not add or delete
medications or replace strengths, relationships, or patient data. The brand
column is GUI display metadata in `drugs.json`; it does not change the API
drug schema.
