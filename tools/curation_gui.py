from __future__ import annotations

import copy
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import (
    END,
    BooleanVar,
    PanedWindow,
    StringVar,
    Tk,
    messagebox,
    ttk,
)
from tkinter.scrolledtext import ScrolledText

import core.constants as constants
from core.constants import normalize_pd_effect_id, normalize_transporter_id
from core.formulations import RELEASE_TYPE_OPTIONS, ROUTE_OPTIONS
from data.curation.validate import (
    known_enzyme_ids,
    known_transporter_ids,
    validate_drugs_curation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DRUGS_PATH = REPO_ROOT / "data" / "curation" / "drugs.json"
RULE_DIR = REPO_ROOT / "rules" / "rule_defs"
BACKUP_DIR = Path.home() / ".pharmds" / "curation_backups"

THERAPEUTIC_INDEX_OPTIONS = ("wide", "moderate", "narrow")
PD_DIRECTION_OPTIONS = ("increase", "decrease")
PD_MAGNITUDE_OPTIONS = ("low", "medium", "high")
HALF_LIFE_OPTIONS = ("short", "medium", "long")
PK_ROLE_OPTIONS = ("substrate", "inhibitor", "inducer")
PK_STRENGTH_OPTIONS = ("", "weak", "moderate", "strong")
DOSAGE_FORM_OPTIONS = (
    "tablet",
    "capsule",
    "oral solution",
    "oral suspension",
    "injection",
    "patch",
    "spray",
    "other",
)
DRUG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_+-]*$")


def normalize_identity(value: str) -> str:
    return value.strip().casefold()


