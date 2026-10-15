-- =============================================================================
-- Talentra Database Design Ã¢â‚¬â€� Master Data module
-- Phase 1 (Common, Team), Milestones 1-6
-- Engine chosen: PostgreSQL (decision + reason in 99_documentation.sql)
--
-- This file models ONLY the docket Master data domain (Section 4, Tier 1):
--   cities, states, countries, skills, qualifications, industries,
--   job roles, employment types, work types, languages,
--   reference codes for every enumeration, UI translation keys.
--
-- Naming follows Rule Group 1 exactly:
--   snake_case table/column names, singular nouns, PK named id,
--   FK named <referenced_table>_id, idx_/uq_ prefixes, no reserved words.
--   Reserved word list checked against PostgreSQL 16 keywords.
--
-- PK type: BIGINT GENERATED ALWAYS AS IDENTITY (64-bit surrogate, Rule Group 2).
-- Standard domains per Rule Group 3 are applied and cited inline.
-- Every business table carries created_at, created_by, updated_at, updated_by (Rule Group 4).
-- Soft-delete is used where stated; deleted_at column present on master data that supports it.
-- Sensitive columns tagged per Rule Group 6 in COMMENT (classification only; handling in security note).
-- Enumerations live in reference_code with code, display_name_key, active flag, sort_order (Rule Group 3 enum rule).
-- UI strings stored by key in ui_translation, one row per key and language, with default-language fallback (Rule Group 7).
--
-- NO out-of-docket entities are added in this file.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- COUNTRIES
-- Master data: countries.
-- Rule Group 3 usage: country uses TEXT for names; ISO codes stored as
--   CHAR(2) / CHAR(3) / CHAR(3) (text with fixed format).
-- Soft-delete: via is_active flag only. No deleted_at because countries are
--   reference data that is deactivated rather than removed.
-- -----------------------------------------------------------------------------
CREATE TABLE country (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    iso_alpha2   CHAR(2)    NOT NULL,
    iso_alpha3   CHAR(3)    NOT NULL,
    name          TEXT       NOT NULL,
    iso_numeric   CHAR(3)    NOT NULL,
    is_active     BOOLEAN    NOT NULL DEFAULT TRUE,
    sort_order    SMALLINT   NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by    BIGINT     NOT NULL DEFAULT 0,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by    BIGINT     NOT NULL DEFAULT 0,
    CONSTRAINT uq_country_iso_alpha2 UNIQUE (iso_alpha2),
    CONSTRAINT uq_country_iso_alpha3 UNIQUE (iso_alpha3)
);

CREATE INDEX idx_country_is_active ON country (is_active);

COMMENT ON TABLE country IS 'Master data: countries (Section 4 Tier 1). Public.';

