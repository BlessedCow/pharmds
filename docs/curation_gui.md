# PharmDS Medication Curation GUI

Run from the repository root:

```powershell
python tools/curation_gui.py
```

The tool edits `data/curation/drugs.json` and validates the complete payload before replacing the source file.

Tabs support medication identity, formulations, curated dosage/strength options, enzyme roles, transporter roles, and PD effects. Medication identity and PD duplicates are blocked. Enzyme/transporter IDs come from the same canonical vocabularies used by the validator.

Dosage entries are **reference strength/form options, not prescribing recommendations**. Each option records `strength_value`, `strength_unit`, `dosage_form`, `route`, and `release_type`, and must correspond to an existing formulation.

On save, the GUI creates a timestamped backup under `~/.pharmds/curation_backups`. After curation changes that need to be visible to the API, rebuild/reseed the PharmDS database using the repository's normal database seeding workflow.
