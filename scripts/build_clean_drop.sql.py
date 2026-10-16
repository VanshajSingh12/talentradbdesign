
from pathlib import Path

ddl_root = Path("/ddl")
files = [
 "01_master_data.sql",
 "02_profile.sql",
 "03_jobs_applications.sql",
 "04_administration.sql",
 "05_organisation.sql",
 "06_gig_marketplace.sql",
 "07_licences.sql",
 "08_sourcing.sql",
 "09_subscriptions.sql",
 "10_notifications.sql",
 "11_analytics.sql",
 "12_tier3_stretch.sql",
 "99_documentation.sql",
]

name_to_file = {}
for f in files:
    text = Path(ddl_root / f).read_text(encoding="utf-8", errors="replace")
    for m in __import__("re").finditer(r"CREATE TABLE (\w+)\s*\(", text, __import__("re").M):
        name_to_file.setdefault(m.group(1), f)

wanted = [
 "country","state","city","skill","qualification","industry","job_role",
 "employment_type","work_type","language_lookup","reference_code","ui_translation",
 "candidate_identity","candidate_contact","candidate_education","candidate_work_experience",
 "candidate_skill","candidate_language","resume_template","resume_version","profile_project",
 "assessment","course_enrolment","profile_completion_score","profile_view_history",
 "candidate_activity_log","candidate_shortlist_entry","candidate_shortlist_history",
 "referral_tracking","job_requirement","job_position","job_requirement_skill",
 "job_requirement_requirement","job_questionnaire","job_questionnaire_question",
 "job_publish_state","application","application_pipeline_event",
 "candidate_job_search_history","candidate_application_history",
 "users","credential_verification","credential_recovery","role_lookup","role_assignment",
 "permission","permission_assignment","session_record","consent_record","audit_event",
 "blocking_list",
 "tenant_account","account_status_history","employer_organisation","company_location",
 "tax_registration_identifier","verification_status_record","recruiter_mapping",
 "organisation_hierarchy","account_administrator",
 "gig_request_detail","gig_worker_profile","gig_worker_availability","gig_application",
 "gig_assignment","gig_handoff_reference","gig_earnings_reference","gig_favourite",
 "gig_blacklist","gig_rating",
 "subscription_licence","seat_allocation","device_registration","device_session",
 "login_history","session_revocation_event",
 "sourcing_request","consultant_decision","sourcing_shortlist","outreach_batch",
 "outreach_batch_recipient",
 "subscription_plan","plan_entitlement","subscription_period","payment_order",
 "payment_status_history","invoice","refund","wallet_account","wallet_ledger_entry",
 "profile_download_history",
 "notification_preference","job_alert_preference","language_preference","privacy_setting",
 "notification_delivery","community_post","community_post_reaction","support_ticket",
 "support_ticket_reply","faq","faq_category","referral_event",
 "analytics_dim_date","analytics_dim_country","analytics_dim_city",
 "analytics_dim_employer_organisation","analytics_dim_candidate","analytics_dim_job_requirement",
 "analytics_dim_application_pipeline_stage","analytics_fact_application_pipeline",
 "analytics_fact_time_to_hire","analytics_fact_source_channel","analytics_fact_employer_activity",
 "analytics_fact_candidate_activity","analytics_fact_gig_marketplace",
 "analytics_agg_pipeline_funnel_by_day","analytics_agg_time_to_hire_by_month",
 "analytics_agg_source_channel_by_month","analytics_agg_employer_activity_by_month",
 "analytics_agg_candidate_activity_by_month","analytics_agg_gig_marketplace_by_day",
 "salary_benchmark","company_rating","trending_job_snapshot","dashboard_aggregate","feature_flag",
 "schema_map_milestone_order",
]

lines = []
for name in wanted:
    if name in name_to_file:
        lines.append(f'DROP TABLE IF EXISTS public."{name}" CASCADE;')
print("\n".join(lines))
