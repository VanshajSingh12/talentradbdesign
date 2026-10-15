# Competitor gap analysis

This is a readable companion to the DDL modules. It is not an excuse to add out-of-docket data. It is a way to explain, in plain language, why this schema is more detailed than a typical Naukri/Monster/LinkedIn-style public schema in a few specific, defensible places.

## How to read this

- “Competitor baseline” = what a typical job platform usually stores for that domain.
- “What we add that is competitive” = areas where this schema goes further.
- “What is unique and defensible here” = parts that are both unusual for competitors and clearly tied to the docket scope.

## Master data — `ddl/01_master_data.sql`

Competitor baseline:
- Countries, states, cities, skills, industries, job roles, employment types, languages, reference codes.
- Skills are often flat tags; taxonomy is usually in a search service, not in the schema.

What we add that is competitive:
- Explicit master schema for qualifications, employment types, work types, reference codes, UI translations.
- Reference data modeled with stable surrogate keys and enforceable unique constraints.

What is unique and defensible here:
- `skill_ancestor` — explicit skill taxonomy/ancestry master.
- `skill_synonym` — multilingual skill synonyms.
- `tag_category`, `tag` — shared tagging taxonomy reused across Profile, Jobs, Applications.
- `language_lookup` instead of bare `language` (reserved-word-safe naming, multilingual domain).

Why this matters:
- A lot of platforms treat skills as strings and push normalization to search. This design stores the skill normalization structure explicitly in master data, so skill affinity, deduplication, and multilingual matching have a first-class model.

## Profile — `ddl/02_profile.sql`

Competitor baseline:
- Candidate identity, contact, education, experience, skills, languages.
- Resume, sometimes assessments and referrals.

What we add that is competitive:
- Full contact model, education, work experience with money domain, language preference, resume versions/templates, projects, assessments, course enrolments, profile completion scoring, view history, activity log, shortlist/bookmark history, referral tracking.
- Tier 2 fully included without omissions.

What is unique and defensible here:
- `candidate_skill_affinity` — a computed skill-affinity snapshot for a candidate.
- `candidate_tag` — flexible candidate tagging using the shared tag master.

Why this matters:
- Competitors often expose skill lists and endorsements, but rarely expose a system-computed skill-affinity snapshot as a first-class, queryable profile object. A shared tagging taxonomy also lets recruiters classify candidates beyond master skills.

## Jobs and Applications — `ddl/03_jobs_applications.sql`

Competitor baseline:
- Job posting, positions, requirements, status, applications, pipeline stages.

What we add that is competitive:
- Job requirement lifecycle with positions, requirement line items, questionnaires, publish state.
- Application pipeline events and candidate job search/application history.

What is unique and defensible here:
- `job_requirement_tag` — tags on job requirements.
- `application_tag` — tags on applications.
- `application_denial_code` — structured, analytics-grade rejection reason codes.

Why this matters:
- Most platforms keep rejection reasons as free text or not at all. Structured denial codes let the platform measure funnel attrition by reason, not just by stage. Tagging jobs and applications also supports recruiter-driven categorization above master skills.

## Administration — `ddl/04_administration.sql`

Competitor baseline:
- User/account, password, roles, sessions, audit, consent, blocking.

What we add that is competitive:
- Credential verification and recovery modeled separately from the password.
- Roles, permissions, assignments, sessions, consent, audit, blocking list.

What is unique and defensible here:
- `password_policy` — platform-wide password rules.
- `account_security_policy` — per-account security policy with lockout windows, session limits, MFA-required flag.
- Reserved-name-safe `role_lookup`.

Why this matters:
- Public competitor schemas rarely expose full credential governance and per-account security policy as a first-class design. Separating verification/recovery from the user row is also a more defensible credential design than folding everything into one table.

## Organisation and Account — `ddl/05_organisation.sql`

Competitor baseline:
- Employer/company profile, locations, account status, hierarchy, recruiters.

What we add that is competitive:
- Tenant account, employer organisation, hierarchy, recruiter mapping, company locations, tax registration, verification status, account administrators.

What is unique and defensible here:
- `organisation_industry_classification` — an employer can carry more than one industry classification.
- `organisation_competitor_intel` — linkage to company review/salary reference data (Section 6 boundary).

Why this matters:
- Real enterprises span industries. A single industry tag is a common shortcut on competitor profiles; this schema supports multi-classification. Linking competitor/salary/review reference data to the employer is also a common analytics gap on job platforms.

## Gig Marketplace — `ddl/06_gig_marketplace.sql`

Competitor baseline:
- Gig postings, worker profiles, applications, assignments, in some cases ratings or favorites.

What we add that is competitive:
- Gig request details, worker profiles, availability, applications, assignments, handoff references, earnings references, favorites, blacklists, ratings.
- Shared-core job model decision with gig extension table.

What is unique and defensible here:
- Explicit gig handoff and earnings-reference tracking.
- Gig worker availability modeled with windows.
- Non-overlap considerations for gig worker windows.

