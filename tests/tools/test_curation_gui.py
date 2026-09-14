from __future__ import annotations

import json
from pathlib import Path

from tools.curation_gui import (
    build_identity_index,
    canonical_pd_effect_ids,
    duplicate_pd_effect_ids,
    find_identity_conflicts,
    split_aliases,
)


def test_split_aliases_trims_and_deduplicates_case_insensitively() -> None:
    assert split_aliases(
        "Wellbutrin, Zyban, wellbutrin,  "
    ) == ["Wellbutrin", "Zyban"]


def test_identity_index_contains_id_generic_name_and_aliases() -> None:
    drugs = [
        {
            "id": "bupropion",
            "generic_name": "bupropion",
            "aliases": ["Wellbutrin", "Zyban"],
        }
    ]

    index = build_identity_index(drugs)

    assert "bupropion" in index
    assert "wellbutrin" in index
    assert "zyban" in index


def test_identity_conflicts_detect_alias_against_existing_generic_name() -> None:
    drugs = [
        {
            "id": "bupropion",
            "generic_name": "bupropion",
            "aliases": ["Wellbutrin"],
        }
    ]

    conflicts = find_identity_conflicts(
        drugs=drugs,
        drug_id="example_drug",
        generic_name="example drug",
        aliases=["Bupropion"],
    )

    assert conflicts
    assert "bupropion" in conflicts[0].lower()


def test_identity_conflicts_ignore_current_drug_during_edit() -> None:
    drugs = [
        {
            "id": "bupropion",
            "generic_name": "bupropion",
            "aliases": ["Wellbutrin"],
        }
    ]

    conflicts = find_identity_conflicts(
        drugs=drugs,
        drug_id="bupropion",
        generic_name="bupropion",
        aliases=["Wellbutrin"],
        exclude_drug_id="bupropion",
    )

    assert conflicts == []


def test_identity_conflicts_allow_id_matching_generic_name() -> None:
    conflicts = find_identity_conflicts(
        drugs=[],
        drug_id="bupropion",
        generic_name="bupropion",
        aliases=[],
    )

    assert conflicts == []


def test_identity_conflicts_reject_alias_matching_primary_identity() -> None:
    conflicts = find_identity_conflicts(
        drugs=[],
        drug_id="bupropion",
        generic_name="bupropion",
        aliases=["Bupropion"],
    )

    assert len(conflicts) == 1
    assert "alias" in conflicts[0].lower()


def test_duplicate_pd_effect_ids_detect_normalized_duplicates() -> None:
    duplicates = duplicate_pd_effect_ids(
        [
            {"effect_id": "QT_prolongation"},
            {"effect_id": "qt prolongation"},
            {"effect_id": "sedation"},
        ]
    )

    assert duplicates == {"QT_prolongation"}


def test_canonical_pd_effect_ids_include_current_core_effects(
    tmp_path: Path,
) -> None:
    rule_dir = tmp_path / "rules"
    rule_dir.mkdir()

    (rule_dir / "pd_example.json").write_text(
        json.dumps(
            {
                "domain": "PD",
                "logic": {
                    "pd_overlap": {
                        "effect_id": "sedation",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    effects = canonical_pd_effect_ids(rule_dir=rule_dir)

    assert "sedation" in effects
    assert "QT_prolongation" in effects
    assert len(effects) == len(set(effects))
