"""Interaction regressions for the sourced catalog expansion.

Seed a separate database from the baseline plus the import manifest. This keeps
the tests valid both before and after the user applies the optional overlay.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.cli import RULE_DIR, connect, load_facts, resolve_drug_ids
from app.service import analyze_names
from data.loaders import load_drugs_curation
from data.seed_sqlite import apply_schema, seed
from rules.engine import evaluate_all, load_rules
from tools.apply_catalog_expansion import MANIFEST, merge_drugs


@pytest.fixture(scope="module")
def expansion_db(tmp_path_factory: pytest.TempPathFactory) -> Path:
    from pytest import MonkeyPatch

    payload, _, _ = merge_drugs(
        load_drugs_curation(), json.loads(MANIFEST.read_text(encoding="utf-8"))
    )
    path = tmp_path_factory.mktemp("catalog_interactions") / "expanded.sqlite3"
    with MonkeyPatch.context() as patch:
        patch.setattr("data.loaders.load_drugs_curation", lambda path=None: payload)
        patch.setattr(
            "data.curation.validate.assert_valid_drugs_curation", lambda: None
        )
        with connect(path) as conn:
            apply_schema(conn)
            seed(conn)
    return path


@pytest.fixture(scope="module")
def rule_set():
    return load_rules(RULE_DIR)


def pair_hits(expansion_db: Path, rule_set: list, first: str, second: str) -> list:
    with connect(expansion_db) as conn:
        ids = resolve_drug_ids(conn, [first, second])
        facts = load_facts(conn, ids, patient_flags={})
    return evaluate_all(rule_set, facts, ids)


@pytest.mark.parametrize(
    ("first", "second", "rule_id"),
    [
        ("fluvoxamine", "tizanidine", "PK_TIZANIDINE_FLUVOXAMINE"),
        ("fluvoxamine", "theophylline", "PK_CYP1A2_INHIB_SUBSTRATE"),
        ("ciprofloxacin", "tizanidine", "PK_TIZANIDINE_CIPROFLOXACIN"),
        ("fluvoxamine", "clozapine", "PK_CYP1A2_INHIB_SUBSTRATE"),
        ("ciprofloxacin", "olanzapine", "PK_CYP1A2_INHIB_SUBSTRATE"),
        ("fluvoxamine", "diazepam", "PK_DIAZEPAM_FLUVOXAMINE"),
        ("ciprofloxacin", "theophylline", "PK_CYP1A2_INHIB_SUBSTRATE"),
        ("omeprazole", "clopidogrel", "PK_CYP2C19_INHIB_CLOPIDOGREL"),
        ("itraconazole", "simvastatin", "PK_CYP3A4_STRONG_INHIB"),
        ("ketoconazole", "simvastatin", "PK_CYP3A4_STRONG_INHIB"),
        ("itraconazole", "apixaban", "PK_CYP3A4_STRONG_INHIB"),
        ("ketoconazole", "rivaroxaban", "PK_RIVAROXABAN_KETOCONAZOLE"),
        ("ritonavir", "atorvastatin", "PK_CYP3A4_STRONG_INHIB"),
        ("cobicistat", "simvastatin", "PK_CYP3A4_STRONG_INHIB"),
        ("phenytoin", "apixaban", "PK_APIXABAN_PHENYTOIN"),
        ("bupropion", "dextromethorphan", "PK_CYP2D6_INHIB_SUBSTRATE"),
        ("bupropion", "metoprolol", "PK_CYP2D6_INHIB_SUBSTRATE"),
        ("fluvoxamine", "linezolid", "PD_SEROTONIN_SYNDROME_ADDITIVE"),
        ("dextromethorphan", "linezolid", "PD_SEROTONIN_SYNDROME_ADDITIVE"),
        ("phenobarbital", "morphine", "PD_CNS_DEP_ADDITIVE"),
        ("phenobarbital", "codeine", "PD_CNS_DEP_ADDITIVE"),
        ("bupropion", "codeine", "PK_CYP2D6_INHIB_CODEINE_ACTIVATION"),
        ("paroxetine", "codeine", "PK_CYP2D6_INHIB_CODEINE_ACTIVATION"),
        ("apixaban", "aspirin", "PD_BLEEDING_ADDITIVE"),
        ("rivaroxaban", "aspirin", "PD_BLEEDING_ADDITIVE"),
        ("fluvoxamine", "apixaban", "PD_BLEEDING_ADDITIVE"),
        ("metoprolol", "sotalol", "PD_BRADYCARDIA_ADDITIVE"),
        ("theophylline", "tobacco_smoke", "PK_THEOPHYLLINE_TOBACCO_SMOKE"),
        ("clozapine", "tobacco_smoke", "PK_CLOZAPINE_TOBACCO_SMOKE"),
        ("simvastatin", "grapefruit_juice", "PK_SIMVASTATIN_GRAPEFRUIT_JUICE"),
        ("apixaban", "st_johns_wort", "PK_APIXABAN_ST_JOHNS_WORT"),
        ("rivaroxaban", "st_johns_wort", "PK_RIVAROXABAN_ST_JOHNS_WORT"),
        ("apixaban", "phenytoin", "PK_APIXABAN_PHENYTOIN"),
        ("rivaroxaban", "phenytoin", "PK_RIVAROXABAN_PHENYTOIN"),
        ("rivaroxaban", "ketoconazole", "PK_RIVAROXABAN_KETOCONAZOLE"),
        ("rivaroxaban", "ritonavir", "PK_RIVAROXABAN_RITONAVIR"),
    ],
)
def test_expansion_produces_expected_pair_finding(
    expansion_db: Path, rule_set: list, first: str, second: str, rule_id: str
) -> None:
    hits = pair_hits(expansion_db, rule_set, first, second)
    assert rule_id in {hit.rule_id for hit in hits}, (first, second, hits)


def test_pantoprazole_does_not_inherit_omeprazole_clopidogrel_rule(
    expansion_db: Path, rule_set: list
) -> None:
    hits = pair_hits(expansion_db, rule_set, "pantoprazole", "clopidogrel")
    assert "PK_CYP2C19_INHIB_CLOPIDOGREL" not in {
        hit.rule_id for hit in hits
    }


def test_morphine_does_not_inherit_codeine_cyp2d6_activation(
    expansion_db: Path, rule_set: list
) -> None:
    assert not any(
        hit.inputs.get("enzyme_id") == "CYP2D6"
        for hit in pair_hits(expansion_db, rule_set, "morphine", "bupropion")
    )


def test_codeine_uses_activation_interpretation_instead_of_generic_substrate_warning(
    expansion_db: Path, rule_set: list
) -> None:
    hits = pair_hits(expansion_db, rule_set, "codeine", "bupropion")
    ids = {hit.rule_id for hit in hits}
    assert "PK_CYP2D6_INHIB_CODEINE_ACTIVATION" in ids
    assert "PK_CYP2D6_INHIB_SUBSTRATE" not in ids


@pytest.mark.parametrize("inhibitor", ["ciprofloxacin", "fluvoxamine"])
def test_labeled_tizanidine_contraindication_overrides_generic_message(
    expansion_db: Path, rule_set: list, inhibitor: str
) -> None:
    hits = pair_hits(expansion_db, rule_set, "tizanidine", inhibitor)
    assert "PK_CYP1A2_INHIB_TIZANIDINE" not in {hit.rule_id for hit in hits}
    specific_id = f"PK_TIZANIDINE_{inhibitor.upper()}"
    specific = next(hit for hit in hits if hit.rule_id == specific_id)
    assert specific.severity.value == "contraindicated"


def test_weak_cyp2d6_inhibition_does_not_trigger_codeine_activation_rule(
    expansion_db: Path, rule_set: list
) -> None:
    hits = pair_hits(expansion_db, rule_set, "codeine", "fluvoxamine")
    assert "PK_CYP2D6_INHIB_CODEINE_ACTIVATION" not in {
        hit.rule_id for hit in hits
    }


def test_cobicistat_is_not_reported_as_enzyme_inducer(
    expansion_db: Path, rule_set: list
) -> None:
    hits = pair_hits(expansion_db, rule_set, "cobicistat", "apixaban")
    assert "PK_CYP3A4_STRONG_INDUC" not in {
        hit.rule_id for hit in hits
    }


def test_acetaminophen_does_not_generate_an_unmodeled_enzyme_interaction(
    expansion_db: Path, rule_set: list
) -> None:
    assert not any(
        "enzyme_id" in hit.inputs
        for hit in pair_hits(expansion_db, rule_set, "acetaminophen", "phenobarbital")
    )


@pytest.mark.parametrize("substrate", ["theophylline", "clozapine"])
def test_nicotine_does_not_inherit_tobacco_smoke_induction(
    expansion_db: Path, rule_set: list, substrate: str
) -> None:
    hits = pair_hits(expansion_db, rule_set, substrate, "nicotine")
    assert not any("TOBACCO_SMOKE" in hit.rule_id for hit in hits)
    assert not any(
        hit.inputs.get("enzyme_id") == "CYP1A2"
        and "exposure_decrease" in hit.tags
        for hit in hits
    )


@pytest.mark.parametrize(
    ("first", "second", "specific_id"),
    [
        ("apixaban", "st_johns_wort", "PK_APIXABAN_ST_JOHNS_WORT"),
        ("rivaroxaban", "st_johns_wort", "PK_RIVAROXABAN_ST_JOHNS_WORT"),
        ("apixaban", "phenytoin", "PK_APIXABAN_PHENYTOIN"),
        ("rivaroxaban", "phenytoin", "PK_RIVAROXABAN_PHENYTOIN"),
        ("rivaroxaban", "ketoconazole", "PK_RIVAROXABAN_KETOCONAZOLE"),
        ("rivaroxaban", "ritonavir", "PK_RIVAROXABAN_RITONAVIR"),
    ],
)
def test_label_avoid_policy_supersedes_generic_monitoring_advice(
    expansion_db: Path, rule_set: list, first: str, second: str, specific_id: str
) -> None:
    hits = pair_hits(expansion_db, rule_set, first, second)
    specific = next(hit for hit in hits if hit.rule_id == specific_id)
    assert specific.rule_class.value == "avoid"
    assert not {
        "PK_CYP3A4_STRONG_INDUC",
        "PK_CYP3A4_STRONG_INHIB",
    } & {hit.rule_id for hit in hits}
    assert any("Avoid" in action for action in specific.actions)
    assert any(
        ref.get("url", "").startswith("https://dailymed.nlm.nih.gov/")
        for ref in specific.references
    )


def test_named_avoid_policy_does_not_hide_unrelated_induction(
    expansion_db: Path, rule_set: list
) -> None:
    hits = pair_hits(expansion_db, rule_set, "simvastatin", "phenytoin")
    assert "PK_CYP3A4_STRONG_INDUC" in {hit.rule_id for hit in hits}


def test_rivaroxaban_avoid_rule_does_not_apply_apixaban_dose_policy(
    expansion_db: Path, rule_set: list
) -> None:
    hits = pair_hits(expansion_db, rule_set, "apixaban", "ketoconazole")
    assert "PK_CYP3A4_STRONG_INHIB" in {hit.rule_id for hit in hits}
    assert "PK_RIVAROXABAN_KETOCONAZOLE" not in {hit.rule_id for hit in hits}


def test_grapefruit_rule_does_not_assume_quantity_or_apply_to_other_statins(
    expansion_db: Path, rule_set: list
) -> None:
    rule_id = "PK_SIMVASTATIN_GRAPEFRUIT_JUICE"
    hits = pair_hits(expansion_db, rule_set, "simvastatin", "grapefruit_juice")
    hit = next(hit for hit in hits if hit.rule_id == rule_id)
    rule = next(rule for rule in rule_set if rule.id == rule_id)
    assert "amount" in rule.explanation_template.lower()
    assert "more than one quart" in " ".join(hit.actions)
    assert rule_id not in {
        result.rule_id
        for result in pair_hits(
            expansion_db, rule_set, "atorvastatin", "grapefruit_juice"
        )
    }


@pytest.mark.parametrize(
    ("names", "domain", "expected"),
    [
        (("omeprazole", "clopidogrel"), "pk", "PK_CYP2C19_INHIB_CLOPIDOGREL"),
        (("linezolid", "fluvoxamine"), "pd", "PD_SEROTONIN_SYNDROME_ADDITIVE"),
        (("codeine", "bupropion"), "pk", "PK_CYP2D6_INHIB_CODEINE_ACTIVATION"),
        (("tizanidine", "ciprofloxacin"), "pk", "PK_TIZANIDINE_CIPROFLOXACIN"),
        (("theophylline", "tobacco_smoke"), "pk", "PK_THEOPHYLLINE_TOBACCO_SMOKE"),
        (("apixaban", "st_johns_wort"), "pk", "PK_APIXABAN_ST_JOHNS_WORT"),
    ],
)
def test_pair_finding_reaches_public_analysis(
    monkeypatch: pytest.MonkeyPatch,
    expansion_db: Path,
    names: tuple[str, str],
    domain: str,
    expected: str,
) -> None:
    monkeypatch.setattr("app.service.DB_PATH", expansion_db)
    result = analyze_names(list(names), domain=domain, as_json_payload=True)
    assert result.ok, result.payload
    assert expected in {
        hit["rule_id"]
        for pair in result.payload["pairs"]
        for hit in pair[domain]["hits"]
    }
