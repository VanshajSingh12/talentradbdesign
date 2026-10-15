# Module index

This is a readable companion to `ddl/*.sql`. The authoritative schema is in the SQL files.  
This index adds intent, relationship summaries, rules applied, and the unique differentiators added from the team’s side.

## Master data — `01_master_data.sql`

Purpose: repeatable standard reference data shared across transactions.

Key entities:
- country, state, city
- skill, qualification, industry, job_role
- employment_type, work_type
- language_lookup
- reference_code
- ui_translation

Relationships:
- country 1..* state
- country 1..* city
- state 1..* city (state_id nullable for non-state territories)
- reference_code 1..* qualification.education_level_code
- language_lookup 1..* ui_translation

Rules applied:
- Rule Group 1 naming
- Rule Group 3 standard domains + enum lookups
- Rule Group 7 multilingual UI

Unique differentiators added:
- `skill_ancestor` (explicit skill taxonomy / ancestry)
- `skill_synonym` (multilingual skill synonyms)
- `tag_category`, `tag` (shared tagging master reused across Profile, Jobs, Applications)

Notes:
- The languages master table is named `language_lookup`, not `language`, because `language` is a PostgreSQL reserved identifier.

## Profile — `02_profile.sql`

Purpose: candidate profile core and the full Tier 2 profile surface.

Key entities:
- candidate_identity, candidate_contact, candidate_education, candidate_work_experience
- candidate_skill, candidate_language
- resume_template, resume_version
- profile_project
- assessment, course_enrolment
- profile_completion_score
- profile_view_history, candidate_activity_log
- candidate_shortlist_entry, candidate_shortlist_history
- referral_tracking

Relationships:
- candidate_identity 1..1 users (optional)
- candidate_identity 1..* candidate_contact/education/work_experience/skill/language/resume_version/profile_project/assessment/course_enrolment/scoring/activity
- candidate_identity 1..* candidate_tag
- candidate_identity 1..* candidate_skill_affinity
- resume_template 1..* resume_version

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6, 7
- Sensitive columns classified in comments

Unique differentiators added:
- `candidate_skill_affinity` (computed skill-affinity snapshot)
- `candidate_tag` (flexible candidate tagging, using the shared `tag` master)

Notes:
- `resume_body` is the one intentionally unbounded TEXT in Profile, annotated as such.
- Profile projects are shared for candidate + gig projects, type-coded, with gig specifics left to the gig module.

## Jobs and applications — `03_jobs_applications.sql`

Purpose: job requirement lifecycle, positions, requirements, questionnaires, publish state, applications, pipeline events, and candidate job/application history.

Key entities:
- job_requirement, job_position, job_requirement_skill
- job_requirement_requirement
- job_questionnaire, job_questionnaire_question
- job_publish_state
- application, application_pipeline_event
- candidate_job_search_history, candidate_application_history

Relationships:
- employer_organisation 1..* job_requirement
- job_requirement 1..* job_position, job_requirement_skill, job_requirement_tag, job_requirement_requirement, job_questionnaire, application, application_denial_code
- application 1..* application_pipeline_event
- candidate_identity 1..* candidate_job_search_history, candidate_application_history

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6, 7

Unique differentiators added:
- `job_requirement_tag` (tags on job requirements)
- `application_tag` (tags on applications)
- `application_denial_code` (structured rejection reason codes, analytics-grade)

Notes:
- Gigs share this core job + application model; gig-specific fields are in the gig module.

## Administration — `04_administration.sql`

Purpose: shared team identity, credential handling, roles/permissions, sessions, consent, audit, blocking.

Key entities:
- users
- credential_verification, credential_recovery
- role_lookup, role_assignment, permission, permission_assignment
- session_record, consent_record, audit_event, blocking_list

Relationships:
- users 1..* credential_verification, credential_recovery, role_assignment, permission_assignment, session_record, consent_record, audit_event, blocking_list
- role_lookup 1..* role_assignment, permission_assignment
- permission 1..* permission_assignment

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6
- Best-practice credential model documented as a unique security differentiator

Unique differentiators added:
- `password_policy`
- `account_security_policy`

Notes:
- Credential verification and recovery are separated from the password itself, following best practice.
- The role master table is named `role_lookup`, not `role`, because `role` is a PostgreSQL reserved identifier.

## Organisation and account — `05_organisation.sql`

Purpose: tenant account, employer organisation, hierarchy, recruiter mapping, identity/verification status, locations, tax registration.

Key entities:
- tenant_account, account_status_history
- organisation_hierarchy
- employer_organisation, company_location
- tax_registration_identifier, verification_status_record
- recruiter_mapping, account_administrator

Relationships:
- tenant_account 1..* employer_organisation, account_status_history, recruiter_mapping, account_administrator
- employer_organisation 1..* company_location, tax_registration_identifier, verification_status_record, recruiter_mapping
- country 1..* tax_registration_identifier (via country_code)

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6

Unique differentiators added:
- `organisation_industry_classification` (multi-industry classification)
- `organisation_competitor_intel` (linkage to company review/salary boundary data)

Notes:
- recruiter_mapping supports effective-dated recruiter-to-organisation mapping.