Why this matters:
- Gigs are usually treated as “jobs with a flag.” This design gives gigs their own structured extension while still sharing the core job/application model where appropriate, and it tracks handoffs and earnings references that are often missing or implicit.

## Licences / Seats / Devices / Sessions — `ddl/07_licences.sql`

Competitor baseline:
- Seat/license limits at the account level, device login, session management.

What we add that is competitive:
- Subscription licence with max users and max devices per user, seat allocation, device registration, device session, login history, session revocation event.

What is unique and defensible here:
- Device-bound session counting.
- Revocable sessions with auditable revocation.
- Login history with device context.

Why this matters:
- Many platforms track seats and devices, but the device-per-user session model with auditable revocation is more explicit than a generic “active session” counter.

## Sourcing and Consultant — `ddl/08_sourcing.sql`

Competitor baseline:
- Job requisitions, recruiter assignments, candidate shortlists.

What we add that is competitive:
- Sourcing requests, consultant decisions, sourcing shortlists, outreach batches, outreach recipients.

What is unique and defensible here:
- Consultant decision modeled with the open-requirements constraint.
- Outreach batches with per-recipient delivery status and outbound tracking.

Why this matters:
- Sourcing is often reduced to “applied candidates.” This design separates sourcing requests, consultant decisions, shortlists, and outreach as distinct domains, which is more useful for managed sourcing/consultant workflows.

## Subscriptions / Wallet / Payments / Download History — `ddl/09_subscriptions.sql`

Competitor baseline:
- Plans, subscription periods, payments, invoices, refunds, sometimes wallet or credits.

What we add that is competitive:
- Plans, entitlements, subscription periods, payment orders, payment status history, invoices, refunds, wallet account, wallet ledger entries, profile download history.
- Append-only wallet ledger with correction references to the original.
- Non-overlapping subscription periods.
- Download history with actor/subject/timestamp/credit deduction.

What is unique and defensible here:
- Wallet renamed to `wallet_account` for strict reserved-word safety.
- Append-only wallet ledger with balance-after and correction references.
- Profile download history tied to credit deduction.

Why this matters:
- Wallet/credit patterns are usually either very simple or hidden behind billing. This schema makes the wallet ledger append-only with balance-after and correction references, which is a stronger financial-auditing pattern than a mutable balance column plus ad hoc edits.

## Notifications / Preferences / Community — `ddl/10_notifications.sql`

Competitor baseline:
- Notification preferences, sometimes community posts, support tickets, FAQ.

What we add that is competitive:
- Notification preferences, job alert preferences, language preference, privacy settings, notification delivery, community posts, reactions, support tickets, replies, FAQ categories, FAQs, referral events.

What is unique and defensible here:
- High-volume delivery write path modeled explicitly.
- Multilingual preferences and FAQ with language tracking.
- Community post reactions and support ticket workflow.

Why this matters:
- Notification delivery is often treated as a side effect. Here it is a first-class write path with status and channel tracking, which supports high-volume delivery and audit.

## Analytics — `ddl/11_analytics.sql`

Competitor baseline:
- Aggregated dashboards, sometimes basic funnel or activity reports.

What we add that is competitive:
- Star-schema dimensions, facts, and aggregates for pipeline, time-to-hire, source/channel, employer activity, candidate activity, gig marketplace.
- SCD-style dimensions for employer, candidate, job requirement.
- Aggregates for recurring KPI refresh.

What is unique and defensible here:
- `analytics_fact_skill_affinity`
- `analytics_fact_application_denial`
- `analytics_agg_denial_by_stage`
- `analytics_agg_dashboard_summary`

Why this matters:
- Most job-platform analytics stop at basic vacancy/application counts. This design includes skill-affinity facts, denial-funnel facts, and dashboard aggregates, which support KPIs competitors rarely expose as first-class data.

## Tier 3 stretch — `ddl/12_tier3_stretch.sql`

Competitor baseline:
- Salary ranges, company ratings, trending jobs, dashboards, feature flags are often bolted on later or owned by separate services.

What we add that is competitive:
- Salary benchmarks, company ratings, trending job snapshots, dashboard aggregates, feature flags.

What is unique and defensible here:
- All five selected Tier 3 items included as a separate, clearly labelled optional stretch module.

Why this matters:
- These are useful differentiators, but they are kept optional and separate, so they do not pollute the core schema.

## Overall differentiator summary

Unique and defensible differentiators in this schema:

1. Explicit skill taxonomy + synonyms + shared tag taxonomy.
2. Computed candidate skill-affinity snapshot.
3. Structured denial codes for applications.
4. Credential verification/recovery separated from the user row, plus password and account security policy masters.
5. Multi-industry classification for employers.
6. Competitor/salary/review reference linkage to employers.
7. Append-only wallet ledger with correction references.
8. Device-bound sessions with auditable revocation.
9. High-volume notification delivery write path.
10. Skill-affinity and denial-funnel analytics facts and aggregates.
11. Optional Tier 3 stretch module for salary benchmarks, company ratings, trending snapshots, dashboard aggregates, feature flags.

All additions stay within docket scope and do not invent out-of-docket entities.
