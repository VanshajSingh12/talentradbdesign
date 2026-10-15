# Master vs transaction data

This file classifies each module’s entities as master-like or transaction-like, with rationale. It is a companion to the DDL and the module index.

## Definitions used here

- Master data: repeatable, standard set, shared across transactions. Stable identifiers, often referenced by many transactional rows.
- Transaction data: time-varying business events, state changes, ownership, per-entity records, audit/history, ledger entries.

A table can be “master-like” even if it is not purely reference data; the test is whether it represents a relatively stable shared concept rather than a per-event business fact.

## Module classification

### 01_master_data.sql
- Master: country, state, city, skill, qualification, industry, job_role, employment_type, work_type, language_lookup, reference_code, ui_translation
- Commentary: all are standard repeatable reference data.

### 02_profile.sql
- Master-like: resume_template
- Transaction-like: candidate_identity, candidate_contact, candidate_education, candidate_work_experience, candidate_skill, candidate_language, resume_version, profile_project, assessment, course_enrolment, profile_completion_score, profile_view_history, candidate_activity_log, candidate_shortlist_entry, candidate_shortlist_history, referral_tracking, candidate_skill_affinity, candidate_tag
- Commentary: profile tables are per-candidate business data, not shared master. resume_template is master because it is a reusable template catalog.

### 03_jobs_applications.sql
- Transaction-like: job_requirement, job_position, job_requirement_skill, job_requirement_requirement, job_questionnaire, job_questionnaire_question, job_publish_state, application, application_pipeline_event, candidate_job_search_history, candidate_application_history, job_requirement_tag, application_tag, application_denial_code
- Commentary: jobs and applications are transactional business objects. Tags are attached transactionally even though the tag master is master data.

### 04_administration.sql
- Master-like: role_lookup, permission
- Transaction-like: users, credential_verification, credential_recovery, role_assignment, permission_assignment, session_record, consent_record, audit_event, blocking_list
- Commentary: role/permission catalogs are master-like; users, assignments, sessions, consent, audit, blocking are transactional or lifecycle data.

### 05_organisation.sql
- Master-like: tenant_account, employer_organisation, company_location, tax_registration_identifier, verification_status_record, account_status_history, organisation_hierarchy, recruiter_mapping, account_administrator
- Commentary: org/account objects are stable shared entities; some carry lifecycle history, but they remain master-like from the system’s point of view.

### 06_gig_marketplace.sql
- Transaction-like: gig_request_detail, gig_worker_profile, gig_worker_availability, gig_application, gig_assignment, gig_handoff_reference, gig_earnings_reference, gig_favourite, gig_blacklist, gig_rating
- Commentary: gig objects are business events/assignments/ratings. Worker profile is per-worker business data, not shared platform master.

### 07_licences.sql
- Transaction-like: subscription_licence, seat_allocation, device_registration, device_session, login_history, session_revocation_event
- Commentary: licences and device/session records are per-tenant/per-user business governance data, even if licence settings are stable.

### 08_sourcing.sql
- Master-like: sourcing_request, consultant_decision, sourcing_shortlist, outreach_batch, outreach_batch_recipient
- Commentary: sourcing objects are request/decision/list records, stable enough to model as master-like within sourcing, though they are still business records.

### 09_subscriptions.sql
- Master-like: subscription_plan, plan_entitlement
- Transaction-like: subscription_period, payment_order, payment_status_history, invoice, refund, wallet_account, wallet_ledger_entry, profile_download_history
- Commentary: plan catalog is master; periods, payments, wallet ledger, downloads are transactional.

### 10_notifications.sql
- Master-like: notification_preference, job_alert_preference, language_preference, privacy_setting, community_post, community_post_reaction, support_ticket, support_ticket_reply, faq, faq_category, referral_event
- Transaction-like: notification_delivery
- Commentary: preferences, community content, support tickets, FAQ are relatively stable shared objects; delivery is transactional.

