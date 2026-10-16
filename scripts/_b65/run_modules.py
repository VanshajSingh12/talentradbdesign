import importlib.util, datetime, os, psycopg2

spec = importlib.util.spec_from_file_location("harness", "scripts/_b65/harness.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

PG_DSN = h.PG_DSN
REPORT_BASE = h.REPORT_BASE

def R(name):
    return os.path.join(REPORT_BASE, name)

def init_report(path):
    p = R(path)
    with open(p, "w", encoding="utf-8") as f:
        f.write("# Talentra Database Design — Deliverable Reports\n")
        f.write("Generated: " + datetime.datetime.now(datetime.timezone.utc).isoformat() + "\n")
        f.write("Database: talentra on localhost:5431\n\n")
    return p

def write_section(path, header_text, queries):
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + header_text + "\n\n")
        f.write("Module-specific queries validating seeded data for this module.\n\n")
    for label, sql in queries:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n## " + label + "\n\n")
            f.write(sql.strip() + "\n\n")
        try:
            conn = psycopg2.connect(PG_DSN)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
            if rows:
                cols = [d.name for d in cur.description]
                with open(path, "a", encoding="utf-8") as f:
                    f.write("Columns: " + ", ".join(cols) + "\n")
                    f.write("Rows: %d (shown: %d)\n\n" % (len(rows), min(len(rows), 60)))
                    for i, r in enumerate(rows[:60]):
                        if i >= 60:
                            f.write("... truncated ...\n")
                            break
                        parts = []
                        for v in r:
                            parts.append("" if v is None else str(v))
                        f.write(" | ".join(parts) + "\n")
                    f.write("\n")
            else:
                with open(path, "a", encoding="utf-8") as f:
                    f.write("Rows: 0\n\n")
            cur.close()
            conn.close()
        except Exception as e:
            with open(path, "a", encoding="utf-8") as f:
                f.write("Query execution failed: %s\n\n" % e)