def split_aliases(value: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    for raw in value.split(","):
        alias = raw.strip()
        if not alias:
            continue

        key = normalize_identity(alias)
        if key in seen:
            continue

        seen.add(key)
        out.append(alias)

    return out


def build_identity_index(
    drugs: list[dict],
    *,
    exclude_drug_id: str | None = None,
) -> dict[str, list[tuple[str, str, str]]]:
    index: dict[str, list[tuple[str, str, str]]] = {}

    for drug in drugs:
        drug_id = str(drug.get("id", "")).strip()

        if exclude_drug_id and drug_id == exclude_drug_id:
            continue

        values = [
            ("id", drug_id),
            ("generic_name", str(drug.get("generic_name", "")).strip()),
        ]
        values.extend(
            ("alias", str(alias).strip())
            for alias in drug.get("aliases", []) or []
        )

        for kind, value in values:
            if not value:
                continue

            index.setdefault(normalize_identity(value), []).append(
                (drug_id, kind, value),
            )

    return index


def find_identity_conflicts(
    *,
    drugs: list[dict],
    drug_id: str,
    generic_name: str,
    aliases: list[str],
    exclude_drug_id: str | None = None,
) -> list[str]:
    index = build_identity_index(
        drugs,
        exclude_drug_id=exclude_drug_id,
    )

    proposed: list[tuple[str, str]] = [
        ("drug id", drug_id),
        ("generic name", generic_name),
    ]
    proposed.extend(("alias", alias) for alias in aliases)

    conflicts: list[str] = []
    seen_proposed: dict[str, str] = {}

    for kind, value in proposed:
        normalized = normalize_identity(value)

        if not normalized:
            continue

        previous_kind = seen_proposed.get(normalized)
        if previous_kind is not None:
            identity_pair = {previous_kind, kind}

            if identity_pair != {"drug id", "generic name"}:
                conflicts.append(
                    f"{kind} '{value}' duplicates the proposed "
                    f"{previous_kind}.",
                )
        else:
            seen_proposed[normalized] = kind

        for existing_drug_id, existing_kind, existing_value in index.get(
            normalized,
            [],
        ):
            conflicts.append(
                f"{kind} '{value}' conflicts with {existing_kind} "
                f"'{existing_value}' on '{existing_drug_id}'.",
            )

    return conflicts


def load_payload(path: Path = DRUGS_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_pd_effect_ids(
    *,
    rule_dir: Path = RULE_DIR,
) -> tuple[str, ...]:
    effect_ids = {
        str(value)
        for name, value in vars(constants).items()
        if name.startswith("PD_EFFECT_") and isinstance(value, str)
    }

    if rule_dir.exists():
        for path in rule_dir.glob("pd_*.json"):
            raw = json.loads(path.read_text(encoding="utf-8"))
            logic = raw.get("logic", {}) or {}

            overlap = logic.get("pd_overlap") or {}
            overlap_effect = overlap.get("effect_id")
            if isinstance(overlap_effect, str) and overlap_effect.strip():
                effect_ids.add(normalize_pd_effect_id(overlap_effect.strip()))

            explicit_effect = logic.get("effect_id")
            if isinstance(explicit_effect, str) and explicit_effect.strip():
                effect_ids.add(normalize_pd_effect_id(explicit_effect.strip()))

    return tuple(sorted(effect_ids, key=str.casefold))


def duplicate_pd_effect_ids(pd_effects: list[dict]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()

    for effect in pd_effects:
        effect_id = normalize_pd_effect_id(
            str(effect.get("effect_id", "")).strip(),
        )

        if not effect_id:
            continue

        if effect_id in seen:
            duplicates.add(effect_id)
        else:
            seen.add(effect_id)

    return duplicates


def atomic_save_payload(
    payload: dict,
    *,
    path: Path = DRUGS_PATH,
    backup_dir: Path = BACKUP_DIR,
) -> Path:
    path = path.resolve()
    backup_dir.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(
        prefix=f"{path.stem}.",
        suffix=".tmp.json",
        dir=path.parent,
    )
    os.close(fd)
    temp_path = Path(temp_name)

    try:
        temp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        errors = validate_drugs_curation(temp_path)
        if errors:
            message = "\n".join(
                f"{error.path}: {error.message}"
                for error in errors
            )
            raise ValueError(
                "Curation validation failed before save:\n" + message,
            )

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = backup_dir / f"drugs-{timestamp}.json"
        shutil.copy2(path, backup_path)
        os.replace(temp_path, path)
        return backup_path
    finally:
        if temp_path.exists():
            temp_path.unlink()


class PharmDSCurationGui:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("PharmDS Medication & PD Curation")
        self.root.geometry("1280x820")
        self.root.minsize(1100, 720)

        self.payload = load_payload()
        self.drugs: list[dict] = self.payload["drugs"]
        self.effect_ids = canonical_pd_effect_ids()
        self.enzyme_ids = known_enzyme_ids()
        self.transporter_ids = known_transporter_ids()
        self.current_drug_id: str | None = None
        self.current_record: dict | None = None
        self.formulations: list[dict] = []
        self.dosage_options: list[dict] = []
        self.enzymes: list[dict] = []
        self.transporters: list[dict] = []
        self.pd_effects: list[dict] = []

        self.search_var = StringVar()
        self.id_var = StringVar()
        self.generic_var = StringVar()
        self.class_var = StringVar()
        self.ti_var = StringVar(value="moderate")
        self.aliases_var = StringVar()
        self.half_life_var = StringVar(value="medium")
        self.prodrug_var = BooleanVar(value=False)
        self.active_metabolite_var = BooleanVar(value=False)
        self.renal_clearance_var = BooleanVar(value=False)

        self.form_route_var = StringVar(value="oral")

        self.dosage_value_var = StringVar()
        self.dosage_unit_var = StringVar(value="mg")
        self.dosage_form_var = StringVar(value="tablet")
        self.dosage_route_var = StringVar(value="oral")
        self.dosage_release_var = StringVar(value="ir")
        self.selected_dosage_key: tuple | None = None

        self.enzyme_id_var = StringVar()
        self.enzyme_role_var = StringVar(value="substrate")
        self.enzyme_strength_var = StringVar()
        self.enzyme_fraction_var = StringVar()

        self.transporter_id_var = StringVar()
        self.transporter_role_var = StringVar(value="substrate")
        self.transporter_strength_var = StringVar()

        self.pd_effect_var = StringVar()
        self.pd_direction_var = StringVar(value="increase")
        self.pd_magnitude_var = StringVar(value="medium")

        self._build_ui()
        self._refresh_drug_list()
        self._new_medication()

    def _build_ui(self) -> None:
        outer = PanedWindow(
            self.root,
            orient="horizontal",
            sashwidth=8,
            sashrelief="raised",
            bd=0,
            relief="flat",
        )
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        left = ttk.Frame(outer, padding=8)
        right = ttk.Frame(outer, padding=8)

        outer.add(
            left,
            minsize=260,
            width=340,
            stretch="always",
        )
        outer.add(
            right,
            minsize=640,
            stretch="always",
        )

        ttk.Label(
            left,
            text="Medications",
            font=("", 14, "bold"),
        ).pack(anchor="w")

        search = ttk.Entry(left, textvariable=self.search_var)
        search.pack(fill="x", pady=(8, 6))
        search.bind("<KeyRelease>", lambda _event: self._refresh_drug_list())

        self.drug_list = ttk.Treeview(
            left,
            columns=("generic",),
            show="tree headings",
            height=28,
        )
        self.drug_list.heading("#0", text="ID")
        self.drug_list.heading("generic", text="Generic name")
        self.drug_list.column(
            "#0",
            width=160,
            minwidth=100,
            stretch=True,
        )
        self.drug_list.column(
            "generic",
            width=180,
            minwidth=120,
            stretch=True,
        )
        self.drug_list.pack(fill="both", expand=True)
        self.drug_list.bind("<<TreeviewSelect>>", self._select_drug)

        ttk.Button(
            left,
            text="New medication",
            command=self._new_medication,
        ).pack(fill="x", pady=(8, 0))

        header = ttk.Frame(right)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Medication curation",
            font=("", 16, "bold"),
        ).pack(side="left")

        ttk.Button(
            header,
            text="Save medication",
            command=self._save_current,
        ).pack(side="right")

        self.status_var = StringVar(
            value="Ready. Changes are not written until Save medication.",
        )
        ttk.Label(
            right,
            textvariable=self.status_var,
            foreground="#555555",
        ).pack(fill="x", pady=(6, 8))

        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        identity_tab = ttk.Frame(notebook, padding=12)
        formulations_tab = ttk.Frame(notebook, padding=12)
        dosages_tab = ttk.Frame(notebook, padding=12)
        enzymes_tab = ttk.Frame(notebook, padding=12)
        transporters_tab = ttk.Frame(notebook, padding=12)
        pd_tab = ttk.Frame(notebook, padding=12)

        notebook.add(identity_tab, text="Medication")
        notebook.add(formulations_tab, text="Formulations")
        notebook.add(dosages_tab, text="Dosages")
        notebook.add(enzymes_tab, text="Enzymes")
        notebook.add(transporters_tab, text="Transporters")
        notebook.add(pd_tab, text="PD Effects")

        self._build_identity_tab(identity_tab)
        self._build_formulations_tab(formulations_tab)
        self._build_dosages_tab(dosages_tab)
        self._build_enzymes_tab(enzymes_tab)
        self._build_transporters_tab(transporters_tab)
        self._build_pd_tab(pd_tab)

    def _build_identity_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Drug ID", self.id_var),
            ("Generic name", self.generic_var),
            ("Drug class", self.class_var),
            ("Aliases (comma separated)", self.aliases_var),
        ]

        row = 0
        for label, variable in fields:
            ttk.Label(frame, text=label).grid(
                row=row,
                column=0,
                sticky="nw",
                padx=(0, 12),
                pady=6,
            )
            ttk.Entry(frame, textvariable=variable).grid(
                row=row,
                column=1,
                sticky="ew",
                pady=6,
            )
            row += 1

        ttk.Label(frame, text="Therapeutic index").grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=6,
        )
        ttk.Combobox(
            frame,
            textvariable=self.ti_var,
            values=THERAPEUTIC_INDEX_OPTIONS,
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        ttk.Label(frame, text="Half-life bucket").grid(
            row=row,
            column=0,
            sticky="w",
            padx=(0, 12),
            pady=6,
        )
        ttk.Combobox(
            frame,
            textvariable=self.half_life_var,
            values=HALF_LIFE_OPTIONS,
            state="readonly",
        ).grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        flags = ttk.Frame(frame)
        flags.grid(row=row, column=1, sticky="w", pady=6)
        ttk.Checkbutton(
            flags,
            text="Prodrug",
            variable=self.prodrug_var,
        ).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(
            flags,
            text="Active metabolite",
            variable=self.active_metabolite_var,
        ).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(
            flags,
            text="Renal clearance flag",
            variable=self.renal_clearance_var,
        ).pack(side="left")
        ttk.Label(frame, text="Parameters").grid(
            row=row,
            column=0,
            sticky="nw",
            padx=(0, 12),
            pady=6,
        )
        row += 1

        ttk.Label(frame, text="Notes").grid(
            row=row,
            column=0,
            sticky="nw",
            padx=(0, 12),
            pady=6,
        )
        self.notes_text = ScrolledText(frame, height=8, wrap="word")
        self.notes_text.grid(
            row=row,
            column=1,
            sticky="nsew",
            pady=6,
        )
        frame.rowconfigure(row, weight=1)

    def _build_formulations_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(
            frame,
            text=(
                "Each route is unique. Select one or more release types, "
                "then add/update the route."
            ),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.form_tree = ttk.Treeview(
            frame,
            columns=("release_types",),
            show="tree headings",
        )
        self.form_tree.heading("#0", text="Route")
        self.form_tree.heading("release_types", text="Release types")
        self.form_tree.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 12),
        )
        self.form_tree.bind(
            "<<TreeviewSelect>>",
            self._select_formulation,
        )

        controls = ttk.Frame(frame)
        controls.grid(row=1, column=1, sticky="nsew")

        ttk.Label(controls, text="Route").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.form_route_var,
            values=ROUTE_OPTIONS,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))

        ttk.Label(controls, text="Release types").pack(anchor="w")
        self.release_list = ttk.Treeview(
            controls,
            columns=("selected",),
            show="tree headings",
            height=10,
        )
        self.release_list.heading("#0", text="Type")
        self.release_list.heading("selected", text="Use")
        self.release_list.column("#0", width=80)
        self.release_list.column("selected", width=50, anchor="center")
        self.release_list.pack(fill="x", pady=(2, 8))
        self.release_list.bind("<Double-1>", self._toggle_release_type)

        for release_type in RELEASE_TYPE_OPTIONS:
            self.release_list.insert(
                "",
                "end",
                iid=release_type,
                text=release_type,
                values=("No",),
            )

        ttk.Button(
            controls,
            text="Add / update formulation",
            command=self._add_formulation,
        ).pack(fill="x", pady=3)
        ttk.Button(
            controls,
            text="Remove selected formulation",
            command=self._remove_formulation,
        ).pack(fill="x", pady=3)

    def _build_dosages_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Label(
            frame,
            text=(
                "Curated marketed/reference strengths only. These entries do not "
                "represent prescribing recommendations."
            ),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.dosage_tree = ttk.Treeview(
            frame,
            columns=("unit", "form", "route", "release"),
            show="tree headings",
        )
        self.dosage_tree.heading("#0", text="Strength")
        self.dosage_tree.heading("unit", text="Unit")
        self.dosage_tree.heading("form", text="Dosage form")
        self.dosage_tree.heading("route", text="Route")
        self.dosage_tree.heading("release", text="Release")
        self.dosage_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        self.dosage_tree.bind("<<TreeviewSelect>>", self._select_dosage)

        controls = ttk.Frame(frame)
        controls.grid(row=1, column=1, sticky="nsew")
        for label, variable in (
            ("Strength value", self.dosage_value_var),
            ("Strength unit", self.dosage_unit_var),
        ):
            ttk.Label(controls, text=label).pack(anchor="w")
            ttk.Entry(controls, textvariable=variable).pack(fill="x", pady=(2, 8))
        ttk.Label(controls, text="Dosage form").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.dosage_form_var,
            values=DOSAGE_FORM_OPTIONS,
        ).pack(fill="x", pady=(2, 8))
        ttk.Label(controls, text="Route").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.dosage_route_var,
            values=ROUTE_OPTIONS,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))
        ttk.Label(controls, text="Release type").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.dosage_release_var,
            values=RELEASE_TYPE_OPTIONS,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))
        ttk.Button(
            controls,
            text="Add / update dosage",
            command=self._add_dosage,
        ).pack(fill="x", pady=3)
        ttk.Button(
            controls,
            text="Remove selected dosage",
            command=self._remove_dosage,
        ).pack(fill="x", pady=3)

    def _build_enzymes_tab(self, frame: ttk.Frame) -> None:
        self._build_pk_role_tab(frame, kind="enzyme")

    def _build_transporters_tab(self, frame: ttk.Frame) -> None:
        self._build_pk_role_tab(frame, kind="transporter")

    def _build_pk_role_tab(self, frame: ttk.Frame, *, kind: str) -> None:
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)
        is_enzyme = kind == "enzyme"
        ids = self.enzyme_ids if is_enzyme else self.transporter_ids
        ttk.Label(
            frame,
            text=(
                "Add substrate, inhibitor, or inducer relationships using the "
                "canonical PharmDS vocabulary."
            ),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        tree = ttk.Treeview(
            frame,
            columns=("role", "strength", "fraction", "notes"),
            show="tree headings",
        )
        tree.heading("#0", text="Enzyme" if is_enzyme else "Transporter")
        tree.heading("role", text="Role")
        tree.heading("strength", text="Strength")
        tree.heading("fraction", text="Fraction metabolized")
        tree.heading("notes", text="Notes")
        tree.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        if is_enzyme:
            self.enzyme_tree = tree
            tree.bind("<<TreeviewSelect>>", self._select_enzyme)
            id_var, role_var, strength_var = (
                self.enzyme_id_var,
                self.enzyme_role_var,
                self.enzyme_strength_var,
            )
        else:
            self.transporter_tree = tree
            tree.bind("<<TreeviewSelect>>", self._select_transporter)
            id_var, role_var, strength_var = (
                self.transporter_id_var,
                self.transporter_role_var,
                self.transporter_strength_var,
            )

        controls = ttk.Frame(frame)
        controls.grid(row=1, column=1, sticky="nsew")
        ttk.Label(controls, text="ID").pack(anchor="w")
        ttk.Combobox(controls, textvariable=id_var, values=ids, state="readonly").pack(
            fill="x", pady=(2, 8)
        )
        ttk.Label(controls, text="Role").pack(anchor="w")
        ttk.Combobox(
            controls, textvariable=role_var, values=PK_ROLE_OPTIONS, state="readonly"
        ).pack(fill="x", pady=(2, 8))
        ttk.Label(controls, text="Strength (optional)").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=strength_var,
            values=PK_STRENGTH_OPTIONS,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))
        if is_enzyme:
            ttk.Label(controls, text="Fraction metabolized (substrates only)").pack(
                anchor="w"
            )
            ttk.Entry(controls, textvariable=self.enzyme_fraction_var).pack(
                fill="x", pady=(2, 8)
            )
            self.enzyme_note_text = ScrolledText(controls, height=6, wrap="word")
            note_widget = self.enzyme_note_text
        else:
            self.transporter_note_text = ScrolledText(controls, height=6, wrap="word")
            note_widget = self.transporter_note_text
        ttk.Label(controls, text="Notes").pack(anchor="w")
        note_widget.pack(fill="x", pady=(2, 8))
        ttk.Button(
            controls,
            text=f"Add / update {kind} role",
            command=self._add_enzyme if is_enzyme else self._add_transporter,
        ).pack(fill="x", pady=3)
        ttk.Button(
            controls,
            text=f"Remove selected {kind} role",
            command=self._remove_enzyme if is_enzyme else self._remove_transporter,
        ).pack(fill="x", pady=3)

    def _build_pd_tab(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(
            frame,
            text=(
                "PD effects are selected from the canonical PharmDS effect "
                "vocabulary. Duplicate effects on one medication are blocked."
            ),
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.pd_tree = ttk.Treeview(
            frame,
            columns=("direction", "magnitude", "note"),
            show="tree headings",
        )
        self.pd_tree.heading("#0", text="Effect")
        self.pd_tree.heading("direction", text="Direction")
        self.pd_tree.heading("magnitude", text="Magnitude")
        self.pd_tree.heading("note", text="Mechanism note")
        self.pd_tree.column("#0", width=185)
        self.pd_tree.column("direction", width=85)
        self.pd_tree.column("magnitude", width=85)
        self.pd_tree.column("note", width=360)
        self.pd_tree.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 12),
        )
        self.pd_tree.bind("<<TreeviewSelect>>", self._select_pd_effect)

        controls = ttk.Frame(frame)
        controls.grid(row=1, column=1, sticky="nsew")

        ttk.Label(controls, text="Effect").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.pd_effect_var,
            values=self.effect_ids,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))

        ttk.Label(controls, text="Direction").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.pd_direction_var,
            values=PD_DIRECTION_OPTIONS,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))

        ttk.Label(controls, text="Magnitude").pack(anchor="w")
        ttk.Combobox(
            controls,
            textvariable=self.pd_magnitude_var,
            values=PD_MAGNITUDE_OPTIONS,
            state="readonly",
        ).pack(fill="x", pady=(2, 8))

        ttk.Label(controls, text="Mechanism note").pack(anchor="w")
        self.pd_note_text = ScrolledText(
            controls,
            height=8,
            wrap="word",
        )
        self.pd_note_text.pack(fill="x", pady=(2, 8))

        ttk.Button(
            controls,
            text="Add / update PD effect",
            command=self._add_pd_effect,
        ).pack(fill="x", pady=3)
        ttk.Button(
            controls,
            text="Remove selected PD effect",
            command=self._remove_pd_effect,
        ).pack(fill="x", pady=3)

    def _refresh_drug_list(self) -> None:
        query = normalize_identity(self.search_var.get())

        for item in self.drug_list.get_children():
            self.drug_list.delete(item)

        for drug in sorted(
            self.drugs,
            key=lambda item: str(item.get("generic_name", "")).casefold(),
        ):
            haystack = " ".join(
                [
                    str(drug.get("id", "")),
                    str(drug.get("generic_name", "")),
                    *[
                        str(alias)
                        for alias in drug.get("aliases", []) or []
                    ],
                ]
            ).casefold()

            if query and query not in haystack:
                continue

            self.drug_list.insert(
                "",
                "end",
                iid=str(drug["id"]),
                text=str(drug["id"]),
                values=(str(drug.get("generic_name", "")),),
            )

    def _select_drug(self, _event=None) -> None:
        selected = self.drug_list.selection()
        if not selected:
            return

        drug_id = selected[0]
        drug = next(
            item for item in self.drugs if item.get("id") == drug_id
        )
        self._load_record(drug)

    def _new_medication(self) -> None:
        self.current_drug_id = None
        self.current_record = None
        self.id_var.set("")
        self.generic_var.set("")
        self.class_var.set("")
        self.ti_var.set("moderate")
        self.aliases_var.set("")
        self.half_life_var.set("medium")
        self.prodrug_var.set(False)
        self.active_metabolite_var.set(False)
        self.renal_clearance_var.set(False)
        self.notes_text.delete("1.0", END)
        self.formulations = []
        self.dosage_options = []
        self.enzymes = []
        self.transporters = []
        self.pd_effects = []
        self._refresh_formulations()
        self._refresh_dosages()
        self._refresh_enzymes()
        self._refresh_transporters()
        self._refresh_pd_effects()
        self.status_var.set("Creating a new medication.")

    def _load_record(self, drug: dict) -> None:
        self.current_record = copy.deepcopy(drug)
        self.current_drug_id = str(drug["id"])
        self.id_var.set(str(drug.get("id", "")))
        self.generic_var.set(str(drug.get("generic_name", "")))
        self.class_var.set(str(drug.get("drug_class", "") or ""))
        self.ti_var.set(str(drug.get("therapeutic_index", "moderate")))
        self.aliases_var.set(", ".join(drug.get("aliases", []) or []))

        params = drug.get("parameters", {}) or {}
        self.half_life_var.set(
            str(params.get("half_life_bucket", "medium") or "medium"),
        )
        self.prodrug_var.set(bool(params.get("prodrug", False)))
        self.active_metabolite_var.set(
            bool(params.get("active_metabolite", False)),
        )
        self.renal_clearance_var.set(
            bool(params.get("renal_clearance_flag", False)),
        )

        self.notes_text.delete("1.0", END)
        self.notes_text.insert("1.0", str(drug.get("notes", "") or ""))

        self.formulations = copy.deepcopy(drug.get("formulations", []) or [])
        self.dosage_options = copy.deepcopy(drug.get("dosage_options", []) or [])
        self.enzymes = copy.deepcopy(drug.get("enzymes", []) or [])
        self.transporters = copy.deepcopy(drug.get("transporters", []) or [])
        self.pd_effects = copy.deepcopy(drug.get("pd_effects", []) or [])
        self._refresh_formulations()
        self._refresh_dosages()
        self._refresh_enzymes()
        self._refresh_transporters()
        self._refresh_pd_effects()
        self.status_var.set(f"Editing '{self.current_drug_id}'.")

    def _selected_release_types(self) -> list[str]:
        selected: list[str] = []

        for release_type in RELEASE_TYPE_OPTIONS:
            if (
                self.release_list.set(release_type, "selected")
                == "Yes"
            ):
                selected.append(release_type)

        return selected

    def _set_selected_release_types(self, values: list[str]) -> None:
        selected = set(values)

        for release_type in RELEASE_TYPE_OPTIONS:
            self.release_list.set(
                release_type,
                "selected",
                "Yes" if release_type in selected else "No",
            )

    def _toggle_release_type(self, event) -> None:
        item = self.release_list.identify_row(event.y)
        if not item:
            return

        current = self.release_list.set(item, "selected")
        self.release_list.set(
            item,
            "selected",
            "No" if current == "Yes" else "Yes",
        )

    def _select_formulation(self, _event=None) -> None:
        selected = self.form_tree.selection()
        if not selected:
            return

        route = selected[0]
        formulation = next(
            item for item in self.formulations if item["route"] == route
        )
        self.form_route_var.set(route)
        self._set_selected_release_types(
            formulation.get("release_types", []),
        )

    def _add_formulation(self) -> None:
        route = self.form_route_var.get().strip().lower()
        release_types = self._selected_release_types()

        if not route:
            messagebox.showerror("Missing route", "Choose a route.")
            return

        if not release_types:
            messagebox.showerror(
                "Missing release type",
                "Select at least one release type.",
            )
            return

        existing = next(
            (
                item
                for item in self.formulations
                if item.get("route") == route
            ),
            None,
        )

        value = {
            "route": route,
            "release_types": release_types,
        }

        if existing is None:
            self.formulations.append(value)
        else:
            existing.clear()
            existing.update(value)

        self._refresh_formulations()

    def _remove_formulation(self) -> None:
        selected = self.form_tree.selection()
        if not selected:
            return

        route = selected[0]
        self.formulations = [
            item
            for item in self.formulations
            if item.get("route") != route
        ]
        self._refresh_formulations()

    def _refresh_formulations(self) -> None:
        for item in self.form_tree.get_children():
            self.form_tree.delete(item)

        for formulation in sorted(
            self.formulations,
            key=lambda item: str(item.get("route", "")),
        ):
            route = str(formulation["route"])
            self.form_tree.insert(
                "",
                "end",
                iid=route,
                text=route,
                values=(", ".join(formulation.get("release_types", [])),),
            )

        self._set_selected_release_types([])

    @staticmethod
    def _dosage_key(option: dict) -> tuple:
        return (
            str(option.get("route", "")).strip().lower(),
            str(option.get("release_type", "")).strip().lower(),
            str(option.get("dosage_form", "")).strip().casefold(),
            float(option.get("strength_value", 0)),
            str(option.get("strength_unit", "")).strip().casefold(),
        )

    def _select_dosage(self, _event=None) -> None:
        selected = self.dosage_tree.selection()
        if not selected:
            return
        option = self.dosage_options[int(selected[0])]
        self.selected_dosage_key = self._dosage_key(option)
        self.dosage_value_var.set(str(option["strength_value"]))
        self.dosage_unit_var.set(str(option["strength_unit"]))
        self.dosage_form_var.set(str(option["dosage_form"]))
        self.dosage_route_var.set(str(option["route"]))
        self.dosage_release_var.set(str(option["release_type"]))

    def _add_dosage(self) -> None:
        try:
            strength_value = float(self.dosage_value_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid strength", "Strength value must be numeric.")
            return
        if strength_value <= 0:
            messagebox.showerror(
                "Invalid strength",
                "Strength value must be greater than 0.",
            )
            return
        option = {
            "route": self.dosage_route_var.get().strip().lower(),
            "release_type": self.dosage_release_var.get().strip().lower(),
            "dosage_form": self.dosage_form_var.get().strip(),
            "strength_value": strength_value,
            "strength_unit": self.dosage_unit_var.get().strip(),
        }
        if not option["dosage_form"] or not option["strength_unit"]:
            messagebox.showerror(
                "Missing dosage fields", "Dosage form and strength unit are required."
            )
            return
        valid_pairs = {
            (str(item["route"]).lower(), str(release).lower())
            for item in self.formulations
            for release in item.get("release_types", [])
        }
        if (option["route"], option["release_type"]) not in valid_pairs:
            messagebox.showerror(
                "Unknown formulation",
                "Add the matching route/release type on the Formulations tab first.",
            )
            return
        new_key = self._dosage_key(option)
        if self.selected_dosage_key is not None:
            self.dosage_options = [
                item
                for item in self.dosage_options
                if self._dosage_key(item) != self.selected_dosage_key
            ]
        elif any(
            self._dosage_key(item) == new_key
            for item in self.dosage_options
        ):
            messagebox.showerror(
                "Duplicate dosage",
                "That dosage option already exists.",
            )
            return
        self.dosage_options.append(option)
        self._refresh_dosages()

    def _remove_dosage(self) -> None:
        selected = self.dosage_tree.selection()
        if not selected:
            return
        index = int(selected[0])
        self.dosage_options.pop(index)
        self._refresh_dosages()

    def _refresh_dosages(self) -> None:
        if not hasattr(self, "dosage_tree"):
            return
        for item in self.dosage_tree.get_children():
            self.dosage_tree.delete(item)
        self.dosage_options.sort(key=self._dosage_key)
        for index, option in enumerate(self.dosage_options):
            self.dosage_tree.insert(
                "",
                "end",
                iid=str(index),
                text=str(option.get("strength_value", "")),
                values=(
                    option.get("strength_unit", ""),
                    option.get("dosage_form", ""),
                    option.get("route", ""),
                    option.get("release_type", ""),
                ),
            )
        self.selected_dosage_key = None
        self.dosage_value_var.set("")

    def _select_enzyme(self, _event=None) -> None:
        selected = self.enzyme_tree.selection()
        if not selected:
            return
        enzyme_id, role = selected[0].split("|", 1)
        item = next(
            value
            for value in self.enzymes
            if value.get("enzyme_id") == enzyme_id and value.get("role") == role
        )
        self.enzyme_id_var.set(enzyme_id)
        self.enzyme_role_var.set(role)
        self.enzyme_strength_var.set(str(item.get("strength") or ""))
        self.enzyme_fraction_var.set(
            ""
            if item.get("fraction_metabolized") is None
            else str(item["fraction_metabolized"])
        )
        self.enzyme_note_text.delete("1.0", END)
        self.enzyme_note_text.insert("1.0", str(item.get("notes") or ""))

    def _add_enzyme(self) -> None:
        enzyme_id = self.enzyme_id_var.get().strip()
        role = self.enzyme_role_var.get().strip()
        if enzyme_id not in self.enzyme_ids:
            messagebox.showerror("Unknown enzyme", "Choose a canonical enzyme ID.")
            return
        fraction = None
        raw_fraction = self.enzyme_fraction_var.get().strip()
        if raw_fraction:
            if role != "substrate":
                messagebox.showerror(
                    "Invalid fraction",
                    "Fraction metabolized is only valid for substrates.",
                )
                return
            try:
                fraction = float(raw_fraction)
            except ValueError:
                messagebox.showerror("Invalid fraction", "Use a number from 0 to 1.")
                return
            if not 0 <= fraction <= 1:
                messagebox.showerror("Invalid fraction", "Use a number from 0 to 1.")
                return
        value = {"enzyme_id": enzyme_id, "role": role}
        if self.enzyme_strength_var.get():
            value["strength"] = self.enzyme_strength_var.get()
        if fraction is not None:
            value["fraction_metabolized"] = fraction
        note = self.enzyme_note_text.get("1.0", END).strip()
        if note:
            value["notes"] = note
        self.enzymes = [
            item
            for item in self.enzymes
            if not (item.get("enzyme_id") == enzyme_id and item.get("role") == role)
        ]
        self.enzymes.append(value)
        self._refresh_enzymes()

    def _remove_enzyme(self) -> None:
        selected = self.enzyme_tree.selection()
        if not selected:
            return
        enzyme_id, role = selected[0].split("|", 1)
        self.enzymes = [
            item
            for item in self.enzymes
            if not (item.get("enzyme_id") == enzyme_id and item.get("role") == role)
        ]
        self._refresh_enzymes()

    def _refresh_enzymes(self) -> None:
        if not hasattr(self, "enzyme_tree"):
            return
        for item in self.enzyme_tree.get_children():
            self.enzyme_tree.delete(item)
        for item in sorted(
            self.enzymes,
            key=lambda value: (value["enzyme_id"], value["role"]),
        ):
            iid = f"{item['enzyme_id']}|{item['role']}"
            self.enzyme_tree.insert(
                "", "end", iid=iid, text=item["enzyme_id"],
                values=(
                    item["role"], item.get("strength", ""),
                    item.get("fraction_metabolized", ""), item.get("notes", ""),
                ),
            )
        self.enzyme_id_var.set("")
        self.enzyme_role_var.set("substrate")
        self.enzyme_strength_var.set("")
        self.enzyme_fraction_var.set("")
        if hasattr(self, "enzyme_note_text"):
            self.enzyme_note_text.delete("1.0", END)

    def _select_transporter(self, _event=None) -> None:
        selected = self.transporter_tree.selection()
        if not selected:
            return
        transporter_id, role = selected[0].split("|", 1)
        item = next(
            value
            for value in self.transporters
            if normalize_transporter_id(
                value.get("transporter_id", "")
            )
            == transporter_id
            and value.get("role") == role
        )
        self.transporter_id_var.set(transporter_id)
        self.transporter_role_var.set(role)
        self.transporter_strength_var.set(str(item.get("strength") or ""))
        self.transporter_note_text.delete("1.0", END)
        self.transporter_note_text.insert("1.0", str(item.get("notes") or ""))

    def _add_transporter(self) -> None:
        transporter_id = normalize_transporter_id(
            self.transporter_id_var.get().strip()
        )
        role = self.transporter_role_var.get().strip()
        if transporter_id not in self.transporter_ids:
            messagebox.showerror(
                "Unknown transporter",
                "Choose a canonical transporter ID.",
            )
            return
        value = {"transporter_id": transporter_id, "role": role}
        if self.transporter_strength_var.get():
            value["strength"] = self.transporter_strength_var.get()
        note = self.transporter_note_text.get("1.0", END).strip()
        if note:
            value["notes"] = note
        self.transporters = [
            item
            for item in self.transporters
            if not (
                normalize_transporter_id(
                    item.get("transporter_id", "")
                )
                == transporter_id
                and item.get("role") == role
            )
        ]
        self.transporters.append(value)
        self._refresh_transporters()

    def _remove_transporter(self) -> None:
        selected = self.transporter_tree.selection()
        if not selected:
            return
        transporter_id, role = selected[0].split("|", 1)
        self.transporters = [
            item
            for item in self.transporters
            if not (
                normalize_transporter_id(
                    item.get("transporter_id", "")
                )
                == transporter_id
                and item.get("role") == role
            )
        ]
        self._refresh_transporters()

    def _refresh_transporters(self) -> None:
        if not hasattr(self, "transporter_tree"):
            return
        for item in self.transporter_tree.get_children():
            self.transporter_tree.delete(item)
        for item in sorted(
            self.transporters,
            key=lambda value: (
                normalize_transporter_id(value["transporter_id"]),
                value["role"],
            ),
        ):
            transporter_id = normalize_transporter_id(item["transporter_id"])
            iid = f"{transporter_id}|{item['role']}"
            self.transporter_tree.insert(
                "", "end", iid=iid, text=transporter_id,
                values=(
                    item["role"],
                    item.get("strength", ""),
                    "",
                    item.get("notes", ""),
                ),
            )
        self.transporter_id_var.set("")
        self.transporter_role_var.set("substrate")
        self.transporter_strength_var.set("")
        if hasattr(self, "transporter_note_text"):
            self.transporter_note_text.delete("1.0", END)

    def _select_pd_effect(self, _event=None) -> None:
        selected = self.pd_tree.selection()
        if not selected:
            return

        effect_id = selected[0]
        effect = next(
            item
            for item in self.pd_effects
            if item["effect_id"] == effect_id
        )

        self.pd_effect_var.set(effect_id)
        self.pd_direction_var.set(str(effect.get("direction", "increase")))
        self.pd_magnitude_var.set(str(effect.get("magnitude", "medium")))
        self.pd_note_text.delete("1.0", END)
        self.pd_note_text.insert(
            "1.0",
            str(effect.get("mechanism_note", "") or ""),
        )

    def _add_pd_effect(self) -> None:
        effect_id = normalize_pd_effect_id(
            self.pd_effect_var.get().strip(),
        )

        if not effect_id or effect_id not in self.effect_ids:
            messagebox.showerror(
                "Unknown PD effect",
                "Choose an effect from the canonical PharmDS list.",
            )
            return

        value = {
            "effect_id": effect_id,
            "direction": self.pd_direction_var.get(),
            "magnitude": self.pd_magnitude_var.get(),
            "mechanism_note": self.pd_note_text.get("1.0", END).strip(),
        }

        existing = next(
            (
                effect
                for effect in self.pd_effects
                if normalize_pd_effect_id(effect["effect_id"])
                == effect_id
            ),
            None,
        )

        if existing is None:
            self.pd_effects.append(value)
        else:
            replace = messagebox.askyesno(
                "PD effect already exists",
                (
                    f"'{effect_id}' is already assigned to this medication. "
                    "Update the existing entry instead?"
                ),
            )
            if not replace:
                return

            existing.clear()
            existing.update(value)

        self._refresh_pd_effects()

    def _remove_pd_effect(self) -> None:
        selected = self.pd_tree.selection()
        if not selected:
            return

        effect_id = selected[0]
        self.pd_effects = [
            effect
            for effect in self.pd_effects
            if effect.get("effect_id") != effect_id
        ]
        self._refresh_pd_effects()

    def _refresh_pd_effects(self) -> None:
        for item in self.pd_tree.get_children():
            self.pd_tree.delete(item)

        for effect in sorted(
            self.pd_effects,
            key=lambda item: str(item.get("effect_id", "")).casefold(),
        ):
            effect_id = str(effect["effect_id"])
            self.pd_tree.insert(
                "",
                "end",
                iid=effect_id,
                text=effect_id,
                values=(
                    effect.get("direction", ""),
                    effect.get("magnitude", ""),
                    effect.get("mechanism_note", ""),
                ),
            )

        self.pd_effect_var.set("")
        self.pd_direction_var.set("increase")
        self.pd_magnitude_var.set("medium")
        self.pd_note_text.delete("1.0", END)

    def _build_record(self) -> dict:
        drug_id = self.id_var.get().strip()
        generic_name = self.generic_var.get().strip()
        aliases = split_aliases(self.aliases_var.get())

        if not drug_id:
            raise ValueError("Drug ID is required.")
        if not DRUG_ID_RE.match(drug_id):
            raise ValueError(
                "Drug ID must be lowercase and match "
                "^[a-z0-9][a-z0-9_+-]*$.",
            )
        if not generic_name:
            raise ValueError("Generic name is required.")
        if not self.class_var.get().strip():
            raise ValueError("Drug class is required.")
        if not self.formulations:
            raise ValueError("Add at least one formulation.")

        conflicts = find_identity_conflicts(
            drugs=self.drugs,
            drug_id=drug_id,
            generic_name=generic_name,
            aliases=aliases,
            exclude_drug_id=self.current_drug_id,
        )
        if conflicts:
            raise ValueError(
                "Medication identity conflict:\n"
                + "\n".join(f"- {item}" for item in conflicts),
            )

        duplicates = duplicate_pd_effect_ids(self.pd_effects)
        if duplicates:
            raise ValueError(
                "Duplicate PD effects: "
                + ", ".join(sorted(duplicates)),
            )

        release_types = sorted(
            {
                release_type
                for formulation in self.formulations
                for release_type in formulation.get("release_types", [])
            },
            key=RELEASE_TYPE_OPTIONS.index,
        )

        record = copy.deepcopy(self.current_record or {})
        record.update(
            {
                "id": drug_id,
                "generic_name": generic_name,
                "drug_class": self.class_var.get().strip(),
                "therapeutic_index": self.ti_var.get(),
                "aliases": aliases,
                "release_types": release_types,
                "notes": self.notes_text.get("1.0", END).strip(),
                "dosage_options": copy.deepcopy(self.dosage_options),
                "enzymes": copy.deepcopy(self.enzymes),
                "transporters": copy.deepcopy(self.transporters),
                "pd_effects": copy.deepcopy(self.pd_effects),
                "parameters": {
                    "prodrug": bool(self.prodrug_var.get()),
                    "active_metabolite": bool(
                        self.active_metabolite_var.get(),
                    ),
                    "renal_clearance_flag": bool(
                        self.renal_clearance_var.get(),
                    ),
                    "half_life_bucket": self.half_life_var.get(),
                },
                "formulations": copy.deepcopy(self.formulations),
            }
        )

        return record

    def _save_current(self) -> None:
        try:
            record = self._build_record()
        except ValueError as error:
            messagebox.showerror("Cannot save", str(error))
            return

        payload = copy.deepcopy(self.payload)
        target_drugs = payload["drugs"]

        if self.current_drug_id is None:
            target_drugs.append(record)
        else:
            index = next(
                index
                for index, drug in enumerate(target_drugs)
                if drug.get("id") == self.current_drug_id
            )
            target_drugs[index] = record

        target_drugs.sort(
            key=lambda item: str(item.get("id", "")).casefold(),
        )

        try:
            backup_path = atomic_save_payload(payload)
        except Exception as error:
            messagebox.showerror(
                "Validation failed",
                str(error),
            )
            return

        self.payload = load_payload()
        self.drugs = self.payload["drugs"]
        self.current_drug_id = str(record["id"])
        self.current_record = next(
            copy.deepcopy(drug)
            for drug in self.drugs
            if drug.get("id") == self.current_drug_id
        )
        self._refresh_drug_list()

        self.status_var.set(
            f"Saved '{self.current_drug_id}'. Backup: {backup_path}",
        )
        messagebox.showinfo(
            "Saved",
            (
                f"Medication '{self.current_drug_id}' saved successfully.\n\n"
                f"Backup:\n{backup_path}"
            ),
        )


def main() -> None:
    root = Tk()
    PharmDSCurationGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
