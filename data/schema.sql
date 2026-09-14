PRAGMA foreign_keys = ON;

-- Core drugs
CREATE TABLE
  IF NOT EXISTS drug (
    id TEXT PRIMARY KEY,
    generic_name TEXT NOT NULL,
    drug_class TEXT,
    therapeutic_index TEXT CHECK (
      therapeutic_index IN ('wide', 'moderate', 'narrow')
    ) NOT NULL DEFAULT 'moderate',
    notes TEXT
  );

CREATE TABLE
  IF NOT EXISTS drug_alias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id TEXT NOT NULL REFERENCES drug (id) ON DELETE CASCADE,
    alias TEXT NOT NULL
  );

CREATE TABLE
  IF NOT EXISTS drug_release_type (
    drug_id TEXT NOT NULL,
    release_type TEXT NOT NULL,
    PRIMARY KEY (drug_id, release_type),
    FOREIGN KEY (drug_id) REFERENCES drug (id) ON DELETE CASCADE
  );

CREATE INDEX IF NOT EXISTS idx_drug_release_type_drug_id ON drug_release_type (drug_id);

CREATE TABLE
  IF NOT EXISTS drug_formulation (
    drug_id TEXT NOT NULL,
    route TEXT NOT NULL,
    release_type TEXT NOT NULL,
    PRIMARY KEY (drug_id, route, release_type),
    FOREIGN KEY (drug_id) REFERENCES drug (id) ON DELETE CASCADE
  );

CREATE INDEX IF NOT EXISTS idx_drug_formulation_drug_id ON drug_formulation (drug_id);

CREATE INDEX IF NOT EXISTS idx_drug_formulation_route ON drug_formulation (route);

-- Curated available strengths/forms. These are reference options, not prescribing recommendations.
CREATE TABLE
  IF NOT EXISTS drug_dosage_option (
    drug_id TEXT NOT NULL,
    route TEXT NOT NULL,
    release_type TEXT NOT NULL,
    dosage_form TEXT NOT NULL,
    strength_value REAL NOT NULL CHECK (strength_value > 0),
    strength_unit TEXT NOT NULL,
    PRIMARY KEY (
      drug_id,
      route,
      release_type,
      dosage_form,
      strength_value,
      strength_unit
    ),
    FOREIGN KEY (drug_id) REFERENCES drug (id) ON DELETE CASCADE
  );

CREATE INDEX IF NOT EXISTS idx_drug_dosage_option_drug_id ON drug_dosage_option (drug_id);

-- Enzymes (CYP, etc.)
CREATE TABLE
  IF NOT EXISTS enzyme (
    id TEXT PRIMARY KEY,
    family TEXT NOT NULL, -- e.g. CYP, UGT
    description TEXT
  );

-- Role of a drug with an enzyme
CREATE TABLE
  IF NOT EXISTS drug_enzyme_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id TEXT NOT NULL REFERENCES drug (id) ON DELETE CASCADE,
    enzyme_id TEXT NOT NULL REFERENCES enzyme (id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('substrate', 'inhibitor', 'inducer')),
    strength TEXT CHECK (strength IN ('weak', 'moderate', 'strong')) NULL,
    fraction_metabolized REAL NULL CHECK (
      fraction_metabolized >= 0.0
      AND fraction_metabolized <= 1.0
    ),
    notes TEXT,
    UNIQUE (drug_id, enzyme_id, role)
  );

-- Transporters
CREATE TABLE
  IF NOT EXISTS transporter (id TEXT PRIMARY KEY, description TEXT);

CREATE TABLE
  IF NOT EXISTS drug_transporter_role (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id TEXT NOT NULL REFERENCES drug (id) ON DELETE CASCADE,
    transporter_id TEXT NOT NULL REFERENCES transporter (id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('substrate', 'inhibitor', 'inducer')),
    strength TEXT CHECK (strength IN ('weak', 'moderate', 'strong')) NULL,
    notes TEXT,
    UNIQUE (drug_id, transporter_id, role)
  );

-- PD effects (domains for additive/synergistic rules)
CREATE TABLE
  IF NOT EXISTS pd_effect (id TEXT PRIMARY KEY, description TEXT NOT NULL);

CREATE TABLE
  IF NOT EXISTS drug_pd_effect (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_id TEXT NOT NULL REFERENCES drug (id) ON DELETE CASCADE,
    pd_effect_id TEXT NOT NULL REFERENCES pd_effect (id) ON DELETE CASCADE,
    direction TEXT NOT NULL CHECK (direction IN ('increase', 'decrease')),
    magnitude TEXT NOT NULL CHECK (magnitude IN ('low', 'medium', 'high')),
    mechanism_note TEXT,
    UNIQUE (drug_id, pd_effect_id)
  );

-- Optional coarse parameters (educational, not dosing)
CREATE TABLE
  IF NOT EXISTS parameter_set (
    drug_id TEXT PRIMARY KEY REFERENCES drug (id) ON DELETE CASCADE,
    prodrug INTEGER NOT NULL DEFAULT 0 CHECK (prodrug IN (0, 1)),
    active_metabolite INTEGER NOT NULL DEFAULT 0 CHECK (active_metabolite IN (0, 1)),
    renal_clearance_flag INTEGER NOT NULL DEFAULT 0 CHECK (renal_clearance_flag IN (0, 1)),
    half_life_bucket TEXT CHECK (half_life_bucket IN ('short', 'medium', 'long')) NULL,
    notes TEXT
  );