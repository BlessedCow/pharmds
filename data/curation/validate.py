from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import core.constants as c
from core.constants import normalize_pd_effect_id, normalize_transporter_id
from core.formulations import (
    RELEASE_TYPE_OPTIONS,
    ROUTE_OPTIONS,
)
from data.loaders import load_transporters

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PATH = BASE_DIR / "data" / "curation" / "drugs.json"

_ALLOWED_TI = {"wide", "moderate", "narrow"}
_ALLOWED_ROLE = {"substrate", "inhibitor", "inducer"}
_ALLOWED_STRENGTH = {"weak", "moderate", "strong"}
_ALLOWED_PD_DIR = {"increase", "decrease"}
_ALLOWED_PD_MAG = {"low", "medium", "high"}
_ALLOWED_HALF_LIFE = {"short", "medium", "long"}

_ALLOWED_ROUTES = set(ROUTE_OPTIONS)
_ALLOWED_RELEASE_TYPES = set(RELEASE_TYPE_OPTIONS)

# Keep in sync with data.seed_sqlite enzymes. v0: small curated set.
_KNOWN_ENZYMES = {
    "CYP3A4",
    "CYP2C9",
    "CYP2C19",
    "CYP2A6",
    "CYP2D6",
    "CYP1A2",
    "CYP2B6",
    "UGT1A1",
    "UGT2B7",
}

_DRUG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_+-]*$")


def known_enzyme_ids() -> tuple[str, ...]:
    return tuple(sorted(_KNOWN_ENZYMES, key=str.casefold))


def known_transporter_ids() -> tuple[str, ...]:
    return tuple(sorted(load_transporters(), key=str.casefold))


@dataclass(frozen=True)
class CurationError:
    path: str
    message: str


def _load_rule_pd_effect_ids() -> set[str]:
    """Infer PD effect ids that are currently used by PD rules.

    This keeps validation aligned with the actual rule set in rules/rule_defs.
    """
    rule_dir = BASE_DIR / "rules" / "rule_defs"
    out: set[str] = set()
    for p in rule_dir.glob("pd_*.json"):
        raw = json.loads(p.read_text(encoding="utf-8"))
        logic = raw.get("logic", {}) or {}
        po = logic.get("pd_overlap") or {}
        eff = po.get("effect_id")
        if isinstance(eff, str) and eff.strip():
            out.add(normalize_pd_effect_id(eff.strip()))
    return out


