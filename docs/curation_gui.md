# PharmDS Medication Curation GUI

For the alternate guided interface, see [Curation Studio](curation_studio.md).

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m tools.curation_gui
```

The tool edits `data/curation/drugs.json` and validates the complete payload before replacing the source file.

Tabs support medication identity, a combined **Formulations & strengths** page, enzyme roles, transporter roles, and PD effects. Drag the vertical divider between the two sections and the horizontal divider between each table and its controls to resize them. The controls scroll vertically when the window is short. The medication list shows ID, generic name, and curated brand names and has an adjustable left/right pane width. Medication identity and PD duplicates are blocked. Enzyme/transporter IDs come from the same canonical vocabularies used by the validator.

The **Sourced PK** tab edits `data/curation/pk_observations.json`, separately
from `drugs.json`. Save a new medication and its formulations first, then add
an HTTPS source on the Sources subtab and a measurement on the Measurements
subtab. Select the exact route, release type, analyte, population, reported
values, conditions, and source. Notes should preserve whether the value is a
mean, median, or range and identify the product. Source IDs and observation IDs
are stable; use New to create another. Changes are staged until **Save sourced
PK**, which validates the complete collection and creates its own backup.
Measurements are not inferred from a regimen or copied into drug identity.
The educational math flag defaults to off and only accepts a positive, single
valued half life when explicitly selected.

Dosage entries are **reference strength/form options, not prescribing recommendations**. Each option records `strength_value`, `strength_unit`, `dosage_form`, `route`, and `release_type`, and must correspond to an existing formulation.
The Strength options section can also record a product name, composition, and HTTPS source. For an oral solution, suspension, syrup, or concentrate, select the amount unit separately from the **Per volume (mL)** field. A strength of 100 mg per 5 mL is entered as value `100`, unit `mg`, and volume `5`; it is stored as `100` and `mg/5 mL` for compatibility with existing data. Selecting a legacy `mg/5mL` option splits it into those editor fields. Other dosage forms retain a single unit field, including injectable `mg/mL`.
See [reference strengths](strength_options.md) for the meaning of these fields
and the in-place database migration.

Brand names are separate display metadata under Medication. Existing aliases remain available for searching and matching. Newly entered brands are added to aliases when necessary, so an entered brand also resolves to that medication. The reviewed note and brand-name batch can be merged without replacing locally edited medication records; see [catalog notes](catalog_notes.md).

On save, the GUI creates a timestamped backup under `~/.pharmds/curation_backups`. After curation changes that need to be visible to the API, rebuild/reseed the PharmDS database using the repository's normal database seeding workflow.

After saving sourced PK, update an existing database without rebuilding drug
rows:

```powershell
.\.venv\Scripts\python.exe -m data.migrate_pk_observations --db data\pharmds.sqlite3
```

The GUI prevents medication edits that would invalidate a previously sourced
observation's formulation. Existing PK entries stay in their separate file.
