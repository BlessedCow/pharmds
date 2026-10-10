from __future__ import annotations

import pytest

from tests.rules.support import evaluate_drug_rules, rule_ids


def test_pk_cyp3a4_strong_inhib_quetiapine_clarithro():
    _, hits = evaluate_drug_rules(["quetiapine", "clarithromycin"])
    assert any(
        h.rule_id == "PK_CYP3A4_STRONG_INHIB" and h.inputs["A"] == "quetiapine"
        for h in hits
    )


def test_pk_cyp3a4_strong_induc_midazolam_rifampin():
    _, hits = evaluate_drug_rules(["midazolam", "rifampin"])
    assert any(
        h.rule_id == "PK_CYP3A4_STRONG_INDUC" and h.inputs["A"] == "midazolam"
        for h in hits
    )


def test_pk_prodrug_activation_clopidogrel_fluconazole():
    _, hits = evaluate_drug_rules(["clopidogrel", "fluconazole"])
    assert any(
        h.rule_id == "PK_CYP2C19_INHIB_CLOPIDOGREL" and h.inputs["A"] == "clopidogrel"
        for h in hits
    )


def test_pk_pgp_digoxin_clarithro():
    _, hits = evaluate_drug_rules(["digoxin", "clarithromycin"])
    assert any(
        h.rule_id == "PK_PGP_INHIB_DIGOXIN" and h.inputs["A"] == "digoxin" for h in hits
    )


def test_pd_qt_no_duplicates_citalopram_ondansetron():
    _, hits = evaluate_drug_rules(["citalopram", "ondansetron"])
    qt_hits = [h for h in hits if h.rule_id == "PD_QT_ADDITIVE"]
    assert len(qt_hits) == 1


def test_pk_bcrp_inhib_rosuvastatin_cyclosporine():
    _, hits = evaluate_drug_rules(["rosuvastatin", "cyclosporine"])
    assert any(
        h.rule_id == "PK_BCRP_INHIB_SUBSTRATE" and h.inputs["A"] == "rosuvastatin"
        for h in hits
    )


def test_pk_oatp_inhib_rosuvastatin_cyclosporine():
    _, hits = evaluate_drug_rules(["rosuvastatin", "cyclosporine"])
    assert any(
        h.rule_id == "PK_OATP_INHIB" and h.inputs["A"] == "rosuvastatin" for h in hits
    )


def test_pk_ugt1a1_inhib_irinotecan_atazanavir():
    _, hits = evaluate_drug_rules(["irinotecan", "atazanavir"])
    assert any(
        h.rule_id == "PK_UGT1A1_INHIB" and h.inputs["A"] == "irinotecan" for h in hits
    )

def test_pd_qt_only_one_qt_rule_fires_per_pair():
    _, hits = evaluate_drug_rules(["citalopram", "ondansetron"])
    qt_hits = [
        h for h in hits
        if h.rule_id in {"PD_QT_ADDITIVE"}
    ]
    assert len(qt_hits) == 1

def test_pd_cns_depression_alcohol_clonazepam():
    _, hits = evaluate_drug_rules(["alcohol", "clonazepam"])
    rids = rule_ids(hits)
    assert (
        "PD_CNS_DEPRESSION_ADDITIVE" in rids
        or "PD_CNS_DEPRESSION_ADDITIVE_HIGH" in rids
)
    assert "PD_SEDATION_ADDITIVE" in rids

def test_pd_cns_depression_ketamine_alcohol():
    _, hits = evaluate_drug_rules(["ketamine", "alcohol"])
    rids = rule_ids(hits)
    assert "PD_SEDATION_ADDITIVE" in rids

def test_pd_stimulation_cocaine_amphetamine():
    _, hits = evaluate_drug_rules(["cocaine", "amphetamine_dextroamphetamine"])
    rids = rule_ids(hits)
    assert len(rids) > 0

def test_pd_tachycardia_methamphetamine_amphetamine():
    _, hits = evaluate_drug_rules(["methamphetamine", "amphetamine_dextroamphetamine"])
    rids = rule_ids(hits)
    assert len(rids) > 0

def test_nausea_additive_varenicline_vortioxetine():
    _, hits = evaluate_drug_rules(["varenicline", "vortioxetine"])
    rids = rule_ids(hits)

    assert "PD_NAUSEA_ADDITIVE" in rids


