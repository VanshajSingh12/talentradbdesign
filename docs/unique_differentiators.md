# Unique differentiators added from the team side

This lists the data and structural choices added on top of the docket baseline, with rationale and where each lives. Every item is intended to be defensible against “why is this in the schema?” and “what competitor data is it beating?”

## 1. Skill taxonomy, synonyms, and shared tagging

Where:
- `ddl/01_master_data.sql`: `skill_ancestor`, `skill_synonym`, `tag_category`, `tag`
- Used by: `02_profile.sql`, `03_jobs_applications.sql`

What is new from our side:
- Explicit skill ancestry/taxonomy master, instead of flat skill tags only.
- Multilingual skill synonym master.
- Shared tag taxonomy that can tag candidates, jobs, and applications.

Why it is a differentiator:
- Many job platforms treat skills as strings and push normalization, synonyms, and taxonomy to search or a separate service. This schema stores the skill structure in master data, which supports skill matching, deduplication, and multilingual matching without assuming a separate taxonomy product.

## 2. Computed candidate skill affinity

Where:
- `ddl/02_profile.sql`: `candidate_skill_affinity`
- Analytics: `ddl/11_analytics.sql`: `analytics_fact_skill_affinity`

What is new from our side:
- A stored snapshot of a candidate’s computed skill affinity.

Why it is a differentiator:
- Most competitor profile schemas expose skills and endorsements, but not a first-class, queryable system-computed skill-affinity snapshot. This gives recruiters a normalized skill-match signal without recomputing it at read time every time.

## 3. Structured application denial codes

Where:
- `ddl/03_jobs_applications.sql`: `application_denial_code`
- Analytics: `ddl/11_analytics.sql`: `analytics_fact_application_denial`, `analytics_agg_denial_by_stage`

What is new from our side:
- Rejection/denial reason codes attached to applications, with analytics-grade structure.

Why it is a differentiator:
- Competitors usually keep rejection reasons as free text, if at all. Structured denial codes let the platform measure attrition by reason, not just by stage, which is a meaningful funnel-analytics advantage.

## 4. Tagging on jobs and applications

Where:
- `ddl/03_jobs_applications.sql`: `job_requirement_tag`, `application_tag`

What is new from our side:
- Recruiter-facing tagging of job requirements and applications, built on the shared tag master.

Why it is a differentiator:
- Tagging above master skills gives recruiters a flexible way to categorize jobs and applications without expanding the core skill model. This is more flexible than the usual fixed-category approach on competitor job postings.

## 5. Credential governance and security policy

Where:
- `ddl/04_administration.sql`: `credential_verification`, `credential_recovery`, `password_policy`, `account_security_policy`

What is new from our side:
- Credential verification and recovery separated from the password/user row.
- Password policy master.
- Account security policy with lockout windows, session limits, and MFA-required flag.

Why it is a differentiator:
- This is a stronger credential and security posture than many public competitor schemas, which often cram auth state into the user row. It is also best-practice-consistent for credential handling.

## 6. Multi-industry classification and competitor intel linkage

Where:
- `ddl/05_organisation.sql`: `organisation_industry_classification`, `organisation_competitor_intel`

What is new from our side:
- Employers can carry more than one industry classification.
- Employers can be linked to competitor/salary/review reference data with source attribution and refresh date.

Why it is a differentiator:
- Real employers span industries. A single industry tag is a common competitor shortcut. Linking review/salary reference data to the employer is also a common analytics gap.

## 7. Append-only wallet ledger with corrections

Where:
- `ddl/09_subscriptions.sql`: `wallet_account`, `wallet_ledger_entry`
- Also: `wallet_account` renamed from `wallet` for strict reserved-word safety.

What is new from our side:
- Wallet ledger is append-only, with balance-after and correction references to the original entry.
- Wallet balance is not editable by ad hoc updates.

Why it is a differentiator:
- A mutable balance column with edits is a weak auditing model. An append-only ledger with corrections is a stronger financial-auditing pattern and supports cleaner credit/recharge/usage history.

## 8. Device-bound sessions and auditable revocation

Where:
- `ddl/07_licences.sql`: `device_registration`, `device_session`, `device_session` counting considerations, `session_revocation_event`

What is new from our side:
- Device-level session identity and device-bound active session counting.
- Auditable session revocation.

Why it is a differentiator:
- Many platforms track “active sessions” loosely. This design makes the device/session relationship explicit enough to support per-user device-limit enforcement and revocation auditing.

## 9. High-volume notification delivery write path

Where:
- `ddl/10_notifications.sql`: `notification_delivery`

What is new from our side:
- Notification delivery is modeled as a first-class write path with status, channel, scheduling, and delivery reference.

Why it is a differentiator:
- Notification delivery is often treated as a side effect. Modeling it explicitly supports high-volume delivery, status tracking, and audit.

## 10. Analytics facts and aggregates competitors rarely expose

Where:
- `ddl/11_analytics.sql`: skill affinity fact, denial fact, denial aggregate, dashboard aggregate, plus pipeline/time-to-hire/source/channel/employer/candidate/gig facts and aggregates.

What is new from our side:
- Skill-affinity analytics fact.
- Denial-funnel analytics fact and aggregate.
- Dashboard aggregate for Tier 3-style dashboard KPIs.

Why it is a differentiator:
- Most job-platform analytics stop at vacancy/application/placement counts. These facts and aggregates support KPIs like skill-affinity distribution and denial-funnel analysis.

## 11. Optional Tier 3 stretch module

Where:
- `ddl/12_tier3_stretch.sql`: `salary_benchmark`, `company_rating`, `trending_job_snapshot`, `dashboard_aggregate`, `feature_flag`

What is new from our side:
- All five selected Tier 3 items included as a separate, clearly labelled optional stretch module.

Why it is a differentiator:
- Salary benchmarks, company ratings, trending snapshots, dashboard config, and feature flags are common “later add-ons” on job platforms. Including them as a separate optional module makes the roadmap explicit without polluting the core schema.

## What we deliberately did not add

- No out-of-docket entities.
- No personal data stored beyond what the docket domains imply.
- No assumed live external integrations; external systems are boundaries, not in-database state.

## Summary table

| Differentiator | Module | Why it beats typical competitor coverage |
|---|---|---|
| Skill taxonomy + synonyms | Master data | Skill structure is explicit, not just flat tags |
| Shared tagging | Master data + Profile + Jobs | Flexible categorization above master skills |
| Candidate skill affinity | Profile + Analytics | System-computed affinity snapshot, unusual for competitors |
| Application denial codes | Jobs + Analytics | Structured rejection reasons, not free text |
| Credential + security policy | Administration | Stronger credential governance than typical |
| Multi-industry classification | Organisation | Real employers span industries |
| Competitor intel linkage | Organisation | Salary/review reference linkage is a common gap |
| Append-only wallet ledger | Subscriptions | Stronger wallet auditing than mutable balance |
| Device-bound sessions | Licences | Clearer device/session enforcement and revocation |
| Notification delivery path | Notifications | Delivery is first-class, not a side effect |
| Skill affinity + denial analytics | Analytics | KPIs competitors rarely expose |
| Tier 3 stretch module | Tier 3 stretch | Explicit optional roadmap, not core pollution |

## How to extend this further

If you want more differentiators later, the same rule applies: add only what the docket domains can absorb, prefer explicit structures over vague free text, and keep optional items in their own module when they are not core to Tier 1/Tier 2.