# ---------------------------------------------------------------- B67
p_b67 = init_report("B67_member_A_Admin_Org_Gig.txt")
write_section(p_b67, "## Administration module", [
    ("Admin-A1: users active count by actor_type",
     "SELECT actor_type_code, count(*) AS users FROM users WHERE deleted_at IS NULL GROUP BY actor_type_code ORDER BY users DESC;"),
    ("Admin-A2: roles and active role assignments",
     "SELECT rl.code, rl.name, count(ra.id) AS assignments FROM role_lookup rl LEFT JOIN role_assignment ra ON ra.role_id = rl.id AND ra.is_active = true AND ra.deleted_at IS NULL WHERE rl.is_active = true GROUP BY rl.id, rl.code, rl.name ORDER BY rl.code;"),
    ("Admin-A3: role assignments per active user (sample)",
     "SELECT u.id, u.email, u.first_name, u.last_name, rl.code AS role_code, ra.assigned_at FROM users u JOIN role_assignment ra ON ra.user_id = u.id AND ra.is_active = true AND ra.deleted_at IS NULL JOIN role_lookup rl ON rl.id = ra.role_id WHERE u.deleted_at IS NULL ORDER BY u.id LIMIT 10;"),
    ("Admin-A4: active sessions per user, last activity (sample)",
     "SELECT u.id, u.email, sr.id AS session_id, sr.started_at, sr.last_activity_at, sr.expires_at, sr.is_revoked FROM users u JOIN session_record sr ON sr.user_id = u.id WHERE u.deleted_at IS NULL AND sr.deleted_at IS NULL ORDER BY sr.last_activity_at DESC LIMIT 10;"),
    ("Admin-A5: credential verification state per seeded candidate user (sample)",
     "SELECT u.id, u.email, cv.credential_type_code, cv.credential_status_code, cv.verified_at, cv.last_used_at, cv.failure_count, cv.locked_until FROM users u JOIN credential_verification cv ON cv.user_id = u.id WHERE u.actor_type_code = 'candidate' AND u.deleted_at IS NULL ORDER BY cv.credential_type_code LIMIT 8;"),
    ("Admin-A6: credential recovery requests (sample)",
     "SELECT u.id, u.email, cr.recovery_type_code, cr.requested_at, cr.used_at, cr.status_code FROM users u JOIN credential_recovery cr ON cr.user_id = u.id WHERE u.deleted_at IS NULL ORDER BY cr.requested_at DESC LIMIT 8;"),
    ("Admin-A7: consent records (sample)",
     "SELECT u.id, u.email, cr.consent_type_code, cr.consent_value_code, cr.recorded_at FROM users u JOIN consent_record cr ON cr.user_id = u.id WHERE u.deleted_at IS NULL ORDER BY cr.recorded_at DESC LIMIT 8;"),
    ("Admin-A8: audit events (sample with actor role)",
     "SELECT a.id, a.actor_user_id, a.event_type_code, a.target_table, a.target_id, u.email AS actor_email, a.occurred_at FROM audit_event a LEFT JOIN users u ON u.id = a.actor_user_id ORDER BY a.occurred_at DESC LIMIT 10;"),
    ("Admin-A9: blocking list (active entries)",
     "SELECT b.id, b.blocker_user_id, b.blocked_party_type_code, b.blocked_party_id, b.blocked_at, b.is_active FROM blocking_list b LEFT JOIN users rp ON rp.id = b.blocker_user_id WHERE b.is_active = true AND b.deleted_at IS NULL ORDER BY b.blocked_at DESC LIMIT 10;"),
])
write_section(p_b67, "## Organisation module", [
    ("Org-A10: tenant accounts",
     "SELECT id, account_type_code, name, status_code, is_active, created_at FROM tenant_account ORDER BY created_at DESC;"),
    ("Org-A11: employer organisations (sample) with verification status",
     "SELECT eo.id, eo.company_name, eo.legal_name, eo.industry_name, eo.type_code, eo.is_verified, eo.verification_status_code, eo.mapped_recruiter_count, eo.city, eo.state, eo.country, eo.created_at FROM employer_organisation eo WHERE eo.deleted_at IS NULL ORDER BY eo.company_name LIMIT 10;"),
    ("Org-A12: company locations per employer (sample)",
     "SELECT eo.company_name, cl.id, cl.location_name, cl.city, cl.country, cl.is_head_office, cl.is_active FROM employer_organisation eo JOIN company_location cl ON cl.employer_organisation_id = eo.id AND cl.deleted_at IS NULL WHERE eo.deleted_at IS NULL ORDER BY eo.company_name, cl.id LIMIT 15;"),
    ("Org-A13: tax registration identifiers (sample)",
     "SELECT eo.company_name, tri.id, tri.country_code, tri.identifier_type_code, tri.identifier_value, tri.is_primary, tri.verification_status_code, tri.valid_from, tri.valid_to FROM employer_organisation eo JOIN tax_registration_identifier tri ON tri.employer_organisation_id = eo.id AND tri.deleted_at IS NULL WHERE eo.deleted_at IS NULL ORDER BY eo.company_name LIMIT 10;"),
    ("Org-A14: verification status records (sample)",
     "SELECT eo.company_name, vsr.verification_type_code, vsr.verification_status_code, vsr.verified_at, vsr.outcome_notes FROM employer_organisation eo JOIN verification_status_record vsr ON vsr.employer_organisation_id = eo.id AND vsr.deleted_at IS NULL WHERE eo.deleted_at IS NULL ORDER BY vsr.verified_at DESC LIMIT 10;"),
    ("Org-A15: recruiter mappings (effective-dated) sample",
     "SELECT eo.company_name, u.first_name, u.last_name, rm.mapping_type_code, rm.is_primary, rm.is_active, rm.effective_start, rm.effective_end FROM recruiter_mapping rm JOIN employer_organisation eo ON eo.id = rm.employer_organisation_id AND eo.deleted_at IS NULL JOIN users u ON u.id = rm.recruiter_user_id AND u.deleted_at IS NULL WHERE rm.deleted_at IS NULL ORDER BY eo.company_name, rm.is_primary DESC LIMIT 10;"),
    ("Org-A16: organisation hierarchy (active)",
     "SELECT eo_parent.company_name AS parent, eo_child.company_name AS child, oh.relationship_type_code, oh.effective_start, oh.effective_end, oh.is_active FROM organisation_hierarchy oh JOIN employer_organisation eo_parent ON eo_parent.id = oh.parent_organisation_id JOIN employer_organisation eo_child ON eo_child.id = oh.child_organisation_id WHERE oh.is_active = true AND oh.deleted_at IS NULL LIMIT 10;"),
    ("Org-A17: account administrators (sample)",
     "SELECT a.id, u.email, u.first_name, u.last_name, ta.name AS tenant_name, a.admin_role_code, a.is_primary, a.is_active FROM account_administrator a JOIN tenant_account ta ON ta.id = a.tenant_account_id JOIN users u ON u.id = a.administrator_user_id AND u.deleted_at IS NULL ORDER BY a.id LIMIT 10;"),
])
write_section(p_b67, "## Gig marketplace module", [
    ("Gig-A18: gig requests with job requirement title and pricing",
     "SELECT jr.title, grd.id, grd.pricing_model_code, grd.fixed_price, grd.fixed_price_currency_code, grd.rate_per_time_unit, grd.rate_time_unit_code, grd.fulfillment_status_code, grd.window_start_at, grd.window_end_at, grd.apply_by_at FROM gig_request_detail grd JOIN job_requirement jr ON jr.id = grd.job_requirement_id AND jr.deleted_at IS NULL ORDER BY grd.created_at DESC LIMIT 12;"),
    ("Gig-A19: gig worker profiles with availability (sample)",
     "SELECT gwp.id, gwp.worker_name, gwp.headline, gwp.service_offerings, gwp.charge_rate_min, gwp.charge_currency_code, gwp.status_code, gwp.is_available, gwa.availability_start_at, gwa.availability_end_at, gwa.is_recurring FROM gig_worker_profile gwp LEFT JOIN gig_worker_availability gwa ON gwa.gig_worker_profile_id = gwp.id AND gwa.is_active = true AND gwa.deleted_at IS NULL WHERE gwp.deleted_at IS NULL ORDER BY case when gwp.is_available then 0 else 1 end, gwp.created_at DESC LIMIT 10;"),
    ("Gig-A20: gig applications for a gig request detail (sample)",
     "SELECT gwd.job_requirement_id, jr.title AS job_title, ga.id AS gig_application_id, gwp.worker_name, ga.bid_amount, ga.bid_currency_code, ga.application_status_code, ga.applied_at, ga.reviewed_at, ga.rejection_reason FROM gig_application ga JOIN gig_request_detail gwd ON gwd.id = ga.gig_request_detail_id JOIN job_requirement jr ON jr.id = gwd.job_requirement_id AND jr.deleted_at IS NULL JOIN gig_worker_profile gwp ON gwp.id = ga.gig_worker_profile_id AND gwp.deleted_at IS NULL WHERE ga.deleted_at IS NULL ORDER BY ga.applied_at DESC LIMIT 10;"),
    ("Gig-A21: gig assignments with handoffs and earnings",
     "SELECT ga.gig_application_id, gwd.job_requirement_id, jr.title, gwp.worker_name, gaz.id AS assignment_id, gaz.assigned_at, gaz.assignment_status_code, ghr.handoff_system_code, ghr.external_reference, ghr.handoff_status_code, ger.earnings_type_code, ger.earnings_amount, ger.earnings_currency_code FROM gig_assignment gaz JOIN gig_application ga ON ga.id = gaz.gig_application_id AND ga.deleted_at IS NULL JOIN gig_request_detail gwd ON gwd.id = ga.gig_request_detail_id JOIN job_requirement jr ON jr.id = gwd.job_requirement_id AND jr.deleted_at IS NULL JOIN gig_worker_profile gwp ON gwp.id = ga.gig_worker_profile_id AND gwp.deleted_at IS NULL LEFT JOIN gig_handoff_reference ghr ON ghr.gig_assignment_id = gaz.id LEFT JOIN gig_earnings_reference ger ON ger.gig_assignment_id = gaz.id WHERE gaz.deleted_at IS NULL LIMIT 8;"),
    ("Gig-A22: gig ratings (sample)",
     "SELECT gwp.worker_name, gaz.assignment_id, gr.id, gr.rating_by_user_id, gr.rating_value, gr.rating_text, gr.rated_at FROM gig_rating gr JOIN gig_assignment gaz ON gaz.id = gr.gig_assignment_id AND gaz.deleted_at IS NULL JOIN gig_application ga ON ga.id = gaz.gig_application_id AND ga.deleted_at IS NULL JOIN gig_worker_profile gwp ON gwp.id = ga.gig_worker_profile_id AND gwp.deleted_at IS NULL ORDER BY gr.rated_at DESC LIMIT 8;"),
    ("Gig-A23: gig favourites / blacklist (sample)",
     "SELECT 'favourite' AS type, gf.id, gf.requester_user_id, gwp.worker_name, gf.favourited_at FROM gig_favourite gf JOIN gig_worker_profile gwp ON gwp.id = gf.gig_worker_profile_id AND gwp.deleted_at IS NULL UNION ALL SELECT 'blacklist', gb.id, gb.requester_user_id, gwp.worker_name, gb.blacklisted_at FROM gig_blacklist gb JOIN gig_worker_profile gwp ON gwp.id = gb.gig_worker_profile_id AND gwp.deleted_at IS NULL ORDER BY type, id LIMIT 10;"),
])

