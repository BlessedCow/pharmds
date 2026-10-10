"""A guided medication curation workspace alongside the original Tk editor.

Run with ``python -m tools.curation_studio``. It shares the original editor's
validation, data model, and save implementation; the original entry point is
kept for existing workflows.
"""

from __future__ import annotations

import webbrowser
from tkinter import PanedWindow, StringVar, Tk, messagebox, ttk

from tools.curation_gui import PharmDSCurationGui
from tools.pk_curation_tab import PKCurationTab


def product_detail(option: dict) -> str:
    """Display the product basis and source context without implying equivalence."""
    name = str(option.get("product_name") or "Unnamed product")
    amount = (
        f"{option.get('strength_value', ''):g}"
        if isinstance(option.get("strength_value"), (int, float))
        else str(option.get("strength_value", ""))
    )
    unit = str(option.get("strength_unit", ""))
    composition = str(option.get("composition") or "Product basis not specified")
    return f"{name}  •  {amount} {unit}\n{composition}"


class CurationStudio(PharmDSCurationGui):
    """Alternate UI over the same curation callbacks and atomic save path."""

    def __init__(self, root: Tk) -> None:
        self._configure_theme(root)
        super().__init__(root)
        root.title("PharmDS Curation Studio")
        root.geometry("1440x900")
        root.minsize(1050, 680)
        root.bind("<Control-s>", self._save_shortcut)
        root.bind("<Control-f>", self._focus_search)

    @staticmethod
    def _configure_theme(root: Tk) -> None:
        root.configure(background="#eef3f6")
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TFrame", background="#eef3f6")
        style.configure("TLabel", background="#eef3f6", foreground="#263443")
        style.configure("TNotebook", background="#eef3f6", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(15, 9), font=("Segoe UI", 10))
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff"), ("!selected", "#dce6ec")],
            foreground=[("selected", "#124b60"), ("!selected", "#344a57")],
        )
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#e5edf1",
            foreground="#263443",
        )
        style.map(
            "Treeview",
            background=[("selected", "#126681")],
            foreground=[("selected", "#ffffff")],
        )
        style.configure("TButton", padding=(10, 6), font=("Segoe UI", 9))
        style.configure(
            "Primary.TButton",
            background="#126681",
            foreground="#ffffff",
            padding=(15, 8),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#0a506a"), ("disabled", "#9aadb6")],
            foreground=[("disabled", "#edf2f4")],
        )
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Hint.TLabel", foreground="#526575", font=("Segoe UI", 9))
        style.configure("TLabelFrame", background="#eef3f6")
        style.configure("TLabelFrame.Label", background="#eef3f6")

    def _build_ui(self) -> None:
        banner = ttk.Frame(self.root, padding=(18, 12))
        banner.pack(fill="x")
        ttk.Label(banner, text="PharmDS", style="Title.TLabel").pack(side="left")
        ttk.Label(banner, text=" / Curation Studio", style="Section.TLabel").pack(
            side="left", padx=(6, 0), pady=(6, 0)
        )
        ttk.Label(
            banner, text="Ctrl+F search    Ctrl+S save", style="Hint.TLabel"
        ).pack(side="right", pady=(6, 0))

        outer = PanedWindow(
            self.root,
            orient="horizontal",
            sashwidth=9,
            sashrelief="raised",
            bd=0,
            relief="flat",
        )
        outer.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        left = ttk.Frame(outer, padding=12)
        right = ttk.Frame(outer, padding=12)
        outer.add(left, width=365, minsize=265, stretch="always")
        outer.add(right, minsize=680, stretch="always")

        ttk.Label(left, text="Catalog", style="Section.TLabel").pack(anchor="w")
        ttk.Label(left, text="Find by name, brand, or ID", style="Hint.TLabel").pack(
            anchor="w", pady=(2, 8)
        )
        self.search = ttk.Entry(left, textvariable=self.search_var)
        self.search.pack(fill="x", pady=(0, 10))
        self.search.bind("<KeyRelease>", lambda _event: self._refresh_drug_list())
        catalog_frame = ttk.Frame(left)
        catalog_frame.pack(fill="both", expand=True)
        self.drug_list = ttk.Treeview(
            catalog_frame,
            columns=("generic", "brands"),
            show="tree headings",
            height=25,
            selectmode="browse",
        )
        for column, title, width in (
            ("#0", "ID", 116),
            ("generic", "Generic", 120),
            ("brands", "Brands", 150),
        ):
            self.drug_list.heading(column, text=title)
            self.drug_list.column(column, width=width, minwidth=85, stretch=False)
        self.drug_list.pack(fill="both", expand=True)
        self._table_scrollbar(catalog_frame, self.drug_list)
        self.drug_list.bind("<<TreeviewSelect>>", self._select_drug)
        ttk.Button(left, text="+  New medication", command=self._new_medication).pack(
            fill="x", pady=(12, 0)
        )

        header = ttk.Frame(right)
        header.pack(fill="x")
        title_block = ttk.Frame(header)
        title_block.pack(side="left", fill="x", expand=True)
        self.header_title = StringVar(value="New medication")
        self.header_subtitle = StringVar(value="Start with the medication profile.")
        ttk.Label(
            title_block, textvariable=self.header_title, style="Title.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            title_block, textvariable=self.header_subtitle, style="Hint.TLabel"
        ).pack(anchor="w", pady=(1, 0))
        ttk.Button(
            header,
            text="Save medication",
            style="Primary.TButton",
            command=self._save_current,
        ).pack(side="right", padx=(12, 0))

        self.status_var = StringVar(
            value="Ready. Changes are saved only when you choose Save."
        )
        ttk.Label(right, textvariable=self.status_var, style="Hint.TLabel").pack(
            fill="x", pady=(9, 10)
        )
        workspace = ttk.Notebook(right)
        workspace.pack(fill="both", expand=True)

        profile = ttk.Frame(workspace, padding=18)
        products = ttk.Frame(workspace, padding=8)
        interactions = ttk.Frame(workspace, padding=8)
        evidence = ttk.Frame(workspace, padding=8)
        workspace.add(profile, text="1  Profile")
        workspace.add(products, text="2  Products")
        workspace.add(interactions, text="3  Interactions")
        workspace.add(evidence, text="4  Sourced PK")

        ttk.Label(
            profile, text="Identity and clinical context", style="Section.TLabel"
        ).pack(anchor="w", pady=(0, 9))
        identity_form = ttk.Frame(profile)
        identity_form.pack(fill="both", expand=True)
        self._build_identity_tab(identity_form)

        ttk.Label(
            products,
            text="Set a route and release type, then enter the product strength.",
            style="Hint.TLabel",
        ).pack(anchor="w", padx=8, pady=(3, 9))
        product_pages = ttk.Notebook(products)
        product_pages.pack(fill="both", expand=True)
        formulations = ttk.Frame(product_pages, padding=8)
        strengths = ttk.Frame(product_pages, padding=8)
        product_pages.add(formulations, text="A  Formulations")
        product_pages.add(strengths, text="B  Strengths and products")
        self._build_formulations_tab(formulations)

        self.selection_info_var = StringVar(
            value="Select a strength to see its product, ingredient basis, and source."
        )
        detail = ttk.Frame(strengths)
        detail.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Label(detail, text="Selected product", style="Section.TLabel").pack(
            anchor="w", pady=(0, 4)
        )
        self.open_source_button = ttk.Button(
            detail,
            text="Open product source",
            command=self._open_selected_source,
            state="disabled",
        )
        self.open_source_button.pack(side="right", padx=(8, 0))
        detail_text = ttk.Label(
            detail,
            textvariable=self.selection_info_var,
            wraplength=450,
            justify="left",
            style="Hint.TLabel",
        )
        detail_text.pack(side="left", fill="x", expand=True)
        detail.bind(
            "<Configure>",
            lambda event: detail_text.configure(
                wraplength=max(
                    220, event.width - self.open_source_button.winfo_width() - 28
                )
            ),
        )
        strength_body = ttk.Frame(strengths)
        strength_body.pack(side="top", fill="both", expand=True)
        self._build_dosages_tab(strength_body)
        self.dosage_tree.column("unit", width=190, minwidth=100, stretch=False)
        self.dosage_tree.column("form", width=175, minwidth=90, stretch=False)

        ttk.Label(
            interactions,
            text="Curate mechanisms and effects using the canonical vocabularies.",
            style="Hint.TLabel",
        ).pack(anchor="w", padx=8, pady=(3, 9))
        mechanism_pages = ttk.Notebook(interactions)
        mechanism_pages.pack(fill="both", expand=True)
        enzymes, transporters, effects = (
            ttk.Frame(mechanism_pages, padding=8),
            ttk.Frame(mechanism_pages, padding=8),
            ttk.Frame(mechanism_pages, padding=8),
        )
        mechanism_pages.add(enzymes, text="Enzymes")
        mechanism_pages.add(transporters, text="Transporters")
        mechanism_pages.add(effects, text="PD effects")
        self._build_enzymes_tab(enzymes)
        self._build_transporters_tab(transporters)
        self._build_pd_tab(effects)
        self.pk_tab = PKCurationTab(
            evidence, lambda: self.current_drug_id, lambda: self.formulations
        )

    def _new_medication(self) -> None:
        super()._new_medication()
        self.header_title.set("New medication")
        self.header_subtitle.set("Start with the medication profile.")
        selected = self.drug_list.selection()
        if selected:
            self.drug_list.selection_remove(*selected)

    def _load_record(self, drug: dict) -> None:
        super()._load_record(drug)
        self._update_header()

    def _update_header(self) -> None:
        self.header_title.set(self.generic_var.get() or "New medication")
        self.header_subtitle.set(
            f"{self.id_var.get()}  •  {len(self.formulations)} formulations  "
            f"•  {len(self.dosage_options)} product strengths"
        )

    def _select_dosage(self, _event=None) -> None:
        super()._select_dosage(_event)
        selected = self.dosage_tree.selection()
        if not selected:
            return
        option = self.dosage_options[int(selected[0])]
        self.selection_info_var.set(product_detail(option))
        self.open_source_button.configure(
            state="normal"
            if str(option.get("source_url", "")).startswith("https://")
            else "disabled"
        )

    def _refresh_dosages(self) -> None:
        super()._refresh_dosages()
        self.selection_info_var.set(
            "Select a strength to see its product, ingredient basis, and source."
        )
        self.open_source_button.configure(state="disabled")

    def _open_selected_source(self) -> None:
        selected = self.dosage_tree.selection()
        if not selected:
            return
        url = str(self.dosage_options[int(selected[0])].get("source_url", ""))
        if not url.startswith("https://"):
            messagebox.showerror("No source", "This product has no HTTPS source URL.")
            return
        webbrowser.open(url)

    def _save_current(self) -> None:
        super()._save_current()
        if self.status_var.get().startswith("Saved '"):
            self._update_header()

    def _save_shortcut(self, _event=None) -> None:
        self._save_current()

    def _focus_search(self, _event=None) -> None:
        self.search.focus_set()
        self.search.select_range(0, "end")


def main() -> None:
    root = Tk()
    CurationStudio(root)
    root.mainloop()


if __name__ == "__main__":
    main()
