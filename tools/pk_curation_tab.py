"""Tkinter editor for the separate, source-linked PK curation collection."""

from __future__ import annotations

import copy
from collections.abc import Callable
from tkinter import BooleanVar, StringVar, messagebox, ttk

from data.curation.pk_observations import DEFAULT_PATH, EVIDENCE_TYPES, METRIC_UNITS
from tools.pk_curation_editor import read_pk_payload, replace_entry, save_pk_payload


class PKCurationTab:
    def __init__(
        self,
        frame: ttk.Frame,
        drug_id: Callable[[], str | None],
        formulations: Callable[[], list[dict]],
    ) -> None:
        self.drug_id = drug_id
        self.formulations = formulations
        self.payload = read_pk_payload()
        self.original_bytes = DEFAULT_PATH.read_bytes()
        self.current_drug_id: str | None = None
        self.selected_source_id: str | None = None
        self.selected_observation_id: str | None = None
        self.status = StringVar(value="Select a saved medication to curate sourced PK.")
        self.source_vars = {
            key: StringVar() for key in ("id", "title", "url", "revision_date")
        }
        self.source_vars["evidence_type"] = StringVar(value="prescribing_label")
        self.obs_vars = {
            key: StringVar()
            for key in (
                "id",
                "route",
                "release_type",
                "metric",
                "min_value",
                "max_value",
                "source_id",
                "population",
                "analyte",
                "administration_condition",
                "dose_value",
                "dose_unit",
                "notes",
            )
        }
        self.obs_vars["metric"].set("half_life")
        self.math_eligible = BooleanVar(value=False)
        self._build(frame)

    def _build(self, frame: ttk.Frame) -> None:
        ttk.Label(
            frame,
            text=(
                "Sourced PK measurements are stored in pk_observations.json, "
                "separately from drug identity and regimen fields."
            ),
            wraplength=770,
        ).pack(anchor="w", pady=(0, 8))
        ttk.Button(frame, text="Save sourced PK", command=self._save).pack(anchor="e")
        ttk.Label(frame, textvariable=self.status, wraplength=780).pack(
            anchor="w", pady=(0, 8)
        )
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)
        measurements = ttk.Frame(notebook, padding=8)
        sources = ttk.Frame(notebook, padding=8)
        notebook.add(measurements, text="Measurements")
        notebook.add(sources, text="Sources")
        self._measurements_ui(measurements)
        self._sources_ui(sources)
        self._refresh_sources()

    def _measurements_ui(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        self.obs_tree = ttk.Treeview(
            frame,
            columns=("metric", "value", "formulation", "source"),
            show="tree headings",
            height=8,
        )
        for key, label in (
            ("#0", "Observation ID"),
            ("metric", "Metric"),
            ("value", "Reported"),
            ("formulation", "Route / release"),
            ("source", "Source"),
        ):
            self.obs_tree.heading(key, text=label)
        self.obs_tree.column("#0", width=210)
        self.obs_tree.column("metric", width=100)
        self.obs_tree.column("value", width=110)
        self.obs_tree.column("formulation", width=110)
        self.obs_tree.column("source", width=170)
        self.obs_tree.grid(row=0, column=0, sticky="nsew")
        self.obs_tree.bind("<<TreeviewSelect>>", self._select_observation)

        fields = ttk.Frame(frame)
        fields.grid(row=1, column=0, sticky="ew", pady=8)
        for column in (1, 3):
            fields.columnconfigure(column, weight=1)
        specs = (
            ("Observation ID", "id"),
            ("Source ID", "source_id"),
            ("Route", "route"),
            ("Release", "release_type"),
            ("Metric", "metric"),
            ("Minimum", "min_value"),
            ("Maximum", "max_value"),
            ("Population", "population"),
            ("Analyte", "analyte"),
            ("Administration condition", "administration_condition"),
            ("Study dose (optional)", "dose_value"),
            ("Dose unit (optional)", "dose_unit"),
            ("Notes", "notes"),
        )
        for index, (label, key) in enumerate(specs):
            row, side = divmod(index, 2)
            ttk.Label(fields, text=label).grid(
                row=row, column=side * 2, sticky="w", padx=(0, 6), pady=3
            )
            if key == "source_id":
                widget = ttk.Combobox(fields, textvariable=self.obs_vars[key])
                self.source_choice = widget
            elif key == "route":
                widget = ttk.Combobox(
                    fields, textvariable=self.obs_vars[key], state="readonly"
                )
                self.route_choice = widget
                widget.bind("<<ComboboxSelected>>", self._route_changed)
            elif key == "release_type":
                widget = ttk.Combobox(
                    fields, textvariable=self.obs_vars[key], state="readonly"
                )
                self.release_choice = widget
            elif key == "metric":
                widget = ttk.Combobox(
                    fields,
                    textvariable=self.obs_vars[key],
                    values=tuple(METRIC_UNITS),
                    state="readonly",
                )
            else:
                widget = ttk.Entry(fields, textvariable=self.obs_vars[key])
            widget.grid(row=row, column=side * 2 + 1, sticky="ew", pady=3)
        ttk.Label(
            frame,
            text=(
                "Enter values exactly as reported for the named analyte, product, "
                "population, and conditions. Describe mean, median, or range in Notes. "
                "Use a study dose only when the source reports one."
            ),
            wraplength=770,
        ).grid(row=1, column=0, sticky="w", pady=2)
        fields.grid_configure(row=2)
        ttk.Checkbutton(
            fields,
            text="Allow educational first-order math (point half-life only)",
            variable=self.math_eligible,
        ).grid(row=7, column=0, columnspan=4, sticky="w", pady=4)
        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, sticky="ew")
        ttk.Button(
            buttons, text="New measurement", command=self._clear_observation
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            buttons, text="Add / update measurement", command=self._stage_observation
        ).pack(side="left", padx=(0, 8))

    def _sources_ui(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        ttk.Label(
            frame,
            text="Sources can be shared by multiple medications. Updating a source "
            "changes its citation everywhere it is used.",
            wraplength=770,
        ).grid(row=0, column=0, sticky="w")
        self.source_tree = ttk.Treeview(
            frame,
            columns=("title", "type"),
            show="tree headings",
            height=11,
        )
        self.source_tree.heading("#0", text="Source ID")
        self.source_tree.heading("title", text="Title")
        self.source_tree.heading("type", text="Evidence")
        self.source_tree.column("#0", width=210)
        self.source_tree.column("title", width=390)
        self.source_tree.column("type", width=130)
        self.source_tree.grid(row=1, column=0, sticky="nsew", pady=8)
        self.source_tree.bind("<<TreeviewSelect>>", self._select_source)
        fields = ttk.Frame(frame)
        fields.grid(row=2, column=0, sticky="ew")
        fields.columnconfigure(1, weight=1)
        for row, (label, key) in enumerate(
            (
                ("Source ID", "id"),
                ("Exact title", "title"),
                ("HTTPS URL", "url"),
                ("Evidence type", "evidence_type"),
                ("Revision date (YYYY-MM-DD, optional)", "revision_date"),
            )
        ):
            ttk.Label(fields, text=label).grid(row=row, column=0, sticky="w", pady=4)
            widget = (
                ttk.Combobox(
                    fields,
                    textvariable=self.source_vars[key],
                    values=tuple(sorted(EVIDENCE_TYPES)),
                    state="readonly",
                )
                if key == "evidence_type"
                else ttk.Entry(fields, textvariable=self.source_vars[key])
            )
            widget.grid(row=row, column=1, sticky="ew", pady=4)
        actions = ttk.Frame(frame)
        actions.grid(row=3, column=0, sticky="w", pady=8)
        ttk.Button(actions, text="New source", command=self._clear_source).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(
            actions, text="Add / update source", command=self._stage_source
        ).pack(side="left")

    def show_drug(self, drug_id: str | None) -> None:
        self.current_drug_id = drug_id
        self.route_choice.configure(
            values=tuple(form["route"] for form in self.formulations())
            if drug_id
            else ()
        )
        self._clear_observation()
        self._refresh_observations()
        self.status.set(
            f"Editing sourced PK for '{drug_id}'. Save PK separately."
            if drug_id
            else "Save the medication before adding sourced PK."
        )

    def _refresh_sources(self) -> None:
        for item in self.source_tree.get_children():
            self.source_tree.delete(item)
        for source in sorted(self.payload["sources"], key=lambda row: row["id"]):
            self.source_tree.insert(
                "",
                "end",
                iid=source["id"],
                text=source["id"],
                values=(source["title"], source["evidence_type"]),
            )
        self.source_choice.configure(
            values=tuple(row["id"] for row in self.payload["sources"])
        )

    def _refresh_observations(self) -> None:
        for item in self.obs_tree.get_children():
            self.obs_tree.delete(item)
        for row in self.payload["observations"]:
            if row["drug_id"] != self.current_drug_id:
                continue
            values = (
                row["metric"],
                f"{row['min_value']}–{row['max_value']} {row['unit']}",
                f"{row['route']} / {row['release_type']}",
                row["source_id"],
            )
            self.obs_tree.insert(
                "", "end", iid=row["id"], text=row["id"], values=values
            )

    def _clear_source(self) -> None:
        self.selected_source_id = None
        for var in self.source_vars.values():
            var.set("")
        self.source_vars["evidence_type"].set("prescribing_label")

    def _select_source(self, _event=None) -> None:
        selected = self.source_tree.selection()
        if not selected:
            return
        row = next(row for row in self.payload["sources"] if row["id"] == selected[0])
        self.selected_source_id = row["id"]
        for key, var in self.source_vars.items():
            var.set(row.get(key) or "")

    def _stage_source(self) -> None:
        values = {key: var.get().strip() for key, var in self.source_vars.items()}
        if not values["id"]:
            messagebox.showerror("Missing source ID", "Enter a stable source ID.")
            return
        if self.selected_source_id and values["id"] != self.selected_source_id:
            messagebox.showerror("Stable source ID", "Use New source for a new ID.")
            return
        entry = {
            "id": values["id"],
            "title": values["title"],
            "url": values["url"],
            "evidence_type": values["evidence_type"],
            "revision_date": values["revision_date"] or None,
        }
        replace_entry(self.payload, "sources", entry)
        self._refresh_sources()
        self.status.set(
            "Source staged. Click Save sourced PK to validate and write it."
        )

    def _clear_observation(self) -> None:
        self.selected_observation_id = None
        for var in self.obs_vars.values():
            var.set("")
        self.obs_vars["metric"].set("half_life")
        self.math_eligible.set(False)
        forms = self.formulations() if self.current_drug_id else []
        if forms:
            self.obs_vars["route"].set(forms[0]["route"])
            self._route_changed()
        else:
            self.release_choice.configure(values=())

    def _route_changed(self, _event=None) -> None:
        route = self.obs_vars["route"].get()
        release_types = next(
            (
                form["release_types"]
                for form in self.formulations()
                if form["route"] == route
            ),
            [],
        )
        self.release_choice.configure(values=tuple(release_types))
        if self.obs_vars["release_type"].get() not in release_types:
            self.obs_vars["release_type"].set(release_types[0] if release_types else "")

    def _select_observation(self, _event=None) -> None:
        selected = self.obs_tree.selection()
        if not selected:
            return
        row = next(
            row for row in self.payload["observations"] if row["id"] == selected[0]
        )
        self.selected_observation_id = row["id"]
        for key, var in self.obs_vars.items():
            var.set("" if row.get(key) is None else str(row[key]))
        self._route_changed()
        self.math_eligible.set(bool(row.get("math_eligible", False)))

    def _stage_observation(self) -> None:
        drug_id = self.drug_id()
        if not drug_id or drug_id != self.current_drug_id:
            messagebox.showerror("Save medication first", "Select a saved medication.")
            return
        values = {key: var.get().strip() for key, var in self.obs_vars.items()}
        try:
            minimum = float(values["min_value"])
            maximum = float(values["max_value"])
            dose = float(values["dose_value"]) if values["dose_value"] else None
        except ValueError:
            messagebox.showerror(
                "Invalid number", "Values and study dose must be numbers."
            )
            return
        if not values["id"]:
            messagebox.showerror(
                "Missing observation ID", "Enter a stable observation ID."
            )
            return
        if (
            self.selected_observation_id
            and values["id"] != self.selected_observation_id
        ):
            messagebox.showerror(
                "Stable observation ID", "Use New measurement for a new ID."
            )
            return
        other = next(
            (row for row in self.payload["observations"] if row["id"] == values["id"]),
            None,
        )
        if other and other["drug_id"] != drug_id:
            messagebox.showerror("ID already used", "Another medication uses this ID.")
            return
        entry = {
            **values,
            "drug_id": drug_id,
            "min_value": minimum,
            "max_value": maximum,
            "dose_value": dose,
            "dose_unit": values["dose_unit"] or None,
            "notes": values["notes"] or None,
            "unit": METRIC_UNITS.get(values["metric"], ""),
            "math_eligible": self.math_eligible.get(),
        }
        replace_entry(self.payload, "observations", entry)
        self._refresh_observations()
        self.status.set(
            "Measurement staged. Click Save sourced PK to validate and write it."
        )

    def _save(self) -> None:
        try:
            backup = save_pk_payload(
                copy.deepcopy(self.payload), expected_bytes=self.original_bytes
            )
        except (ValueError, OSError) as error:
            messagebox.showerror("PK validation failed", str(error))
            return
        self.payload = read_pk_payload()
        self.original_bytes = DEFAULT_PATH.read_bytes()
        self._refresh_sources()
        self._refresh_observations()
        self.status.set(f"Sourced PK saved. Backup: {backup}")
        messagebox.showinfo(
            "Sourced PK saved",
            "Validated and saved sourced PK observations. "
            "Run the PK database migration to make changes visible in the API.\n\n"
            f"Backup: {backup}",
        )
