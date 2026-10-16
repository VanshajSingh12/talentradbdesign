# B66 — Seed validation report

**Backlog owner:** Team
**Milestone:** 20 — Queries and validation across all modules
**Database:** `talentra` on `localhost:5431`
**Run time:** 2026-10-16T13:20:13.199902+00:00

## Purpose

Validate the seeded data against **Section 5 — Data Standards and Domain Rules** and the **coverage gap register**, and record any failures.

The automated checks are assertions about the schema and the current seeded rows. A `FAIL` or `ERROR` in this report means the automated assertion found an exception that needs review; it is not, by itself, a judgment that the whole seed is invalid.

## Checks against Section 5

| Rule group | Check | Result | Notes |
|---|---|---|---|
| RG1 | Table names are `snake_case` singular | **PASS** | No public tables violate the naming pattern. |
| RG1 | Column names are `snake_case` | **PASS** | No public columns violate the naming pattern. |
| RG1 | Primary key columns are named `id` | **PASS** (public business tables only) | Checked only the public schema's business tables. System catalog tables such as `pg_proc` use `oid`, which is expected and excluded from this check. |
| RG2 | Business tables have a surrogate PK `id` | **ERROR** | The check SQL had a syntax error, so no conclusion was reached. Needs a fix to the query, not the seed. |
| RG2 | `users.email` has a unique constraint | **PASS** | `uq_users_email` exists. |
| RG3 | Money columns have a companion currency code column | **FAIL** | See failures below. |
| RG4 | Audit events carry `created_by` / `updated_by` | **ERROR** | The seeded `audit_event` table does not have a `created_by` column. |
| RG4 | Business tables carry `deleted_at` | **ERROR** | The check SQL had a syntax error, so no conclusion was reached. Needs a fix to the query. |
| RG5 | No empty/NA sentinel email address | **PASS** | No seeded user uses `''` or `'NA'` as email. |
| RG5 | No zero salary disguised as missing | **PASS** | No seeded work-experience row has `salary_min = 0` or `salary_max = 0`. |
| RG6 | Sensitive columns have a comment classifying them | **ERROR** | The comment lookup query used a non-castable `oid` expression and could not run. Needs a fix to the query. |
| RG8 | Analytics objects are prefixed `analytics_` | **FAIL** | See failures below. |

### Failures needing review

#### RG3 — Money columns without a companion currency code column

The schema has several `numeric` money-type columns that do not have a matching `*_currency_code` column in the same table.

| table | column |
|---|---|
| `analytics_dim_job_requirement` | `compensation_min` |
| `analytics_dim_job_requirement` | `compensation_max` |
| `analytics_fact_gig_marketplace` | `earnings_amount` |
| `gig_application` | `bid_amount` |
| `gig_earnings_reference` | `earnings_amount` |

For an analytics dimension/fact these columns are denormalized snapshots, so the missing currency code is a documentation/modeling question rather than a row-level data corruption issue. For transaction tables such as `gig_application`, the currency context for `bid_amount` should be explicit.

#### RG8 — Analytics-table prefix not applied to some tables

The automated check expects every analytical table to be prefixed `analytics_`. A few tables in the seeded schema are analytical in purpose but not prefixed that way, or are flagged only because the exclusion list was incomplete.

| table | note |
|---|---|
| `industry` | domain lookup, not analytics |
| `job_role` | domain lookup, not analytics |
| `faq_category` | lookup table, not analytics |
| `credential_verification` | transactional/admin, not analytics |
| `credential_recovery` | transactional/admin, not analytics |
| `account_status_history` | history/audit, not prefixed analytics_ |
| `candidate_application_history` | history, not prefixed analytics_ |
| `candidate_job_search_history` | history, not prefixed analytics_ |
| `candidate_shortlist_history` | history, not prefixed analytics_ |
| `course_enrolment` | transactional, not analytics |

The rule itself is about analytics objects. The clear “failure” here is that history/audit tables such as `*_history` are not named under the analytics prefix, which is probably correct — but the project should make the naming convention for history versus analytics explicit so the automated check can be written correctly.

## Coverage gap register

The coverage gap register lists tables the docket expects to exist, but are **missing from the current seeded schema**.

### Missing core tables

- `job_requirement_tag`
- `application_tag`
- `application_denial_code`
- `application_denial_record`
- `skill_synonym`
- `skill_ancestor`
- `tag_category`
- `tag`
- `candidate_tag`
- `password_policy`
- `account_security_policy`

### Tier 3 stretch tables

All Tier 3 stretch tables listed in the check were present:

- `salary_benchmark`
- `company_rating`
- `trending_job_snapshot`
- `dashboard_aggregate`
- `feature_flag`

## Summary

**Checks run:** 12 automated Section 5 checks + coverage gap register for expected tables.

**Failures/errors:** 6

- RG2 business-table surrogate PK check — query syntax error, inconclusive
- RG3 money columns without companion currency code
- RG4 audit-event `created_by` column missing
- RG4 business-table `deleted_at` check — query syntax error, inconclusive
- RG6 sensitive-column comment check — query error, inconclusive
- RG8 analytics prefix — false positives / naming-convention clarification needed

**Coverage gaps:** 11 missing core tables.

## Interpretation

- The strongest concrete data-standard issue found in this run is that the **seeded `audit_event` table does not yet have `created_by`**, which Section 5 Rule Group 4 expects for business/audit data.
- The **money-with-currency** and **analytics-prefix** items are partial failures: they flag real schema-design questions, but several flagged items are history or analytics snapshot tables rather than core transactional money columns.
- The **missing coverage tables** are the main gap between the current seed and the full docket footprint. Several of them (tagging, denial codes, skill taxonomy, password policy) are exactly the modules that the query set in B65 could not exercise.

## Companion artifacts

- Automated validation run with per-check SQL and samples: `scripts/reports/B66_seed_validation_report.txt`
- Query set whose coverage depends on these tables: `docs/team_deliverables/B65_query_set_with_output_and_execution_plans.md`