# ---------------------------------------------------------------- B68
p_b68 = init_report("B68_member_B_Licences_Sourcing_Subs.txt")
write_section(p_b68, "## Licences module", [
    ("Lic-B1: subscription licences with tenant",
     "SELECT sl.id, sl.licence_number, sl.licence_type_code, sl.status_code, ta.name AS tenant_name, sl.max_users_allowed, sl.max_devices_per_user, sl.issued_at, sl.activated_at, sl.suspended_at, sl.terminated_at FROM subscription_licence sl JOIN tenant_account ta ON ta.id = sl.tenant_account_id ORDER BY sl.created_at;"),
    ("Lic-B2: seat allocations against a licence (sample)",
     "SELECT sl.licence_number, sa.id, u.email, u.first_name, u.last_name, sa.seat_status_code, sa.allocated_at, sa.revoked_at, sa.is_active FROM seat_allocation sa JOIN subscription_licence sl ON sl.id = sa.subscription_licence_id JOIN users u ON u.id = sa.user_id AND u.deleted_at IS NULL WHERE sa.deleted_at IS NULL ORDER BY sl.id, sa.allocated_at LIMIT 15;"),
    ("Lic-B3: device registrations per user (sample)",
     "SELECT u.id, u.email, u.first_name, dr.id AS device_id, dr.device_identifier, dr.device_type_code, dr.last_seen_at, dr.revoked_at, dr.is_active FROM device_registration dr JOIN users u ON u.id = dr.user_id AND u.deleted_at IS NULL WHERE dr.deleted_at IS NULL ORDER BY u.id LIMIT 10;"),
    ("Lic-B4: device sessions (active) per user (sample)",
     "SELECT u.id, u.email, ds.id AS session_id, ds.session_token_ref, ds.started_at, ds.expires_at, ds.is_revoked, dr.device_identifier FROM device_session ds JOIN users u ON u.id = ds.user_id AND u.deleted_at IS NULL JOIN device_registration dr ON dr.id = ds.device_registration_id AND dr.deleted_at IS NULL WHERE ds.deleted_at IS NULL AND ds.expires_at > now() AND ds.is_revoked = false ORDER BY ds.started_at DESC LIMIT 10;"),
    ("Lic-B5: session revocation events (sample)",
     "SELECT sre.id, sre.revoked_by_user_id, sre.revocation_target_type_code, sre.revocation_target_id, u.email AS revoked_by_email, sre.revoked_at, sre.revocation_reason_code FROM session_revocation_event sre LEFT JOIN users u ON u.id = sre.revoked_by_user_id ORDER BY sre.revoked_at DESC LIMIT 8;"),
])
write_section(p_b68, "## Sourcing module", [
    ("Src-B6: sourcing requests with job requirement and consultant",
     "SELECT sr.id, jr.title AS job_title, sr.requester_user_id, u.first_name, u.last_name AS requester, sr.consultant_user_id, uc.first_name AS consultant_first, uc.last_name AS consultant_last, sr.request_type_code, sr.description, sr.status_code, sr.is_open_to_consultants, sr.shortlist_id, sr.created_at FROM sourcing_request sr JOIN job_requirement jr ON jr.id = sr.job_requirement_id AND jr.deleted_at IS NULL LEFT JOIN users u ON u.id = sr.requester_user_id AND u.deleted_at IS NULL LEFT JOIN users uc ON uc.id = sr.consultant_user_id AND uc.deleted_at IS NULL WHERE sr.deleted_at IS NULL ORDER BY sr.created_at DESC LIMIT 15;"),
    ("Src-B7: consultant decisions for open requirements (sample)",
     "SELECT sr.id AS sourcing_id, jr.title, cd.id AS decision_id, cd.decision_code, cd.decision_note, cd.decided_at, uc.first_name || ' ' || uc.last_name AS consultant FROM consultant_decision cd JOIN sourcing_request sr ON sr.id = cd.sourcing_request_id AND sr.deleted_at IS NULL JOIN job_requirement jr ON jr.id = sr.job_requirement_id AND jr.deleted_at IS NULL JOIN users uc ON uc.id = cd.consultant_user_id AND uc.deleted_at IS NULL WHERE cd.deleted_at IS NULL ORDER BY cd.decided_at DESC LIMIT 10;"),
    ("Src-B8: sourcing shortlists (recipient sample)",
     "SELECT sr.id AS sourcing_id, jr.title, ss.id AS shortlist_id, oct.id AS candidate_id, ci.first_name, ci.last_name, oct.created_at AS shortlist_entry_at FROM sourcing_shortlist ss JOIN sourcing_request sr ON sr.id = ss.sourcing_request_id AND sr.deleted_at IS NULL JOIN job_requirement jr ON jr.id = sr.job_requirement_id AND jr.deleted_at IS NULL LEFT JOIN organisation_candidate_tracking oct ON oct.shortlist_id = ss.id LEFT JOIN candidate_identity ci ON ci.id = oct.candidate_id WHERE ss.deleted_at IS NULL LIMIT 10;"),
    ("Src-B9: outreach batches and recipients",
     "SELECT ob.id, ob.name, ob.batch_type_code, ob.channel_code, ob.status_code, ob.scheduled_at, ob.started_at, ob.completed_at, ob.total_recipients, ob.delivered_recipients, ob.failed_recipients FROM outreach_batch ob WHERE ob.deleted_at IS NULL ORDER BY ob.created_at DESC;"),
    ("Src-B10: outreach batch recipients (sample)",
     "SELECT ob.name AS batch_name, obr.id, ci.first_name, ci.last_name, obr.contact_channel_code, obr.delivery_status_code, obr.delivered_at FROM outreach_batch ob JOIN outreach_batch_recipient obr ON obr.outreach_batch_id = ob.id LEFT JOIN candidate_identity ci ON ci.id = obr.candidate_identity_id WHERE ob.deleted_at IS NULL AND obr.deleted_at IS NULL ORDER BY obr.delivery_status_code LIMIT 12;"),
])
write_section(p_b68, "## Subscriptions module", [
    ("Sub-B11: subscription plans",
     "SELECT id, plan_code, name, category_code, billing_period_code, price_amount, price_currency_code, renewal_type_code, trial_days, is_active FROM subscription_plan ORDER BY price_amount;"),
    ("Sub-B12: plan entitlements per plan",
     "SELECT sp.plan_code, sp.name, pe.id, pe.entitlement_code, pe.entitlement_value, pe.value_unit_code, pe.is_active FROM plan_entitlement pe JOIN subscription_plan sp ON sp.id = pe.subscription_plan_id AND sp.deleted_at IS NULL WHERE pe.deleted_at IS NULL ORDER BY sp.plan_code, pe.entitlement_code;"),
    ("Sub-B13: tenant subscription periods",
     "SELECT ta.name AS tenant_name, sl.licence_number, sp.id AS period_id, sp.status_code, sp.started_at, sp.ended_at, sp.renew_type_code, sp.cancelled_at, sp.cancellation_reason FROM subscription_period sp JOIN subscription_licence sl ON sl.id = sp.subscription_licence_id JOIN tenant_account ta ON ta.id = sl.tenant_account_id WHERE sp.deleted_at IS NULL ORDER BY sp.started_at DESC;"),
    ("Sub-B14: wallet account and ledger for a tenant",
     "SELECT wa.id, wa.currency_code, wa.balance, wa.status_code, ta.name AS tenant_name, u.email AS owner_email FROM wallet_account wa JOIN tenant_account ta ON ta.id = wa.tenant_account_id LEFT JOIN users u ON u.id = wa.owner_user_id AND u.deleted_at IS NULL WHERE wa.deleted_at IS NULL ORDER BY wa.created_at;"),
    ("Sub-B15: wallet ledger entries (append-only)",
     "SELECT wl.id, wl.created_at, wl.transaction_type_code, wl.amount, wl.currency_code, wl.balance_after, wl.reference_type_code, wl.reference_id, wl.correction_reference_id, wl.description, wl.created_by_user_id FROM wallet_ledger_entry wl WHERE wl.wallet_account_id = (SELECT id FROM wallet_account LIMIT 1) ORDER BY wl.created_at;"),
    ("Sub-B16: payment orders with status history",
     "SELECT po.id, po.order_number, po.payment_method_code, po.status_code, po.amount, po.currency_code, po.gateway_reference, po.initiated_at, po.completed_at, po.failed_at FROM payment_order po WHERE po.deleted_at IS NULL ORDER BY po.initiated_at;"),
    ("Sub-B17: payment status history for an order",
     "SELECT ph.id, po.id AS order_id, po.order_number, ph.status_code, ph.changed_at, ph.changed_by_user_id, ph.gateway_status FROM payment_status_history ph JOIN payment_order po ON po.id = ph.payment_order_id AND po.deleted_at IS NULL WHERE ph.deleted_at IS NULL ORDER BY ph.changed_at;"),
    ("Sub-B18: invoices for payment orders",
     "SELECT i.id, i.invoice_number, po.id AS payment_order_id, po.order_number, i.issue_date, i.due_date, i.total_amount, i.currency_code, i.status_code, i.issued_at, i.paid_at FROM invoice i JOIN payment_order po ON po.id = i.payment_order_id AND po.deleted_at IS NULL WHERE i.deleted_at IS NULL ORDER BY i.issue_date;"),
    ("Sub-B19: refunds (sample)",
     "SELECT r.id, r.refund_number, r.payment_order_id, po.order_number, r.invoice_id, r.refund_amount, r.currency_code, r.refund_status_code, r.refund_type_code, r.requested_at, r.processed_at, r.gateway_reference FROM refund r JOIN payment_order po ON po.id = r.payment_order_id AND po.deleted_at IS NULL WHERE r.deleted_at IS NULL ORDER BY r.requested_at;"),
    ("Sub-B20: profile download history (append-only)",
     "SELECT pdh.id, pdh.downloader_user_id, u.email AS downloader_email, ci.id AS candidate_id, u2.email AS candidate_email, pdh.downloaded_at, pdh.download_format_code, pdh.credit_deducted_amount, pdh.credit_currency_code, pdh.credit_deduction_applied, pdh.download_reference FROM profile_download_history pdh JOIN users u ON u.id = pdh.downloader_user_id AND u.deleted_at IS NULL JOIN candidate_identity ci ON ci.id = pdh.candidate_identity_id AND ci.deleted_at IS NULL LEFT JOIN users u2 ON u2.id = ci.user_id AND u2.deleted_at IS NULL WHERE pdh.deleted_at IS NULL ORDER BY pdh.downloaded_at DESC LIMIT 12;"),
])