@pytest.mark.parametrize(
    ("drug_names", "expected_rule_id"),
    [
        pytest.param(
            ('hydroxyzine', 'paliperidone'),
            'PD_QT_ADDITIVE',
            id='pd_qt_additive_hydroxyzine_paliperidone',
        ),
        pytest.param(
            ('citalopram', 'ondansetron'),
            'PD_QT_ADDITIVE',
            id='pd_qt_additive_citalopram_ondansetron',
        ),
        pytest.param(
            ('lorazepam', 'hydroxyzine'),
            'PD_CNS_DEP_ADDITIVE',
            id='pd_cns_dep_additive_lorazepam_hydroxyzine',
        ),
        pytest.param(
            ('lorazepam', 'methocarbamol'),
            'PD_CNS_DEP_ADDITIVE',
            id='pd_cns_dep_additive_lorazepam_methocarbamol',
        ),
        pytest.param(
            ('hydroxyzine', 'olanzapine'),
            'PD_CNS_DEP_ADDITIVE',
            id='pd_cns_dep_additive_hydroxyzine_olanzapine',
        ),
        pytest.param(
            ('olanzapine', 'methocarbamol'),
            'PD_CNS_DEP_ADDITIVE',
            id='pd_cns_dep_additive_olanzapine_methocarbamol',
        ),
        pytest.param(
            ('doxepin', 'hydroxyzine'),
            'PD_H1_ANTAGONISM_ADDITIVE',
            id='pd_h1_antagonism_additive_doxepin_hydroxyzine',
        ),
        pytest.param(
            ('risperidone', 'amitriptyline'),
            'PD_ALPHA1_ANTAGONISM_ADDITIVE',
            id='pd_alpha1_antagonism_additive_risperidone_amitriptyline',
        ),
        pytest.param(
            ('trazodone', 'quetiapine'),
            'PD_ALPHA1_ANTAGONISM_ADDITIVE',
            id='pd_alpha1_antagonism_additive_trazodone_quetiapine',
        ),
        pytest.param(
            ('methadone', 'citalopram'),
            'PD_QT_PROLONGATION_ADDITIVE_HIGH',
            id='pd_qt_prolongation_additive_methadone_citalopram',
        ),
        pytest.param(
            ('methadone', 'erenumab'),
            'PD_CONSTIPATION_ADDITIVE_MEDIUM',
            id='pd_constipation_additive_methadone_erenumab',
        ),
        pytest.param(
            ('vibegron', 'digoxin'),
            'PK_VIBEGRON_DIGOXIN',
            id='pk_vibegron_digoxin',
        ),
        pytest.param(
            ('doxycycline', 'warfarin'),
            'PK_DOXYCYCLINE_WARFARIN',
            id='pk_doxycycline_warfarin',
        ),
        pytest.param(
            ('doxycycline', 'amoxicillin'),
            'PK_DOXYCYCLINE_AMOXICILLIN',
            id='pk_doxycycline_amoxicillin',
        ),
        pytest.param(
            ('doxycycline', 'calcium carbonate'),
            'PK_DOXYCYCLINE_CALCIUM_CARBONATE',
            id='pk_doxycycline_calcium_carbonate',
        ),
        pytest.param(
            ('methadone', 'fluoxetine'),
            'PK_METHADONE_FLUOXETINE',
            id='pk_methadone_fluoxetine',
        ),
        pytest.param(
            ('methadone', 'carbamazepine'),
            'PK_METHADONE_CARBAMAZEPINE',
            id='pk_methadone_carbamazepine',
        ),
        pytest.param(
            ('lisdexamfetamine', 'fluoxetine'),
            'PK_LISDEXAMFETAMINE_FLUOXETINE',
            id='pk_lisdexamfetamine_fluoxetine',
        ),
        pytest.param(
            ('fentanyl', 'midazolam'),
            'PD_RESPIRATORY_DEPRESSION_ADDITIVE',
            id='pd_respiratory_depression_fentanyl_midazolam',
        ),
        pytest.param(
            ('mdma', 'citalopram'),
            'PD_SEROTONIN_SYNDROME_ADDITIVE',
            id='pd_serotonin_syndrome_mdma_citalopram',
        ),
    ],
)
def test_expected_curated_rule(
    drug_names: tuple[str, str], expected_rule_id: str
) -> None:
    _, hits = evaluate_drug_rules(drug_names)
    assert expected_rule_id in rule_ids(hits)
