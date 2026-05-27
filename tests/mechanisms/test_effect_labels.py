from core.mechanisms.effect_labels import effect_display_label


def test_effect_display_label_uses_public_labels_for_known_effects():
    assert effect_display_label("QT_prolongation") == "QT prolongation"
    assert (
        effect_display_label("h1_antagonism")
        == "antihistamine/sedation-related effect"
    )
    assert effect_display_label("hypertension_risk") == "blood-pressure elevation risk"
    assert effect_display_label("tachycardia_risk") == "increased heart-rate risk"


def test_effect_display_label_falls_back_to_readable_unknown_effect_id():
    assert effect_display_label("unknown_effect_id") == "unknown effect id"


def test_effect_display_label_handles_missing_effect_id():
    assert effect_display_label(None) == "unspecified effect"
