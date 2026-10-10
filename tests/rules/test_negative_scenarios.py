"""Negative / non-trigger tests.

These tests exist to reduce false positives ("alert fatigue"). They assert that
rules do NOT fire when mechanisms/overlaps are absent or when the "wrong" rule
could be tempting.
"""

from __future__ import annotations

import pytest

from tests.rules.support import evaluate_drug_rules, rule_ids


def _run(drugs: list[str]):
    return evaluate_drug_rules(drugs)


_rule_ids = rule_ids


def test_negative_no_qt_hit_citalopram_sertraline():
    """Only citalopram has QT liability; the pair may be serotonergic."""
    _, hits = _run(["citalopram", "sertraline"])
    assert "PD_QT_ADDITIVE" not in _rule_ids(hits)


def test_negative_no_bradycardia_hit_propranolol_tizanidine():
    """Only propranolol has bradycardia liability in seed data."""
    _, hits = _run(["propranolol", "tizanidine"])
    assert "PD_BRADYCARDIA_ADDITIVE" not in _rule_ids(hits)
    assert hits == []


def test_negative_desvenlafaxine_not_serotonergic_overlap():
    """Desvenlafaxine uses the serotonin_syndrome effect, not overlap."""
    _, hits = _run(["desvenlafaxine", "sertraline"])
    rids = _rule_ids(hits)
    assert "PD_SEROTONIN_SYNDROME_ADDITIVE" in rids
    assert "PD_SEROTONERGIC_ADDITIVE" not in rids


def test_negative_pgp_induction_not_inhibition_digoxin_rifampin():
    """Rifampin should induce (not inhibit) P-gp for digoxin in seed data."""
    _, hits = _run(["digoxin", "rifampin"])
    rids = _rule_ids(hits)
    assert "PK_PGP_INDUC_DIGOXIN" in rids
    assert "PK_PGP_INHIB_DIGOXIN" not in rids


def test_negative_cyp3a4_induction_not_inhibition_midazolam_rifampin():
    """Rifampin should induce (not inhibit) CYP3A4 for midazolam in seed data."""
    _, hits = _run(["midazolam", "rifampin"])
    rids = _rule_ids(hits)
    assert "PK_CYP3A4_STRONG_INDUC" in rids
    assert "PK_CYP3A4_STRONG_INHIB" not in rids


def test_negative_no_bcrp_hit_rosuvastatin_fluconazole():
    """Fluconazole should not be treated as a BCRP inhibitor in seed data."""
    _, hits = _run(["rosuvastatin", "fluconazole"])
    assert "PK_BCRP_INHIB_SUBSTRATE" not in _rule_ids(hits)


def test_negative_no_oatp_hit_rosuvastatin_fluconazole():
    """Fluconazole is not modeled as an OATP inhibitor in seed data."""
    _, hits = _run(["rosuvastatin", "fluconazole"])
    assert "PK_OATP_INHIB" not in _rule_ids(hits)

def test_pd_cns_dep_additive_does_not_fire_for_low_magnitude():
    _, hits = _run(["paliperidone", "hydroxyzine"])
    assert all(h.rule_id != "PD_CNS_DEP_ADDITIVE" for h in hits)

def test_pd_alpha1_antagonism_not_triggered_sertraline_gabapentin():
    _, hits = _run(["sertraline", "gabapentin"])
    assert all(h.rule_id != "PD_ALPHA1_ANTAGONISM_ADDITIVE" for h in hits)

def test_pd_alpha1_antagonism_not_triggered_warfarin_clarithromycin():
    _, hits = _run(["warfarin", "clarithromycin"])
    assert all(h.rule_id != "PD_ALPHA1_ANTAGONISM_ADDITIVE" for h in hits)

def test_negative_no_activation_agitation_hit_clonazepam_zolpidem():
    _, hits = _run(["clonazepam", "zolpidem"])
    assert "PD_ACTIVATION_AGITATION_ADDITIVE" not in _rule_ids(hits)


def test_negative_no_activation_agitation_hit_clonidine_guanfacine():
    _, hits = _run(["clonidine", "guanfacine"])
    assert "PD_ACTIVATION_AGITATION_ADDITIVE" not in _rule_ids(hits)


def test_negative_no_insomnia_hit_clonazepam_zolpidem():
    _, hits = _run(["clonazepam", "zolpidem"])
    assert "PD_INSOMNIA_ADDITIVE" not in _rule_ids(hits)


def test_negative_no_insomnia_hit_clonidine_guanfacine():
    _, hits = _run(["clonidine", "guanfacine"])
    assert "PD_INSOMNIA_ADDITIVE" not in _rule_ids(hits)

def test_negative_no_serotonin_syndrome_lsd_sertraline():
    _, hits = _run(["lsd", "sertraline"])
    assert "PD_SEROTONIN_SYNDROME_ADDITIVE" not in _rule_ids(hits)

def test_negative_no_respiratory_depression_cannabis_sertraline():
    _, hits = _run(["cannabis", "sertraline"])
    assert "PD_RESPIRATORY_DEPRESSION_ADDITIVE" not in _rule_ids(hits)

def test_negative_no_qt_hit_nicotine_citalopram():
    _, hits = _run(["nicotine", "citalopram"])
    assert "PD_QT_ADDITIVE" not in _rule_ids(hits)

def test_negative_no_serotonergic_cocaine_citalopram():
    _, hits = _run(["cocaine", "citalopram"])
    assert "PD_SEROTONERGIC_ADDITIVE" not in _rule_ids(hits)

def test_negative_no_respiratory_depression_nicotine_methylphenidate():
    _, hits = _run(["nicotine", "methylphenidate"])
    assert "PD_RESPIRATORY_DEPRESSION_ADDITIVE" not in _rule_ids(hits)



@pytest.mark.parametrize(
    "drug_names",
    [
        # Fluconazole is not a CYP3A4 strong inhibitor in seed data; no PD
        # overlap either.
        pytest.param(
            ('midazolam', 'fluconazole'),
            id='negative_no_interaction_midazolam_fluconazole',
        ),
        # Clarithromycin should not be treated as a CYP2C19 inhibitor for
        # clopidogrel activation.
        pytest.param(
            ('clopidogrel', 'clarithromycin'),
            id='negative_no_interaction_clopidogrel_clarithromycin',
        ),
        # Clarithromycin should not trip the CYP2C9 inhibition warfarin rule
        # in current seed data.
        pytest.param(
            ('warfarin', 'clarithromycin'),
            id='negative_no_interaction_warfarin_clarithromycin',
        ),
        # Digoxin is a P-gp substrate, but fluconazole is not a P-gp
        # inhibitor/inducer in seed data.
        pytest.param(
            ('digoxin', 'fluconazole'),
            id='negative_no_interaction_digoxin_fluconazole',
        ),
        # Quetiapine is CYP3A4 substrate, but fluconazole is not a strong
        # CYP3A4 inhibitor in seed.
        pytest.param(
            ('quetiapine', 'fluconazole'),
            id='negative_no_cyp3a4_strong_inhib_quetiapine_fluconazole',
        ),
    ],
)
def test_pairs_without_curated_findings(drug_names: tuple[str, str]) -> None:
    _, hits = evaluate_drug_rules(drug_names)
    assert hits == []
