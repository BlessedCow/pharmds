from __future__ import annotations

from tests.rules.support import evaluate_drug_rules


def test_transporter_family_rule_matches_pgp_roles():
    _, hits = evaluate_drug_rules(["digoxin", "verapamil"])

    assert any(h.rule_id == "PK_PGP_INHIB_DIGOXIN" for h in hits)