-- -----------------------------------------------------------------------------
-- STATES
-- Master data: states/provinces.
-- Relationship: country 1..* state.
-- Rule Group 3 usage: state name is TEXT.
-- -----------------------------------------------------------------------------
CREATE TABLE state (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_id   BIGINT     NOT NULL,
    name         TEXT       NOT NULL,
    is_active    BOOLEAN    NOT NULL DEFAULT TRUE,
    sort_order   SMALLINT   NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by   BIGINT     NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   BIGINT     NOT NULL DEFAULT 0,
    CONSTRAINT fk_state_country FOREIGN KEY (country_id)
        REFERENCES country(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_state_country_name UNIQUE (country_id, name)
);

CREATE INDEX idx_state_country ON state (country_id);
CREATE INDEX idx_state_is_active ON state (is_active);

COMMENT ON TABLE state IS 'Master data: states/provinces (Section 4 Tier 1). Public.';

-- -----------------------------------------------------------------------------
-- CITIES
-- Master data: cities.
-- Relationship: country 1..* city; state 1..* city (state_id nullable where
--   a city is not in a state, e.g. a territory or district that is not a state).
-- Rule Group 3 usage: city name is TEXT. Coordinates use latitude/longitude
--   NUMERIC(9,6) with coordinates_source text (Rule Group 3 coordinates domain).
--   Nullable only when coordinate is genuinely unknown.
-- -----------------------------------------------------------------------------
CREATE TABLE city (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    country_id        BIGINT    NOT NULL,
    state_id          BIGINT    NULL,
    name              TEXT      NOT NULL,
    latitude          NUMERIC(9,6) NULL,
    longitude         NUMERIC(9,6) NULL,
    coordinates_source TEXT     NULL,
    timezone          TEXT      NULL,
    is_active         BOOLEAN   NOT NULL DEFAULT TRUE,
    sort_order        SMALLINT  NOT NULL DEFAULT 0,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by        BIGINT    NOT NULL DEFAULT 0,
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by        BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT fk_city_country FOREIGN KEY (country_id)
        REFERENCES country(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_city_state FOREIGN KEY (state_id)
        REFERENCES state(id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT uq_city_country_name UNIQUE (country_id, name),
    CONSTRAINT chk_city_coordinates_consistent CHECK (
        (latitude IS NULL AND longitude IS NULL)
        OR (latitude IS NOT NULL AND longitude IS NOT NULL)
    )
);

CREATE INDEX idx_city_country ON city (country_id);
CREATE INDEX idx_city_state ON city (state_id);
CREATE INDEX idx_city_is_active ON city (is_active);

COMMENT ON TABLE city IS 'Master data: cities (Section 4 Tier 1). Public. state_id nullable where a city does not belong to a state.';

-- -----------------------------------------------------------------------------
-- SKILLS
-- Master data: skills.
-- Rule Group 3 usage: skill name is TEXT (unbounded not required; bounded TEXT).
-- Soft-delete: via is_active.
-- -----------------------------------------------------------------------------
CREATE TABLE skill (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT      NOT NULL,
    category   TEXT      NOT NULL,
    is_active  BOOLEAN   NOT NULL DEFAULT TRUE,
    sort_order SMALLINT  NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by BIGINT    NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT uq_skill_name_active UNIQUE (name, is_active)
);

CREATE INDEX idx_skill_category ON skill (category);
CREATE INDEX idx_skill_is_active ON skill (is_active);

COMMENT ON TABLE skill IS 'Master data: skills (Section 4 Tier 1). Public.';

-- -----------------------------------------------------------------------------
-- QUALIFICATIONS
-- Master data: qualifications.
-- Relationship: qualification 1..1 reference_code (education_level) via
--   education_level_code stored in qualification. The lookup uses
--   reference_code(domain = 'education_level', code).
-- Rule Group 3 usage: qualification name is TEXT.
-- -----------------------------------------------------------------------------
CREATE TABLE qualification (
    id                     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code                   TEXT     NOT NULL,
    name                   TEXT     NOT NULL,
    education_level_code   TEXT     NOT NULL,
    is_active              BOOLEAN  NOT NULL DEFAULT TRUE,
    sort_order             SMALLINT NOT NULL DEFAULT 0,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by             BIGINT   NOT NULL DEFAULT 0,
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by             BIGINT   NOT NULL DEFAULT 0,
    CONSTRAINT uq_qualification_code UNIQUE (code),
    CONSTRAINT uq_qualification_name_active UNIQUE (name, is_active),
    CONSTRAINT fk_qualification_education_level FOREIGN KEY (education_level_code, 'education_level')
        REFERENCES reference_code(domain, code) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE INDEX idx_qualification_education_level ON qualification (education_level_code);
CREATE INDEX idx_qualification_is_active ON qualification (is_active);

COMMENT ON TABLE qualification IS 'Master data: qualifications (Section 4 Tier 1). Public. education_level_code references reference_code(domain=education_level).';

-- -----------------------------------------------------------------------------
-- INDUSTRIES
-- Master data: industries.
-- Rule Group 3 usage: industry name is TEXT.
-- -----------------------------------------------------------------------------
CREATE TABLE industry (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT      NOT NULL,
    is_active  BOOLEAN   NOT NULL DEFAULT TRUE,
    sort_order SMALLINT  NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by BIGINT    NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT uq_industry_name_active UNIQUE (name, is_active)
);

CREATE INDEX idx_industry_is_active ON industry (is_active);

COMMENT ON TABLE industry IS 'Master data: industries (Section 4 Tier 1). Public.';

-- -----------------------------------------------------------------------------
-- JOB ROLES
-- Master data: job roles.
-- Rule Group 3 usage: job_role name is TEXT.
-- -----------------------------------------------------------------------------
CREATE TABLE job_role (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT      NOT NULL,
    is_active  BOOLEAN   NOT NULL DEFAULT TRUE,
    sort_order SMALLINT  NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by BIGINT    NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT    NOT NULL DEFAULT 0,
    CONSTRAINT uq_job_role_name_active UNIQUE (name, is_active)
);

CREATE INDEX idx_job_role_is_active ON job_role (is_active);

COMMENT ON TABLE job_role IS 'Master data: job roles (Section 4 Tier 1). Public.';

-- -----------------------------------------------------------------------------
-- EMPLOYMENT TYPES
-- Master data: employment types (enumeration lookup).
-- Rule Group 3 enum rule: fixed set of values held in a lookup table with
--   code, display_name_key, active flag, sort_order.
-- Relationship: employment_type referenced as employment_type_id elsewhere.
-- -----------------------------------------------------------------------------
CREATE TABLE employment_type (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code               TEXT     NOT NULL,
    display_name_key   TEXT     NOT NULL,
    is_active          BOOLEAN  NOT NULL DEFAULT TRUE,
    sort_order         SMALLINT NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT   NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT   NOT NULL DEFAULT 0,
    CONSTRAINT uq_employment_type_code UNIQUE (code)
);

CREATE INDEX idx_employment_type_is_active ON employment_type (is_active);

COMMENT ON TABLE employment_type IS 'Master data: employment types (Section 4 Tier 1, enumeration lookup, Rule Group 3 enum rule). Public.';

-- -----------------------------------------------------------------------------
-- WORK TYPES
-- Master data: work types (enumeration lookup).
-- Rule Group 3 enum rule.
-- -----------------------------------------------------------------------------
CREATE TABLE work_type (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code               TEXT     NOT NULL,
    display_name_key   TEXT     NOT NULL,
    is_active          BOOLEAN  NOT NULL DEFAULT TRUE,
    sort_order         SMALLINT NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT   NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT   NOT NULL DEFAULT 0,
    CONSTRAINT uq_work_type_code UNIQUE (code)
);

CREATE INDEX idx_work_type_is_active ON work_type (is_active);

COMMENT ON TABLE work_type IS 'Master data: work types (Section 4 Tier 1, enumeration lookup, Rule Group 3 enum rule). Public.';

-- -----------------------------------------------------------------------------
-- LANGUAGES
-- Master data: languages.
-- Rule Group 3 usage: language name is TEXT. ISO codes stored as CHAR(2)/CHAR(3).
-- -----------------------------------------------------------------------------
CREATE TABLE language_lookup (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    iso_639_1  CHAR(2)   NOT NULL,
    iso_639_3  CHAR(3)   NOT NULL,
    name       TEXT       NOT NULL,
    is_active  BOOLEAN    NOT NULL DEFAULT TRUE,
    sort_order SMALLINT   NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by BIGINT     NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by BIGINT     NOT NULL DEFAULT 0,
    CONSTRAINT uq_language_iso_639_1 UNIQUE (iso_639_1),
    CONSTRAINT uq_language_iso_639_3 UNIQUE (iso_639_3)
);

CREATE INDEX idx_language_is_active ON language_lookup (is_active);

COMMENT ON TABLE language_lookup IS 'Master data: languages (Section 4 Tier 1). Public.';

-- -----------------------------------------------------------------------------
-- REFERENCE CODES
-- Master data: reference codes for every enumeration (Section 4 Tier 1).
-- Rule Group 3 enum rule: single lookup for all fixed-value sets.
-- Columns: domain, code, display_name_key, active flag, sort_order.
-- Natural key: (domain, code), kept as UNIQUE; surrogate id is PK.
-- -----------------------------------------------------------------------------
CREATE TABLE reference_code (
    id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    domain             TEXT     NOT NULL,
    code               TEXT     NOT NULL,
    display_name_key   TEXT     NOT NULL,
    is_active          BOOLEAN  NOT NULL DEFAULT TRUE,
    sort_order         SMALLINT NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by         BIGINT   NOT NULL DEFAULT 0,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by         BIGINT   NOT NULL DEFAULT 0,
    CONSTRAINT uq_reference_code_domain_code UNIQUE (domain, code),
    CONSTRAINT uq_reference_code_display UNIQUE (domain, display_name_key)
);

CREATE INDEX idx_reference_code_domain ON reference_code (domain);
CREATE INDEX idx_reference_code_is_active ON reference_code (is_active);

COMMENT ON TABLE reference_code IS 'Master data: reference codes for every enumeration (Section 4 Tier 1, Rule Group 3 enum rule). Public.';

-- -----------------------------------------------------------------------------
-- UI TRANSLATIONS
-- Master data: UI translation keys (Section 4 Tier 1 master data list includes
--   UI translation keys).
-- Rule Group 7: UI strings stored by key, one row per key and language,
--   with fallback to the default language defined here as the row where
--   is_default = TRUE for that key.
-- Columns:
--   ui_key        TEXT NOT NULL Ã¢â‚¬â€� the key, never displayed to users
--   language_id   BIGINT NOT NULL Ã¢â‚¬â€� references language_lookup
--   value         TEXT NOT NULL Ã¢â‚¬â€� the translated string
--   is_default    BOOLEAN NOT NULL DEFAULT FALSE Ã¢â‚¬â€� exactly one default per key
-- -----------------------------------------------------------------------------
CREATE TABLE ui_translation (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ui_key       TEXT     NOT NULL,
    language_id  BIGINT   NOT NULL,
    value        TEXT     NOT NULL,
    is_default   BOOLEAN  NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by   BIGINT   NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by   BIGINT   NOT NULL DEFAULT 0,
    CONSTRAINT fk_ui_translation_language FOREIGN KEY (language_id)
        REFERENCES language_lookup (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT uq_ui_translation_key_language UNIQUE (ui_key, language_id)
);

CREATE INDEX idx_ui_translation_key ON ui_translation (ui_key);
CREATE INDEX idx_ui_translation_language ON ui_translation (language_id);

COMMENT ON TABLE ui_translation IS 'Master data: UI translation keys (Section 4 Tier 1). Public. Rule Group 7: one row per key and language; fallback to default language row for the key.';

-- -----------------------------------------------------------------------------
-- RELATIONSHIPS SUMMARY Ã¢â‚¬â€� Master Data (Milestone 3, B8/B9, B10/B11 context)
--   country 1..* state
--   country 1..* city
--   state 1..* city  (state_id nullable)
--   reference_code 1..* qualification.education_level_code (domain='education_level')
--   language_lookup 1..* ui_translation
--   employment_type, work_type, reference_code, language, skill, industry, job_role:
--       standalone masters referenced by transactional modules with <entity>_id.
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- MASTER vs TRANSACTION DATA
-- Master data (repeatable, standard set, shared across transactions):
--   country, state, city, skill, qualification, industry, job_role,
--   employment_type, work_type, language_lookup, reference_code, ui_translation.
-- All other modules below hold transaction/business data.
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- NEW FROM MY END?
-- No new master entities beyond the docket list. The only structural decisions
-- are:
--   1. qualification.education_level_code references reference_code
--      (domain = 'education_level') rather than a separate education_level
--      table, because the docket says "reference codes for every enumeration"
--      and Rule Group 3 requires a single enum lookup pattern. This is the
--      same pattern used for employment_type, work_type, and other lookups.
--   2. city.state_id is nullable where a city is not in a state. This is a
--      modelling decision for reference-data correctness, not a new entity.
-- Both decisions are recorded in 99_documentation.sql.
-- -----------------------------------------------------------------------------