### 11_analytics.sql
- Dimension-like: analytics_dim_date, analytics_dim_country, analytics_dim_city, analytics_dim_employer_organisation, analytics_dim_candidate, analytics_dim_job_requirement, analytics_dim_application_pipeline_stage
- Fact-like: analytics_fact_application_pipeline, analytics_fact_time_to_hire, analytics_fact_source_channel, analytics_fact_employer_activity, analytics_fact_candidate_activity, analytics_fact_gig_marketplace, analytics_fact_skill_affinity, analytics_fact_application_denial
- Aggregate-like: analytics_agg_pipeline_funnel_by_day, analytics_agg_time_to_hire_by_month, analytics_agg_source_channel_by_month, analytics_agg_employer_activity_by_month, analytics_agg_candidate_activity_by_month, analytics_agg_gig_marketplace_by_day, analytics_agg_denial_by_stage, analytics_agg_dashboard_summary
- Commentary: analytics objects are analytical, not application master or transactional OLTP data.

### 12_tier3_stretch.sql
- Master-like: salary_benchmark, company_rating, trending_job_snapshot, dashboard_aggregate, feature_flag
- Commentary: these are reference/dashboard objects, not application transactional data.

## Master data we offer as a standard set

- Geography: country, state, city
- Skills: skill, skill_ancestor, skill_synonym
- Qualifications, industries, job roles, employment types, work types
- Languages: language_lookup
- Enums: reference_code
- UI: ui_translation
- Tagging: tag_category, tag
- Plans and entitlements: subscription_plan, plan_entitlement
- Roles and permissions: role_lookup, permission
- FAQ: faq_category, faq
- Tier 3 reference/dashboard: salary_benchmark, company_rating, feature_flag, dashboard_aggregate

## Relationship-first design

For each module, relationships were identified before columns wherever practical.  
Examples:

- country 1..* state, country 1..* city, state 1..* city
- skill 1..* candidate_skill, skill 1..* job_requirement_skill, skill 1..* skill_ancestor, skill 1..* skill_synonym
- tag_category 1..* tag, tag 1..* candidate_tag, tag 1..* job_requirement_tag, tag 1..* application_tag
- candidate_identity 1..* candidate_contact/education/work_experience/skill/language/resume_version/profile_project/assessment/course_enrolment/scoring/activity/tag/affinity
- employer_organisation 1..* company_location, tax_registration_identifier, verification_status_record, industry_classification, competitor_intel
- tenant_account 1..* employer_organisation, subscription_licence, wallet_account
- job_requirement 1..* job_position, job_requirement_skill, job_requirement_tag, application, denial_code
- application 1..* application_pipeline_event, application_tag, denial_code
- wallet_account 1..* wallet_ledger_entry
- subscription_plan 1..* subscription_period, plan_entitlement
- gig_request_detail 1..* gig_assignment, gig_favourite, gig_blacklist, gig_rating
- analytics dims and facts joined through date/key dimensions
- Tier 3 stretch objects kept separate but referenceable where applicable

## Relationship cardinalities used in this design

Common patterns:
- 1..1 where a child is the natural extension of a parent (for example, gig_request_detail 1..1 job_requirement, candidate_skill_affinity 1..1 current snapshot per candidate, wallet_account 1..1 per tenant/currency where applicable).
- 1..* where a master is referenced by many business rows (for example, country 1..* city, skill 1..* candidate_skill, job_requirement 1..* application).
- ..* where many-to-many is resolved through join/assignment tables (for example, recruiter_mapping, role_assignment, permission_assignment, seat_allocation).

## Why relationship-first matters here

- It prevents creating columns first and then inventing relationships later.
- It makes referential integrity and indexing choices easier to justify.
- It keeps master data clearly separated from transactional attachments, which reduces the chance of putting transaction-specific columns in master tables.

## Current differentiators, restated as master/transaction additions

Master additions:
- skill_ancestor, skill_synonym, tag_category, tag
- organisation_industry_classification, organisation_competitor_intel
- password_policy, account_security_policy

Transaction additions:
- candidate_skill_affinity, candidate_tag
- job_requirement_tag, application_tag, application_denial_code

All are scoped to docket domains and are intended to be competitive differentiators, not generic extras.
