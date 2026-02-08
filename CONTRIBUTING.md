CONTRIBUTING TO PHARMDS

Thanks for contributing to PharmDS.

PharmDS is an educational, rule-based PK/PD interaction reasoner. Contributions should prioritize:
- clarity over complexity
- reducing false positives (avoid alert fatigue)
- reproducible behavior with tests


QUICK START (DEV)

```
python -m pip install -U pip
pip install -e .
ruff check .
pytest
```

If CI fails due to Python version, check pyproject.toml (requires-python).


HOW TO ADD A DRUG

PharmDS uses a small SQLite database for seed data.

1) Add the drug
Edit: `data/seed_sqlite.py`

Add a new entry in the drugs list.
Keep the drug id lowercase and stable (usually the generic name).

Example pattern:
("sertraline", "sertraline", "SSRI", "moderate", "Short educational note.")

For a structured checklist of required information, see
`docs/ADDING_A_DRUG.txt`

2) Add aliases (recommended)
Add brand names or common variants to the aliases list.
Aliases should be lowercase.

3) Add mechanism roles (as applicable)
- Enzyme roles (substrate / inhibitor / inducer)
- Transporter roles (e.g. P-gp substrate)
- PD effect profiles (QT, bleeding, serotonergic, etc.)

Keep notes conservative and educational.

4) Re-seed locally
Run the seed script used by the repo, for example:
python data/seed_sqlite.py

5) Add tests
At minimum:
- one positive test
- one negative (false-positive prevention) test


HOW TO ADD A RULE

1) Choose domain
- PK: enzyme or transporter mechanisms (directional)
- PD: additive or overlapping effects

2) Create rule JSON
Place under rules/ following existing naming conventions.

Rules must include:
- id (stable, uppercase)
- domain
- severity
- rule_class
- exactly one mechanism block (enzyme / transporter / pd_overlap)

3) Validate
Run:
```
ruff check .
pytest
```

5) Add tests
Every rule must include:
- at least one positive test
- at least one negative test

See `docs/ADDING_A_RULE.txt` for the required rule contribution template.

HOW TO ADD A TEST

Tests use pytest.

Locations:
- tests/test_golden_scenarios.py (positive anchors)
- tests/test_negative_scenarios.py (false-positive prevention)
- tests/test_scenarios.py (general scenarios)

Good tests:
- assert on rule_id
- assert directionality when relevant
- assert absence of tempting incorrect rules

Run:
```
pytest -q
ruff check .
```


CONTRIBUTION STANDARDS

- Educational only (not clinical decision support)
- Minimize false positives
- Prefer small, focused PRs

Example commit messages:
- Add escitalopram seed data and QT tests
- Add PK rule for CYP2D6 strong inhibition
- Tighten drug name resolution and add tests