## Gig marketplace — `06_gig_marketplace.sql`

Purpose: gig requests, worker profiles, availability, gig applications, assignments, handoffs, earnings, favourites, blacklist, ratings.

Key entities:
- gig_request_detail, gig_worker_profile, gig_worker_availability
- gig_application, gig_assignment
- gig_handoff_reference, gig_earnings_reference
- gig_favourite, gig_blacklist, gig_rating

Relationships:
- job_requirement 1..1 gig_request_detail
- candidate_identity 1..1 gig_worker_profile
- gig_worker_profile 1..* gig_worker_availability, gig_application, gig_assignment, gig_favourite, gig_blacklist, gig_rating
- gig_request_detail 1..* gig_assignment, gig_favourite, gig_blacklist, gig_rating

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6

Notes:
- Gig worker window non-overlap considerations are reflected in the gig module design.

## Licences / seats / devices / sessions — `07_licences.sql`

Purpose: licence/governance, seat allocation, device registration, device sessions, login history, session revocation.

Key entities:
- subscription_licence, seat_allocation
- device_registration, device_session
- login_history, session_revocation_event

Rules applied:
- Rule Group 9
- Audit and revocation support

Notes:
- Device limit at login, seat allocation, and active session counting are modeled here.

## Sourcing and consultant — `08_sourcing.sql`

Purpose: sourcing requests, consultant decisions, shortlists, outreach batches and recipients.

Key entities:
- sourcing_request, consultant_decision, sourcing_shortlist
- outreach_batch, outreach_batch_recipient

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6
- Docket rules B37 and B46 reflected where applicable

Notes:
- Consultant decisions are tied to open requirement context per the docket rule.

## Subscriptions / wallet / payments / download history — `09_subscriptions.sql`

Purpose: plans, entitlements, subscription periods, payment orders, payment status history, invoices, refunds, wallet, wallet ledger, profile download history.

Key entities:
- subscription_plan, plan_entitlement
- subscription_period
- payment_order, payment_status_history, invoice, refund
- wallet, wallet_ledger_entry, profile_download_history

Rules applied:
- Rule Group 10
- Append-only ledger for wallet
- Non-overlapping subscription periods
- Correction references original
- Download/view history with actor/subject/timestamp/credit deduction

Notes:
- Wallet balance is a sensitive/internal value in the design; the table name is `wallet`.
- See `docs/wallet_table_note.md` for why `wallet` is acceptable here.

## Notifications / preferences / community — `10_notifications.sql`

Purpose: notification preferences, job alert preferences, language preference, privacy settings, notification delivery, community posts, reactions, support tickets, FAQ, referral events.

Key entities:
- notification_preference, job_alert_preference, language_preference, privacy_setting
- notification_delivery
- community_post, community_post_reaction
- support_ticket, support_ticket_reply
- faq, faq_category
- referral_event

Rules applied:
- Rule Group 1, 2, 3, 4, 5, 6, 7
- B57 high-volume delivery path modeled where the docket calls for it

Notes:
- All Tier 2 items selected for notifications/preferences/community are included.

## Analytics — `11_analytics.sql`

Purpose: star-schema dimensions, facts, and aggregates for KPI reporting.

Key entities:
- analytics_dim_date, analytics_dim_country, analytics_dim_city
- analytics_dim_employer_organisation, analytics_dim_candidate, analytics_dim_job_requirement
- analytics_dim_application_pipeline_stage
- analytics_fact_application_pipeline, analytics_fact_time_to_hire, analytics_fact_source_channel
- analytics_fact_employer_activity, analytics_fact_candidate_activity, analytics_fact_gig_marketplace
- analytics_agg_* materialized views

Rules applied:
- Rule Group 8 analytics prefix
- B49/B58 analytics modeling patterns where applicable
- SCD dimension keys and aggregate refresh rules recorded where applicable

Unique differentiators added:
- `analytics_fact_skill_affinity`
- `analytics_fact_application_denial`
- `analytics_agg_denial_by_stage`

Notes:
- These support KPIs like skill-affinity distribution and denial-code funnel analysis.

## Tier 3 stretch — `12_tier3_stretch.sql`

Purpose: optional Tier 3 features, clearly labelled as a separate optional stretch module.

Key entities:
- salary_benchmark
- company_rating
- trending_job_snapshot
- dashboard_aggregate
- feature_flag

Rules applied:
- Placed in its own module so the optional nature is explicit.
- Not required for Tier 1/Tier 2 submission.

Notes:
- This module includes all five selected Tier 3 items: salary benchmarks, company ratings, trending job snapshots, dashboard aggregates, feature flags.

## Documentation artifact — `99_documentation.sql`

Purpose: executable documentation for decisions, Section 6 integration boundaries, Rule Group 1-10 compliance register, and the milestone-order context menu.

Contents:
- Decision notes (DB provider, gig model, credentials, Tier 2, Tier 3)
- Section 6 integration boundaries table
- Rule Group 1-10 compliance register
- `schema_map_milestone_order` (milestone-order entities → relationships → columns)

Reading note:
- The `.sql` file is the authoritative documentation artifact.
- Human-readable summaries are in `docs/*.md`.