def validate_drugs_curation(path: Path = DEFAULT_PATH) -> list[CurationError]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    errors: list[CurationError] = []

    if not isinstance(raw, dict):
        return [CurationError(str(path), "Root must be a JSON object.")]

    if raw.get("version") != 1:
        errors.append(CurationError(str(path), "Expected version=1."))

    drugs = raw.get("drugs")
    if not isinstance(drugs, list):
        errors.append(CurationError(str(path), "Expected key 'drugs' to be a list."))
        return errors
    PD_EFFECT_IDS = {v for k, v in vars(c).items() if k.startswith("PD_EFFECT_")}
    transporters = load_transporters()
    known_transporters = set(transporters.keys())
    known_pd_effects = PD_EFFECT_IDS | _load_rule_pd_effect_ids()

    seen_drug_ids: set[str] = set()
    seen_aliases: dict[str, str] = {}  # alias -> drug_id

    for i, d in enumerate(drugs):
        prefix = f"drugs[{i}]"
        if not isinstance(d, dict):
            errors.append(CurationError(prefix, "Drug must be an object."))
            continue

        drug_id = d.get("id")
        if not isinstance(drug_id, str) or not drug_id.strip():
            errors.append(CurationError(prefix + ".id", "Missing or empty drug id."))
            continue
        drug_id = drug_id.strip()

        if not _DRUG_ID_RE.match(drug_id):
            errors.append(
                CurationError(
                    prefix + ".id",
                    "Drug id must be lowercase and match ^[a-z0-9][a-z0-9_+-]*$.",
                )
            )

        if drug_id in seen_drug_ids:
            errors.append(CurationError(prefix + ".id", f"Duplicate id '{drug_id}'."))
        seen_drug_ids.add(drug_id)

        generic = d.get("generic_name")
        if not isinstance(generic, str) or not generic.strip():
            errors.append(
                CurationError(prefix + ".generic_name", "Missing generic_name.")
            )

        ti = d.get("therapeutic_index")
        if ti not in _ALLOWED_TI:
            errors.append(
                CurationError(
                    prefix + ".therapeutic_index",
                    f"therapeutic_index must be one of {sorted(_ALLOWED_TI)}.",
                )
            )

        # Aliases
        aliases = d.get("aliases", [])
        if aliases is None:
            aliases = []
        if not isinstance(aliases, list):
            errors.append(CurationError(prefix + ".aliases", "aliases must be a list."))
            aliases = []

        norm_aliases: list[str] = []
        for a in aliases:
            if not isinstance(a, str) or not a.strip():
                errors.append(
                    CurationError(
                        prefix + ".aliases",
                        "Alias must be a non-empty string.",
                    )
                )
                continue
            a_norm = a.strip().lower()
            norm_aliases.append(a_norm)

        # Alias uniqueness (per drug and global)
        if len(set(norm_aliases)) != len(norm_aliases):
            errors.append(
                CurationError(
                    prefix + ".aliases",
                    "Duplicate aliases within the same drug.",
                )
            )

        for a in norm_aliases:
            # prevent alias collisions with other drugs and drug ids
            if a in seen_drug_ids and a != drug_id:
                errors.append(
                    CurationError(
                        prefix + ".aliases",
                        f"Alias '{a}' collides with another drug id.",
                    )
                )
            if a in seen_aliases and seen_aliases[a] != drug_id:
                errors.append(
                    CurationError(
                        prefix + ".aliases",
                        f"Alias '{a}' already used by '{seen_aliases[a]}'.",
                    )
                )
            seen_aliases[a] = drug_id

        # Release types
        release_types = d.get("release_types")

        if release_types is not None:
            if not isinstance(release_types, list):
                errors.append(
                    CurationError(
                        prefix + ".release_types",
                        "release_types must be a list.",
                    )
                )
            else:
                normalized_release_types: list[str] = []

                for release_type in release_types:
                    if not isinstance(release_type, str) or not release_type.strip():
                        errors.append(
                            CurationError(
                                prefix + ".release_types",
                                "release type must be a non-empty string.",
                            )
                        )
                        continue

                    normalized = release_type.strip().lower()
                    normalized_release_types.append(normalized)

                    if normalized not in _ALLOWED_RELEASE_TYPES:
                        errors.append(
                            CurationError(
                                prefix + ".release_types",
                                (
                                    f"Unknown release type '{normalized}'. "
                                    "Expected one of "
                                    f"{sorted(_ALLOWED_RELEASE_TYPES)}."
                                ),
                            )
                        )

                if not normalized_release_types:
                    errors.append(
                        CurationError(
                            prefix + ".release_types",
                            "release_types must contain at least one value.",
                        )
                    )

                if len(set(normalized_release_types)) != len(normalized_release_types):
                    errors.append(
                        CurationError(
                            prefix + ".release_types",
                            "Duplicate release types for this drug.",
                        )
                    )

        # Formulations
        formulations = d.get("formulations")

        if formulations is not None:
            if not isinstance(formulations, list):
                errors.append(
                    CurationError(
                        prefix + ".formulations",
                        "formulations must be a list.",
                    )
                )
            elif not formulations:
                errors.append(
                    CurationError(
                        prefix + ".formulations",
                        "formulations must contain at least one value.",
                    )
                )
            else:
                seen_routes: set[str] = set()
                formulation_release_types: set[str] = set()

                for j, formulation in enumerate(formulations):
                    formulation_prefix = f"{prefix}.formulations[{j}]"

                    if not isinstance(formulation, dict):
                        errors.append(
                            CurationError(
                                formulation_prefix,
                                "formulation must be an object.",
                            )
                        )
                        continue

                    route = formulation.get("route")

                    if not isinstance(route, str) or not route.strip():
                        errors.append(
                            CurationError(
                                formulation_prefix + ".route",
                                "route must be a non-empty string.",
                            )
                        )
                        continue

                    normalized_route = route.strip().lower()

                    if normalized_route not in _ALLOWED_ROUTES:
                        errors.append(
                            CurationError(
                                formulation_prefix + ".route",
                                (
                                    f"Unknown route '{normalized_route}'. "
                                    "Expected one of "
                                    f"{sorted(_ALLOWED_ROUTES)}."
                                ),
                            )
                        )

                    if normalized_route in seen_routes:
                        errors.append(
                            CurationError(
                                formulation_prefix + ".route",
                                (
                                    "Duplicate formulation route "
                                    f"'{normalized_route}' for this drug."
                                ),
                            )
                        )

                    seen_routes.add(normalized_route)

                    formulation_release_values = formulation.get("release_types")

                    if not isinstance(
                        formulation_release_values,
                        list,
                    ):
                        errors.append(
                            CurationError(
                                formulation_prefix + ".release_types",
                                "release_types must be a list.",
                            )
                        )
                        continue

                    if not formulation_release_values:
                        errors.append(
                            CurationError(
                                formulation_prefix + ".release_types",
                                ("release_types must contain at least " "one value."),
                            )
                        )
                        continue

                    normalized_values: list[str] = []

                    for release_type in formulation_release_values:
                        if (
                            not isinstance(release_type, str)
                            or not release_type.strip()
                        ):
                            errors.append(
                                CurationError(
                                    formulation_prefix + ".release_types",
                                    ("release type must be a " "non-empty string."),
                                )
                            )
                            continue

                        normalized_release_type = release_type.strip().lower()

                        normalized_values.append(normalized_release_type)

                        if normalized_release_type not in _ALLOWED_RELEASE_TYPES:
                            errors.append(
                                CurationError(
                                    formulation_prefix + ".release_types",
                                    (
                                        "Unknown release type "
                                        f"'{normalized_release_type}'. "
                                        "Expected one of "
                                        f"{sorted(_ALLOWED_RELEASE_TYPES)}."
                                    ),
                                )
                            )

                        formulation_release_types.add(normalized_release_type)

                    if len(set(normalized_values)) != len(normalized_values):
                        errors.append(
                            CurationError(
                                formulation_prefix + ".release_types",
                                ("Duplicate release types for this " "formulation."),
                            )
                        )

                if isinstance(release_types, list):
                    normalized_flat_release_types = {
                        release_type.strip().lower()
                        for release_type in release_types
                        if isinstance(release_type, str) and release_type.strip()
                    }

                    if normalized_flat_release_types != formulation_release_types:
                        errors.append(
                            CurationError(
                                prefix + ".formulations",
                                (
                                    "Formulation release types must match "
                                    "the drug-level release_types values."
                                ),
                            )
                        )

        # Dosage / strength options
        dosage_options = d.get("dosage_options", [])
        if dosage_options is None:
            dosage_options = []
        if not isinstance(dosage_options, list):
            errors.append(
                CurationError(
                    prefix + ".dosage_options",
                    "dosage_options must be a list.",
                )
            )
            dosage_options = []

        formulation_pairs: set[tuple[str, str]] = set()
        if isinstance(formulations, list):
            for formulation in formulations:
                if not isinstance(formulation, dict):
                    continue
                route = formulation.get("route")
                release_values = formulation.get("release_types")
                if not isinstance(route, str) or not isinstance(release_values, list):
                    continue
                for release_value in release_values:
                    if isinstance(release_value, str):
                        formulation_pairs.add(
                            (route.strip().lower(), release_value.strip().lower())
                        )

        seen_dosages: set[tuple[str, str, str, float, str]] = set()
        for j, dosage in enumerate(dosage_options):
            p2 = f"{prefix}.dosage_options[{j}]"
            if not isinstance(dosage, dict):
                errors.append(CurationError(p2, "dosage option must be an object."))
                continue

            route = dosage.get("route")
            release_type = dosage.get("release_type")
            dosage_form = dosage.get("dosage_form")
            strength_value = dosage.get("strength_value")
            strength_unit = dosage.get("strength_unit")

            normalized_route = (
                route.strip().lower() if isinstance(route, str) else ""
            )
            normalized_release = (
                release_type.strip().lower()
                if isinstance(release_type, str)
                else ""
            )

            if normalized_route not in _ALLOWED_ROUTES:
                errors.append(
                    CurationError(
                        p2 + ".route",
                        f"route must be one of {sorted(_ALLOWED_ROUTES)}.",
                    )
                )
            if normalized_release not in _ALLOWED_RELEASE_TYPES:
                errors.append(
                    CurationError(
                        p2 + ".release_type",
                        (
                            "release_type must be one of "
                            f"{sorted(_ALLOWED_RELEASE_TYPES)}."
                        ),
                    )
                )
            if (normalized_route, normalized_release) not in formulation_pairs:
                errors.append(
                    CurationError(
                        p2,
                        (
                            "dosage route/release_type must match an existing "
                            "formulation for this drug."
                        ),
                    )
                )

            if not isinstance(dosage_form, str) or not dosage_form.strip():
                errors.append(
                    CurationError(
                        p2 + ".dosage_form",
                        "dosage_form must be a non-empty string.",
                    )
                )
            if (
                isinstance(strength_value, bool)
                or not isinstance(strength_value, (int, float))
                or float(strength_value) <= 0
            ):
                errors.append(
                    CurationError(
                        p2 + ".strength_value",
                        "strength_value must be a number greater than 0.",
                    )
                )
                continue
            if not isinstance(strength_unit, str) or not strength_unit.strip():
                errors.append(
                    CurationError(
                        p2 + ".strength_unit",
                        "strength_unit must be a non-empty string.",
                    )
                )
                continue

            key = (
                normalized_route,
                normalized_release,
                str(dosage_form).strip().casefold(),
                float(strength_value),
                strength_unit.strip().casefold(),
            )
            if key in seen_dosages:
                errors.append(
                    CurationError(
                        p2,
                        "Duplicate dosage option for this drug.",
                    )
                )
            seen_dosages.add(key)

        # Enzymes
        enzymes = d.get("enzymes", [])
        if enzymes is None:
            enzymes = []
        if not isinstance(enzymes, list):
            errors.append(CurationError(prefix + ".enzymes", "enzymes must be a list."))
            enzymes = []

        seen_er: set[tuple[str, str]] = set()
        for j, er in enumerate(enzymes):
            p2 = f"{prefix}.enzymes[{j}]"
            if not isinstance(er, dict):
                errors.append(CurationError(p2, "enzyme role must be an object."))
                continue
            enzyme_id = er.get("enzyme_id")
            role = er.get("role")

            if enzyme_id not in _KNOWN_ENZYMES:
                errors.append(
                    CurationError(
                        p2 + ".enzyme_id",
                        f"Unknown enzyme_id '{enzyme_id}'.",
                    )
                )

            if role not in _ALLOWED_ROLE:
                errors.append(
                    CurationError(
                        p2 + ".role",
                        f"role must be one of {sorted(_ALLOWED_ROLE)}.",
                    )
                )

            key = (str(enzyme_id), str(role))
            if key in seen_er:
                errors.append(
                    CurationError(
                        p2,
                        "Duplicate (enzyme_id, role) for this drug.",
                    )
                )
            seen_er.add(key)

            strength = er.get("strength")
            if strength is not None and strength not in _ALLOWED_STRENGTH:
                errors.append(
                    CurationError(
                        p2 + ".strength",
                        f"strength must be one of {sorted(_ALLOWED_STRENGTH)}.",
                    )
                )

            fm = er.get("fraction_metabolized")
            if fm is not None:
                if role != "substrate":
                    errors.append(
                        CurationError(
                            p2 + ".fraction_metabolized",
                            "Only allowed for role='substrate'.",
                        )
                    )
                if not isinstance(fm, (int, float)) or not (0.0 <= float(fm) <= 1.0):
                    errors.append(
                        CurationError(
                            p2 + ".fraction_metabolized",
                            "Must be a number between 0 and 1.",
                        )
                    )

        # Transporters
        transport = d.get("transporters", [])
        if transport is None:
            transport = []
        if not isinstance(transport, list):
            errors.append(
                CurationError(
                    prefix + ".transporters",
                    "transporters must be a list.",
                )
            )
            transport = []

        seen_tr: set[tuple[str, str]] = set()
        for j, tr in enumerate(transport):
            p2 = f"{prefix}.transporters[{j}]"
            if not isinstance(tr, dict):
                errors.append(CurationError(p2, "transporter role must be an object."))
                continue
            raw_tid = tr.get("transporter_id")
            if not isinstance(raw_tid, str) or not raw_tid.strip():
                errors.append(
                    CurationError(
                        p2 + ".transporter_id",
                        "Missing transporter_id.",
                    )
                )
                continue
            tid = normalize_transporter_id(raw_tid)
            tr["transporter_id"] = tid  # normalized in memory, seed normalizes too

            role = tr.get("role")
            if role not in _ALLOWED_ROLE:
                errors.append(
                    CurationError(
                        p2 + ".role",
                        f"role must be one of {sorted(_ALLOWED_ROLE)}.",
                    )
                )

            if tid not in known_transporters:
                errors.append(
                    CurationError(
                        p2 + ".transporter_id",
                        f"Unknown transporter_id '{tid}'.",
                    )
                )

            key = (tid, str(role))
            if key in seen_tr:
                errors.append(
                    CurationError(
                        p2,
                        "Duplicate (transporter_id, role) for this drug.",
                    )
                )
            seen_tr.add(key)

            strength = tr.get("strength")
            if strength is not None and strength not in _ALLOWED_STRENGTH:
                errors.append(
                    CurationError(
                        p2 + ".strength",
                        f"strength must be one of {sorted(_ALLOWED_STRENGTH)}.",
                    )
                )

        # PD effects
        pd = d.get("pd_effects", [])
        if pd is None:
            pd = []
        if not isinstance(pd, list):
            errors.append(
                CurationError(prefix + ".pd_effects", "pd_effects must be a list.")
            )
            pd = []

        seen_pd: set[str] = set()
        for j, pe in enumerate(pd):
            p2 = f"{prefix}.pd_effects[{j}]"
            if not isinstance(pe, dict):
                errors.append(CurationError(p2, "pd_effect must be an object."))
                continue
            raw_eid = pe.get("effect_id")
            if not isinstance(raw_eid, str) or not raw_eid.strip():
                errors.append(CurationError(p2 + ".effect_id", "Missing effect_id."))
                continue
            eid = normalize_pd_effect_id(raw_eid)
            pe["effect_id"] = eid

            if eid not in known_pd_effects:
                errors.append(
                    CurationError(
                        p2 + ".effect_id",
                        f"Unknown effect_id '{eid}'. Must match a known PD effect_id.",
                    )
                )
            if eid in seen_pd:
                errors.append(
                    CurationError(
                        p2 + ".effect_id",
                        "Duplicate effect_id for this drug.",
                    )
                )
            seen_pd.add(eid)

            direction = pe.get("direction")
            magnitude = pe.get("magnitude")
            if direction not in _ALLOWED_PD_DIR:
                errors.append(
                    CurationError(
                        p2 + ".direction",
                        f"direction must be one of {sorted(_ALLOWED_PD_DIR)}.",
                    )
                )
            if magnitude not in _ALLOWED_PD_MAG:
                errors.append(
                    CurationError(
                        p2 + ".magnitude",
                        f"magnitude must be one of {sorted(_ALLOWED_PD_MAG)}.",
                    )
                )

        # Parameters
        params = d.get("parameters")
        if params is not None:
            if not isinstance(params, dict):
                errors.append(
                    CurationError(
                        prefix + ".parameters",
                        "parameters must be an object.",
                    )
                )
            else:
                for b in ["prodrug", "active_metabolite", "renal_clearance_flag"]:
                    v = params.get(b)
                    if v is not None and not isinstance(v, bool):
                        errors.append(
                            CurationError(
                                prefix + f".parameters.{b}",
                                "Must be boolean.",
                            )
                        )

                hl = params.get("half_life_bucket")
                if hl is not None and hl not in _ALLOWED_HALF_LIFE:
                    errors.append(
                        CurationError(
                            prefix + ".parameters.half_life_bucket",
                            (
                                "half_life_bucket must be one of "
                                f"{sorted(_ALLOWED_HALF_LIFE)}."
                            ),
                        )
                    )

    return errors


def assert_valid_drugs_curation(path: Path = DEFAULT_PATH) -> None:
    errors = validate_drugs_curation(path)
    if errors:
        msg = "Drug curation validation failed:\n" + "\n".join(
            f"- {e.path}: {e.message}" for e in errors
        )
        raise ValueError(msg)
