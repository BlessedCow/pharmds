import json
from pathlib import Path

path = Path("data/evidence/pd_effect_claims.json")

legacy_h1_drug_ids = {
    "amitriptyline",
    "clozapine",
    "doxepin",
    "hydroxyzine",
    "olanzapine",
    "quetiapine",
    "risperidone",
}

claims = json.loads(path.read_text(encoding="utf-8"))

kept_claims = []
removed_claims = []

for claim in claims:
    drug_id = claim.get("subject", {}).get("id")
    effect_id = claim.get("object", {}).get("effect_id")

    is_legacy_h1_claim = (
        drug_id in legacy_h1_drug_ids
        and effect_id == "H1_antagonism"
    )

    if is_legacy_h1_claim:
        removed_claims.append(claim)
    else:
        kept_claims.append(claim)

removed_drug_ids = {
    claim.get("subject", {}).get("id")
    for claim in removed_claims
}

if removed_drug_ids != legacy_h1_drug_ids:
    missing = sorted(legacy_h1_drug_ids - removed_drug_ids)
    extra = sorted(removed_drug_ids - legacy_h1_drug_ids)
    raise SystemExit(
        "Unexpected legacy H1 cleanup result. "
        f"Missing={missing}; Extra={extra}"
    )

if len(removed_claims) != 7:
    raise SystemExit(
        f"Expected to remove 7 legacy H1 claims, removed {len(removed_claims)}"
    )

path.write_text(
    json.dumps(kept_claims, indent=2) + "\n",
    encoding="utf-8",
)

print("Removed legacy H1_antagonism claims:")
for claim in sorted(
    removed_claims,
    key=lambda item: item.get("subject", {}).get("id", ""),
):
    print(f"- {claim.get('claim_id')}")