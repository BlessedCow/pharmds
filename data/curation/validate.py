from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import core.constants as c
from core.constants import normalize_pd_effect_id, normalize_transporter_id
from data.loaders import load_transporters

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PATH = BASE_DIR / "data" / "curation" / "drugs.json"

_ALLOWED_TI = {"wide", "moderate", "narrow"}
_ALLOWED_ROLE = {"substrate", "inhibitor", "inducer"}
_ALLOWED_STRENGTH = {"weak", "moderate", "strong"}
_ALLOWED_PD_DIR = {"increase", "decrease"}
_ALLOWED_PD_MAG = {"low", "medium", "high"}
_ALLOWED_HALF_LIFE = {"short", "medium", "long"}

# Keep in sync with data.seed_sqlite enzymes. v0: small curated set.
_KNOWN_ENZYMES = {
    "CYP3A4",
    "CYP2C9",
    "CYP2C19",
    "CYP2D6",
    "CYP1A2",
    "CYP2B6",
    "UGT1A1",
    "UGT2B7",
}

_DRUG_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_+-]*$")


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
            out.add(eff.strip())
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
        print("DEBUG locals:", sorted(locals().keys()))
        raise ValueError(msg)