# ---------------------------------------------------------------- B69
p_b69 = init_report("B69_member_C_Notifications_Analytics_Shared.txt")
write_section(p_b69, "## Notifications module", [
    ("Not-C1: notification preferences by channel and event type (sample)",
     "SELECT u.id, u.email, u.first_name, np.channel_code, np.notification_type_code, np.is_enabled FROM notification_preference np JOIN users u ON u.id = np.user_id AND u.deleted_at IS NULL WHERE np.deleted_at IS NULL ORDER BY u.id, np.channel_code, np.notification_type_code LIMIT 15;"),
    ("Not-C2: job alert preferences (sample)",
     "SELECT u.id, u.email, u.first_name, jal.alert_name, jal.criteria, jal.frequency_code, jal.delivery_channel_codes, jal.is_active FROM job_alert_preference jal JOIN users u ON u.id = jal.user_id AND u.deleted_at IS NULL WHERE jal.deleted_at IS NULL ORDER BY jal.created_at DESC LIMIT 10;"),
    ("Not-C3: multilingual preferences and privacy settings (sample)",
     "SELECT u.id, u.email, u.first_name, lp.ui_language_code, lp.content_language_code, ps.setting_key, ps.setting_value, ps.setting_type_code, ps.is_active FROM users u JOIN language_preference lp ON lp.user_id = u.id AND lp.is_active = true AND lp.deleted_at IS NULL JOIN privacy_setting ps ON ps.user_id = u.id AND ps.is_active = true AND ps.deleted_at IS NULL WHERE u.deleted_at IS NULL ORDER BY u.id LIMIT 10;"),
    ("Not-C4: community posts with reactions (sample)",
     "SELECT cp.id, cp.author_user_id, u.first_name || ' ' || u.last_name AS author, cp.community_type_code, cp.title, cp.language_code, cp.visibility_code, cp.is_pinned, cp.is_published, cp.created_at, count(cpr.id) AS reaction_count FROM community_post cp LEFT JOIN users u ON u.id = cp.author_user_id AND u.deleted_at IS NULL LEFT JOIN community_post_reaction cpr ON cpr.community_post_id = cp.id AND cpr.deleted_at IS NULL WHERE cp.deleted_at IS NULL AND cp.is_published = true GROUP BY cp.id, cp.author_user_id, cp.community_type_code, cp.title, cp.language_code, cp.visibility_code, cp.is_pinned, cp.is_published, cp.created_at ORDER BY cp.created_at DESC LIMIT 10;"),
    ("Not-C5: support ticket with replies (sample)",
     "SELECT st.id, st.reporter_user_id, u1.email AS reporter_email, st.assignee_user_id, u2.email AS assignee_email, st.category_code, st.priority_code, st.status_code, st.subject, st.language_code, st.created_at, count(str.id) AS reply_count FROM support_ticket st LEFT JOIN users u1 ON u1.id = st.reporter_user_id AND u1.deleted_at IS NULL LEFT JOIN users u2 ON u2.id = st.assignee_user_id AND u2.deleted_at IS NULL LEFT JOIN support_ticket_reply str ON str.support_ticket_id = st.id AND str.deleted_at IS NULL WHERE st.deleted_at IS NULL GROUP BY st.id, st.reporter_user_id, u1.email, st.assignee_user_id, u2.email, st.category_code, st.priority_code, st.status_code, st.subject, st.language_code, st.created_at ORDER BY st.created_at DESC LIMIT 8;"),
    ("Not-C6: FAQ by category and language (sample)",
     "SELECT f.id, f.category_code, f.question, f.answer, f.language_code, f.sort_order, f.is_published, f.view_count FROM faq f WHERE f.deleted_at IS NULL AND f.is_published = true ORDER BY f.category_code, f.sort_order LIMIT 10;"),
])
write_section(p_b69, "## Analytics module", [
    ("Ana-C7: analytics dimensions — date dim (current flag)",
     "SELECT id, date_key, day_of_week, day_of_month, month_name, quarter, year, is_current FROM analytics_dim_date WHERE is_current = true LIMIT 5;"),
    ("Ana-C8: analytics fact — application pipeline funnel by stage (grouped)",
     "SELECT pipeline_stage_code, count(*) AS applications, count(DISTINCT application_id) AS distinct_applications, count(DISTINCT candidate_identity_id) AS candidates_touched FROM analytics_fact_application_pipeline WHERE date_key >= date_trunc('month', current_date) - interval '1 month' GROUP BY pipeline_stage_code ORDER BY pipeline_stage_code;"),
    ("Ana-C9: analytics fact — source/channel attribution (top channels)",
     "SELECT source_channel_code, count(*) AS applications, count(DISTINCT candidate_identity_id) AS candidates, count(DISTINCT employer_organisation_id) AS employers FROM analytics_fact_source_channel WHERE date_key >= date_trunc('month', current_date) - interval '1 month' GROUP BY source_channel_code ORDER BY applications DESC LIMIT 10;"),
    ("Ana-C10: analytics fact — time-to-hire summary (outcome distribution)",
     "SELECT outcome_code, count(*) AS applications, avg(days_to_outcome) AS avg_days_to_outcome, min(days_to_outcome) AS min_days, max(days_to_outcome) AS max_days FROM analytics_fact_time_to_hire WHERE date_key >= date_trunc('month', current_date) - interval '1 month' GROUP BY outcome_code ORDER BY outcome_code;"),
    ("Ana-C11: analytics fact — gig marketplace summary by pipeline stage",
     "SELECT pipeline_stage_code, count(*) AS records, count(DISTINCT gig_request_detail_id) AS requests, count(DISTINCT gig_worker_profile_id) AS workers, count(DISTINCT assignment_id) AS assignments, sum(earnings_amount) AS total_earnings FROM analytics_fact_gig_marketplace WHERE date_key >= date_trunc('month', current_date) - interval '1 month' GROUP BY pipeline_stage_code ORDER BY pipeline_stage_code;"),
    ("Ana-C12: analytics fact — candidate activity summary (top candidates by actions)",
     "SELECT candidate_identity_id, applications_sent_count, profile_views_count, searches_count, (applications_sent_count + profile_views_count + searches_count) AS total_actions FROM analytics_fact_candidate_activity WHERE activity_date_key >= date_trunc('month', current_date) - interval '1 month' ORDER BY total_actions DESC LIMIT 10;"),
    ("Ana-C13: analytics fact — employer activity summary (top employers by posts)",
     "SELECT employer_organisation_id, job_posts_count, applications_received_count, shortlisted_count, interviewed_count, offered_count, joined_count, rejected_count FROM analytics_fact_employer_activity WHERE activity_date_key >= date_trunc('month', current_date) - interval '1 month' ORDER BY job_posts_count DESC LIMIT 10;"),
])
write_section(p_b69, "## Shared team items module", [
    ("Shd-C14: notification deliveries (status distribution)",
     "SELECT delivery_status_code, count(*) AS deliveries, count(DISTINCT recipient_user_id) AS recipients FROM notification_delivery WHERE deleted_at IS NULL GROUP BY delivery_status_code ORDER BY deliveries DESC;"),
    ("Shd-C15: credential verification records (sample)",
     "SELECT u.id, u.email, cv.credential_type_code, cv.credential_status_code, cv.verified_at, cv.last_used_at, cv.failure_count, cv.locked_until FROM credential_verification cv JOIN users u ON u.id = cv.user_id AND u.deleted_at IS NULL WHERE cv.deleted_at IS NULL ORDER BY cv.credential_type_code, cv.verified_at DESC LIMIT 10;"),
    ("Shd-C16: credential recovery records (sample)",
     "SELECT u.id, u.email, cr.recovery_type_code, cr.requested_at, cr.used_at, cr.status_code, cr.token_ref FROM credential_recovery cr JOIN users u ON u.id = cr.user_id AND u.deleted_at IS NULL WHERE cr.deleted_at IS NULL ORDER BY cr.requested_at DESC LIMIT 8;"),
    ("Shd-C17: consent records (sample)",
     "SELECT u.id, u.email, cr.consent_type_code, cr.consent_value_code, cr.recorded_at, cr.ip_address FROM consent_record cr JOIN users u ON u.id = cr.user_id AND u.deleted_at IS NULL WHERE cr.deleted_at IS NULL ORDER BY cr.recorded_at DESC LIMIT 8;"),
    ("Shd-C18: audit events (sample)",
     "SELECT a.id, a.actor_user_id, a.event_type_code, a.target_table, a.target_id, u.email AS actor_email, a.occurred_at, a.source_ip FROM audit_event a LEFT JOIN users u ON u.id = a.actor_user_id ORDER BY a.occurred_at DESC LIMIT 8;"),
    ("Shd-C19: blocking list (active)",
     "SELECT b.id, b.blocker_user_id, u1.email AS blocker_email, b.blocked_party_type_code, b.blocked_party_id, b.blocked_at, b.is_active, b.reason FROM blocking_list b LEFT JOIN users u1 ON u1.id = b.blocker_user_id WHERE b.is_active = true AND b.deleted_at IS NULL ORDER BY b.blocked_at DESC LIMIT 8;"),
    ("Shd-C20: analytics — source-channel fact rows (sample)",
     "SELECT af.id, af.application_id, af.candidate_identity_id, af.job_requirement_id, af.employer_organisation_id, af.source_channel_code, af.applied_at, af.date_key FROM analytics_fact_source_channel af WHERE af.deleted_at IS NULL ORDER BY af.applied_at DESC LIMIT 8;"),
])

print("B67:", os.path.getsize(p_b67), "bytes")
print("B68:", os.path.getsize(p_b68), "bytes")
print("B69:", os.path.getsize(p_b69), "bytes")
