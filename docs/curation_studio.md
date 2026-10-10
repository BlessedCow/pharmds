# PharmDS Curation Studio

The original editor remains available:

```powershell
.\.venv\Scripts\python.exe -m tools.curation_gui
```

The alternate, guided interface is launched separately:

```powershell
.\.venv\Scripts\python.exe -m tools.curation_studio
```

Both programs edit the same local `data/curation/drugs.json`, use the same
validation and backup flow, and share the separate sourced PK editor. Do not
edit the same medication in both windows at once; each window loads its own
copy of the file when it starts.

The Studio groups work into **Profile**, **Products**, **Interactions**, and
**Sourced PK**. Under Products, create the route and release type first, then
curate a strength. Full-height views replace the original stacked editors.
The catalog pane and the table/control panes can be resized. Product details
show the named product, its exact labeled ingredient basis and composition,
with a button to open the linked source. `Ctrl+F` focuses catalog search and
`Ctrl+S` saves the current medication.

For example, ARISTADA `441 mg aripiprazole lauroxil` is the mass of the ester
in the syringe. The product label gives a corresponding amount of aripiprazole,
but the depot formulation has its own dosing schedule and must not be treated
as an interchangeable 300 mg ABILIFY MAINTENA injection. The existing catalog
keeps the ingredient qualifier in `strength_unit` to avoid losing this
distinction. The Studio displays the full unit and composition in the selected
product details area; no drug strength is silently converted.
