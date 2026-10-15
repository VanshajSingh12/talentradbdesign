# Compliance register — Rule Group 1-10

Source of truth: `ddl/99_documentation.sql`.

## Rule Group 1 — Naming conventions

- Design complies.
- Naming rules followed: lower_snake_case table/column names, singular table names, PK named `id`, FK named `<referenced>_id`, index/constraint prefixes used as expected.
- Reserved-word handling: where a desired name collided with a PostgreSQL reserved identifier, the name was changed and the change is recorded. Notable examples:
  - languages master table is `language_lookup`, not `language`.
  - role master table is `role_lookup`, not `role`.
  - wallet table: kept as `wallet` (see wallet note).

## Rule Group 2 — Surrogate keys

- Design complies.
- Surrogate PKs use `BIGINT GENERATED ALWAYS AS IDENTITY`.

## Rule Group 3 — Standard domains

- Design complies.
- Standard domains are applied and cited inline in the DDL.
- Enum lookups use `reference_code` where appropriate.
- Money domains use NUMERIC + currency code.
- Appropriate bounded vs unbounded TEXT decisions are annotated.

## Rule Group 4 — Audit / lifecycle

- Design complies.
- Business tables carry `created_at`, `created_by`, `updated_at`, `updated_by` where appropriate.
- Soft-delete, effective-dated history, and append-only tables are used as stated in the docket.

## Rule Group 5 — Nullability

- Design complies.
- Nullable columns are justified in comments.
- Unknown vs not-applicable distinctions are kept where relevant.

## Rule Group 6 — Sensitive classification

- Design complies.
- Sensitive columns are tagged in `COMMENT` where required.

## Rule Group 7 — Multilingual

- Design complies.
- Multilingual data and UI strings are handled per the rule.
- UI translations use `ui_translation`; language preferences use `language_lookup` references.

## Rule Group 8 — Analytics prefix

- Design complies.
- Analytics objects use the `analytics_` prefix.

## Rule Group 9 — Licences / seats / devices / sessions

- Design complies.
- Relevant structures are in `07_licences.sql`.

## Rule Group 10 — Subscriptions / wallet / payments / download history

- Design complies.
- Ledger-style and append-only patterns are used where required.
- Relevant structures are in `09_subscriptions.sql`.

## Deviations

- Any deviation from a rule is recorded in `ddl/99_documentation.sql` with a reason.
- If no deviation is recorded for a rule, the design is treated as compliant for that rule.
