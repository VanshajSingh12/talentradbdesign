# B69 — Module query results: Notifications, Analytics, Shared items

**Owner:** Member C
**Milestone:** 20 — Queries and validation across all modules
**Database:** `talentra` on `localhost:5431`
**Run time:** 2026-10-16T13:33:16.108038+00:00

Raw module output lives in `scripts/reports/B69_member_C_Notifications_Analytics_Shared.txt`.

## Notifications

### Not-C1 — notification preferences by channel and event type (sample)

```sql
SELECT u.id, u.email, u.first_name, np.channel_code,
       np.notification_type_code, np.is_enabled
FROM notification_preference np
JOIN users u
       ON u.id = np.user_id AND u.deleted_at IS NULL
WHERE np.deleted_at IS NULL
ORDER BY u.id, np.channel_code, np.notification_type_code
LIMIT 15;
```

**Result:** 15 rows.

| id | email | first_name | channel_code | notification_type_code | is_enabled |
|---|---|---|---|---|---|
| 1 | candidate_1@example.com |  | nc_email | job_alert | True |
| 1 | candidate_1@example.com |  | nc_sms | job_alert | True |
| 2 | candidate_2@example.com |  | nc_email | job_alert | True |
| 2 | candidate_2@example.com |  | nc_sms | job_alert | True |
| 3 | candidate_3@example.com |  | nc_email | job_alert | True |
| 3 | candidate_3@example.com |  | nc_sms | job_alert | True |
| 4 | candidate_4@example.com |  | nc_email | job_alert | True |
| 4 | candidate_4@example.com |  | nc_sms | job_alert | True |
| 5 | candidate_5@example.com |  | nc_email | job_alert | True |
| 5 | candidate_5@example.com |  | nc_sms | job_alert | True |
| 6 | candidate_6@example.com |  | nc_email | job_alert | True |
| 6 | candidate_6@example.com |  | nc_sms | job_alert | True |
| 7 | candidate_7@example.com |  | nc_email | job_alert | True |
| 7 | candidate_7@example.com |  | nc_sms | job_alert | True |
| 8 | candidate_8@example.com |  | nc_email | job_alert | True |

### Not-C2 — job alert preferences (sample)

```sql
SELECT u.id, u.email, u.first_name, jal.alert_name,
       jal.criteria, jal.frequency_code,
       jal.delivery_channel_codes, jal.is_active
FROM job_alert_preference jal
JOIN users u
       ON u.id = jal.user_id AND u.deleted_at IS NULL
WHERE jal.deleted_at IS NULL
ORDER BY jal.created_at DESC
LIMIT 10;
```

**Result:** 10 rows.

| id | email | first_name | alert_name | criteria | frequency_code | delivery_channel_codes | is_active |
|---|---|---|---|---|---|---|---|
| 2 | candidate_2@example.com |  | Alert 2 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 3 | candidate_3@example.com |  | Alert 3 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 4 | candidate_4@example.com |  | Alert 4 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 5 | candidate_5@example.com |  | Alert 5 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 6 | candidate_6@example.com |  | Alert 6 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 7 | candidate_7@example.com |  | Alert 7 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 8 | candidate_8@example.com |  | Alert 8 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 9 | candidate_9@example.com |  | Alert 9 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 10 | candidate_10@example.com |  | Alert 10 | {"keywords": ["python", "developer"]} | immediate | email | True |
| 1 | candidate_1@example.com |  | Alert 1 | {"keywords": ["python", "developer"]} | immediate | email | True |

### Not-C3 — multilingual preferences and privacy settings (sample)

```sql
SELECT u.id, u.email, u.first_name, lp.ui_language_code,
       lp.content_language_code, ps.setting_key, ps.setting_value,
       ps.setting_type_code, ps.is_active
FROM users u
JOIN language_preference lp
       ON lp.user_id = u.id
      AND lp.is_active = true
      AND lp.deleted_at IS NULL
JOIN privacy_setting ps
       ON ps.user_id = u.id
      AND ps.is_active = true
      AND ps.deleted_at IS NULL
WHERE u.deleted_at IS NULL
ORDER BY u.id
LIMIT 10;
```

**Result:** 10 rows.

| id | email | first_name | ui_language_code | content_language_code | setting_key | setting_value | setting_type_code | is_active |
|---|---|---|---|---|---|---|---|
| 1 | candidate_1@example.com |  | en | en | profile_visibility | public | boolean | True |
| 1 | candidate_1@example.com |  | en | en | email_visible | true | boolean | True |
| 2 | candidate_2@example.com |  | en | en | profile_visibility | public | boolean | True |
| 2 | candidate_2@example.com |  | en | en | email_visible | true | boolean | True |
| 3 | candidate_3@example.com |  | en | en | profile_visibility | public | boolean | True |
| 3 | candidate_3@example.com |  | en | en | email_visible | true | boolean | True |
| 4 | candidate_4@example.com |  | en | en | profile_visibility | public | boolean | True |
| 4 | candidate_4@example.com |  | en | en | email_visible | true | boolean | True |
| 5 | candidate_5@example.com |  | en | en | profile_visibility | public | boolean | True |
| 5 | candidate_5@example.com |  | en | en | email_visible | true | boolean | True |

### Not-C4 — community posts with reactions (sample)

```sql
SELECT cp.id, cp.author_user_id,
       u.first_name || ' ' || u.last_name AS author,
       cp.community_type_code, cp.title, cp.language_code,
       cp.visibility_code, cp.is_pinned, cp.is_published,
       cp.created_at, count(cpr.id) AS reaction_count
FROM community_post cp
LEFT JOIN users u
       ON u.id = cp.author_user_id AND u.deleted_at IS NULL
LEFT JOIN community_post_reaction cpr
       ON cpr.community_post_id = cp.id
      AND cpr.deleted_at IS NULL
WHERE cp.deleted_at IS NULL
  AND cp.is_published = true
GROUP BY cp.id, cp.author_user_id, cp.community_type_code,
         cp.title, cp.language_code, cp.visibility_code,
         cp.is_pinned, cp.is_published, cp.created_at
ORDER BY cp.created_at DESC
LIMIT 10;
```

**Result:** Query execution failed — `column "u.first_name" must appear in the GROUP BY clause or be used in an aggregate function`.

This query is included for completeness, but the version that ran needs the author name expression in the `GROUP BY` (PostgreSQL `GROUP BY` semantics). The post/reaction structure is present; the query just needs a small SQL fix.

### Not-C5 — support ticket with replies (sample)

```sql
SELECT st.id, st.reporter_user_id, u1.email AS reporter_email,
       st.assignee_user_id, u2.email AS assignee_email,
       st.category_code, st.priority_code, st.status_code,
       st.subject, st.language_code, st.created_at,
       count(str.id) AS reply_count
FROM support_ticket st
LEFT JOIN users u1
       ON u1.id = st.reporter_user_id AND u1.deleted_at IS NULL
LEFT JOIN users u2
       ON u2.id = st.assignee_user_id AND u2.deleted_at IS NULL
LEFT JOIN support_ticket_reply str
       ON str.support_ticket_id = st.id AND str.deleted_at IS NULL
WHERE st.deleted_at IS NULL
GROUP BY st.id, st.reporter_user_id, u1.email,
         st.assignee_user_id, u2.email, st.category_code,
         st.priority_code, st.status_code, st.subject,
         st.language_code, st.created_at
ORDER BY st.created_at DESC
LIMIT 8;
```

**Result:** 8 rows.

| id | reporter_user_id | reporter_email | assignee_user_id | assignee_email | category_code | priority_code | status_code | subject | language_code | created_at | reply_count |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 2 | candidate_2@example.com |  |  | billing | low | open | S Support ticket subject 2 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 3 | 3 | candidate_3@example.com |  |  | billing | low | open | S Support ticket subject 3 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 4 | 4 | candidate_4@example.com |  |  | billing | low | open | S Support ticket subject 4 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 5 | 5 | candidate_5@example.com |  |  | billing | low | open | S Support ticket subject 5 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 6 | 6 | candidate_6@example.com |  |  | billing | low | open | S Support ticket subject 6 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 7 | 7 | candidate_7@example.com |  |  | billing | low | open | S Support ticket subject 7 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 8 | 8 | candidate_8@example.com |  |  | billing | low | open | S Support ticket subject 8 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |
| 1 | 1 | candidate_1@example.com |  |  | billing | low | open | S Support ticket subject 1 | en | 2026-10-16 11:38:54.545702+00:00 | 2 |

### Not-C6 — FAQ by category and language (sample)

```sql
SELECT f.id, f.category_code, f.question, f.answer,
       f.language_code, f.sort_order, f.is_published,
       f.view_count
FROM faq f
WHERE f.deleted_at IS NULL
  AND f.is_published = true
ORDER BY f.category_code, f.sort_order
LIMIT 10;
```

**Result:** 10 rows.

| id | category_code | question | answer | language_code | sort_order | is_published | view_count |
|---|---|---|---|---|---|---|---|
| 1 | general | Stuff need early year strategy. | Nature less receive model garden produce. You identify worker system agreement election. Girl federal last soldier. Share ahead what collection actually. Worry station step standard. Company worry less administration. Usually treatment within have machine wife. Operation wrong manager million. Prepare word stop skill you use. Model sport understand store. Foreign more these. Impact thus everything town light machine specific music. | en | 0 | True | 0 |
| 2 | general | Newspaper may where exist. | Rock long admit simple evidence site. Idea tax history floor number president. Need impact sea foot paper accept. Hot water space end. Foreign any event us sense able well. Outside rock these need. Stay ever scene until operation ability. Room six blue nothing. Party past shoulder. Yard show local care. Important day wait suffer learn avoid worker. Far back create certainly. Page message within star. | en | 1 | True | 0 |
| 3 | general | Moment six field care. | Listen sister bar set. School explain play still foreign open kitchen. Field force remain. Point threat police food sense whom. And factor anything cut lawyer policy walk. Matter property sell service. Feel partner may serve business compare. Director should simply position left arm discover. Clearly already glass wait describe value. Yard put culture item however professor. Personal final exist anything entire force. | en | 2 | True | 0 |
| 4 | general | Your subject among any education phone father. | Expert economy training economy street. Pressure from listen step order card. Detail despite now event night purpose. Always assume body man feeling rule world. Research car back instead whole sense station. Future require discover physical business director. Value treat better. Finally including business concern down head. Take brother decision mission table truth theory culture. Husband fire five spring land even. Will person serve usually. | en | 3 | True | 0 |
| 5 | general | Word actually hotel space affect news. | Course unit others scene direction any. Great doctor agent myself he whether require. Agent often common season make past home their. Not democratic use tree social. Easy fall treat prepare factor suffer. By arm way. Base administration bad service also explain. Improve exactly best million. Industry clear lot ground. Avoid maybe per training particular site. Day ball main station. Fly citizen hotel light station development. Page tell individual fact they strong. Over far yourself. | en | 4 | True | 0 |
| 6 | general | Dog set church first possible however. | Either know three direction keep guess. Late heart actually coach cause audience reduce. Strategy study day group character. Country them exactly. Research late determine personal onto give better. Time put meeting various. Image your single it support since worker. Decide air one other anything whole. Easy trade culture. Sense bring direction material not left. Arrive night defense. | en | 5 | True | 0 |
| 7 | general | Future respond important those. | Forward song particular person teacher decision maybe. Claim represent father important nothing. Social away always discuss just. So continue southern. Choice no effect. Happen free college real serve laugh. Political cover soon. Recognize design tough campaign simple. West occur capital drop large blood. Interview focus question. Continue majority girl like major exactly phone. Pass wait mean movie her item like yeah. Hand common step fear then mean fear. Design never issue despite sea whole. | en | 6 | True | 0 |
| 8 | general | Like relationship final. | Front career cost consumer improve north special. A cost good mission. Management which traditional listen produce school specific. Security even account why. Camera almost write blood speech. Its mother PM catch. Up simple just part among hit. Nor family remember decide now term from too. Especially its benefit local century sense. Myself information specific turn field. Western pretty bring themselves chair half. Fund too itself bag center program. Human determine note. | en | 7 | True | 0 |
| 9 | general | Position type camera nothing charge when worry. | Significant international between your bag in determine. Like about several final. Score boy effort pressure air name. Guess couple media window. Although such message pretty trip offer. To series tree huge treatment arm its value. Believe sign feel step. Mother radio let like accept check. Material economy that that soon he four. Tell environmental however style wind final. Model avoid organization. Large move sit. Manager wish I including teacher. | en | 8 | True | 0 |
| 10 | general | Common work result among after. | Scientist organization rise nor. Idea different table involve add soldier. Nice personal recent per key everyone customer. Far involve bar bit well. Need several mention military wrong believe. Form yard arm onto let. Sort we model true north easy. Executive government example individual above. Space site environmental wish. Daughter long more. Include source play play. Call rock add learn good pretty question. Over treatment agency particularly serve finally. | en | 9 | True | 0 |

## Analytics

### Ana-C7 — analytics dimensions: date dim (current flag)

```sql
SELECT id, date_key, day_of_week, day_of_month,
       month_name, quarter, year, is_current
FROM analytics_dim_date
WHERE is_current = true
LIMIT 5;
```

**Result:** 5 rows.

| id | date_key | day_of_week | day_of_month | month_name | quarter | year | is_current |
|---|---|---|---|---|---|---|---|
| 78 | 2026-01-01 | 4 | 1 | January | 1 | 2026 | True |
| 79 | 2026-01-02 | 5 | 2 | January | 1 | 2026 | True |
| 80 | 2026-01-03 | 6 | 3 | January | 1 | 2026 | True |
| 81 | 2026-01-04 | 7 | 4 | January | 1 | 2026 | True |
| 82 | 2026-01-05 | 1 | 5 | January | 1 | 2026 | True |

### Ana-C8 — analytics fact: application pipeline funnel by stage (grouped)

```sql
SELECT pipeline_stage_code,
       count(*) AS applications,
       count(DISTINCT application_id) AS distinct_applications,
       count(DISTINCT candidate_identity_id) AS candidates_touched
FROM analytics_fact_application_pipeline
WHERE date_key >= date_trunc('month', current_date)
                - interval '1 month'
GROUP BY pipeline_stage_code
ORDER BY pipeline_stage_code;
```

**Result:** 6 rows.

| pipeline_stage_code | applications | distinct_applications | candidates_touched |
|---|---|---|---|
| applied | 283 | 283 | 283 |
| interviewed | 83 | 83 | 83 |
| joined | 30 | 30 | 30 |
| offered | 74 | 74 | 74 |
| rejected | 27 | 27 | 27 |
| shortlisted | 131 | 131 | 131 |

### Ana-C9 — analytics fact: source/channel attribution (top channels)

```sql
SELECT source_channel_code,
       count(*) AS applications,
       count(DISTINCT candidate_identity_id) AS candidates,
       count(DISTINCT employer_organisation_id) AS employers
FROM analytics_fact_source_channel
WHERE date_key >= date_trunc('month', current_date)
                - interval '1 month'
GROUP BY source_channel_code
ORDER BY applications DESC
LIMIT 10;
```

**Result:** 1 row.

| source_channel_code | applications | candidates | employers |
|---|---|---|---|
| portal | 54 | 49 | 1 |

### Ana-C10 — analytics fact: time-to-hire summary (outcome distribution)

```sql
SELECT outcome_code,
       count(*) AS applications,
       avg(days_to_outcome) AS avg_days_to_outcome,
       min(days_to_outcome) AS min_days,
       max(days_to_outcome) AS max_days
FROM analytics_fact_time_to_hire
WHERE date_key >= date_trunc('month', current_date)
                - interval '1 month'
GROUP BY outcome_code
ORDER BY outcome_code;
```

**Result:** 1 row.

| outcome_code | applications | avg_days_to_outcome | min_days | max_days |
|---|---|---|---|
| rejected | 54 |  |  |  |

The seeded time-to-hire fact has one outcome code in the current month window, but the outcome rows here do not carry a non-null `days_to_outcome`, so the average/min/max come back null in this sample window. That is a data-population question for the seed, not a query failure.

### Ana-C11 — analytics fact: gig marketplace summary by pipeline stage

```sql
SELECT pipeline_stage_code,
       count(*) AS records,
       count(DISTINCT gig_request_detail_id) AS requests,
       count(DISTINCT gig_worker_profile_id) AS workers,
       count(DISTINCT assignment_id) AS assignments,
       sum(earnings_amount) AS total_earnings
FROM analytics_fact_gig_marketplace
WHERE date_key >= date_trunc('month', current_date)
                - interval '1 month'
GROUP BY pipeline_stage_code
ORDER BY pipeline_stage_code;
```

**Result:** 1 row.

| pipeline_stage_code | records | requests | workers | assignments | total_earnings |
|---|---|---|---|---|---|
| applied | 75 | 75 | 75 | 15 |  |

### Ana-C12 — analytics fact: candidate activity summary (top candidates by actions)

```sql
SELECT candidate_identity_id,
       applications_sent_count, profile_views_count,
       searches_count,
       (applications_sent_count + profile_views_count
        + searches_count) AS total_actions
FROM analytics_fact_candidate_activity
WHERE activity_date_key >= date_trunc('month', current_date)
                            - interval '1 month'
ORDER BY total_actions DESC
LIMIT 10;
```

**Result:** 0 rows.

No candidate-activity fact rows fall in the current-month window for this seed.

### Ana-C13 — analytics fact: employer activity summary (top employers by posts)

```sql
SELECT employer_organisation_id, job_posts_count,
       applications_received_count, shortlisted_count,
       interviewed_count, offered_count, joined_count,
       rejected_count
FROM analytics_fact_employer_activity
WHERE activity_date_key >= date_trunc('month', current_date)
                            - interval '1 month'
ORDER BY job_posts_count DESC
LIMIT 10;
```

**Result:** 0 rows.

No employer-activity fact rows fall in the current-month window for this seed.

## Shared team items

### Shd-C14 — notification deliveries (status distribution)

```sql
SELECT delivery_status_code,
       count(*) AS deliveries,
       count(DISTINCT recipient_user_id) AS recipients
FROM notification_delivery
WHERE deleted_at IS NULL
GROUP BY delivery_status_code
ORDER BY deliveries DESC;
```

**Result:** 1 row.

| delivery_status_code | deliveries | recipients |
|---|---|---|
| sent | 5000 | 5000 |

### Shd-C15 — credential verification records (sample)

```sql
SELECT u.id, u.email, cv.credential_type_code,
       cv.credential_status_code, cv.verified_at,
       cv.last_used_at, cv.failure_count, cv.locked_until
FROM credential_verification cv
JOIN users u
       ON u.id = cv.user_id AND u.deleted_at IS NULL
WHERE cv.deleted_at IS NULL
ORDER BY cv.credential_type_code, cv.verified_at DESC
LIMIT 10;
```

**Result:** 10 rows.

| id | email | credential_type_code | credential_status_code | verified_at | last_used_at | failure_count | locked_until |
|---|---|---|---|---|---|---|---|
| 2 | candidate_2@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 3 | candidate_3@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 4 | candidate_4@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 5 | candidate_5@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 6 | candidate_6@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 7 | candidate_7@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 8 | candidate_8@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 9 | candidate_9@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 10 | candidate_10@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |
| 1 | candidate_1@example.com | password | locked | 2026-10-16 10:30:54.915454+00:00 | 2026-10-16 10:30:54.915454+00:00 | 0 |  |

### Shd-C16 — credential recovery records (sample)

```sql
SELECT u.id, u.email, cr.recovery_type_code,
       cr.requested_at, cr.used_at, cr.status_code,
       cr.token_ref
FROM credential_recovery cr
JOIN users u
       ON u.id = cr.user_id AND u.deleted_at IS NULL
WHERE cr.deleted_at IS NULL
ORDER BY cr.requested_at DESC
LIMIT 8;
```

**Result:** 8 rows.

| id | email | recovery_type_code | requested_at | used_at | status_code | token_ref |
|---|---|---|---|---|---|---|
| 7 | candidate_7@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 4 | candidate_4@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 5 | candidate_5@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 6 | candidate_6@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 1 | candidate_1@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 3 | candidate_3@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 2 | candidate_2@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |
| 8 | candidate_8@example.com | email_reset | 2026-10-16 17:04:09.679945+00:00 |  | completed |  |

### Shd-C17 — consent records (sample)

```sql
SELECT u.id, u.email, cr.consent_type_code,
       cr.consent_value_code, cr.recorded_at, cr.ip_address
FROM consent_record cr
JOIN users u
       ON u.id = cr.user_id AND u.deleted_at IS NULL
WHERE cr.deleted_at IS NULL
ORDER BY cr.recorded_at DESC
LIMIT 8;
```

**Result:** 8 rows.

| id | email | consent_type_code | consent_value_code | recorded_at | ip_address |
|---|---|---|---|---|---|
| 100 | candidate_100@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 99 | candidate_99@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 98 | candidate_98@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 97 | candidate_97@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 96 | candidate_96@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 95 | candidate_95@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 94 | candidate_94@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |
| 93 | candidate_93@example.com | data_processing | granted | 2026-10-16 17:04:09.768109+00:00 |  |

### Shd-C18 — audit events (sample)

```sql
SELECT a.id, a.actor_user_id, a.event_type_code,
       a.target_table, a.target_id, u.email AS actor_email,
       a.occurred_at, a.source_ip
FROM audit_event a
LEFT JOIN users u ON u.id = a.actor_user_id
ORDER BY a.occurred_at DESC
LIMIT 8;
```

**Result:** 8 rows.

| id | actor_user_id | event_type_code | target_table | target_id | actor_email | occurred_at | source_ip |
|---|---|---|---|---|---|---|---|
| 300 | 50 | evt_login | users | 50 | candidate_50@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 299 | 49 | evt_login | users | 49 | candidate_49@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 298 | 48 | evt_login | users | 48 | candidate_48@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 297 | 47 | evt_login | users | 47 | candidate_47@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 296 | 46 | evt_login | users | 46 | candidate_46@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 295 | 45 | evt_login | users | 45 | candidate_45@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 294 | 44 | evt_login | users | 44 | candidate_44@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |
| 293 | 43 | evt_login | users | 43 | candidate_43@example.com | 2026-10-16 17:04:09.845900+00:00 | 127.0.0.1 |

### Shd-C19 — blocking list (active)

```sql
SELECT b.id, b.blocker_user_id, u1.email AS blocker_email,
       b.blocked_party_type_code, b.blocked_party_id,
       b.blocked_at, b.is_active, b.reason
FROM blocking_list b
LEFT JOIN users u1 ON u1.id = b.blocker_user_id
WHERE b.is_active = true
  AND b.deleted_at IS NULL
ORDER BY b.blocked_at DESC
LIMIT 8;
```

**Result:** 8 rows.

| id | blocker_user_id | blocker_email | blocked_party_type_code | blocked_party_id | blocked_at | is_active | reason |
|---|---|---|---|---|---|---|---|
| 9 | 2 | candidate_2@example.com | bpt_candidate | 53 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 10 | 3 | candidate_3@example.com | bpt_candidate | 54 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 11 | 4 | candidate_4@example.com | bpt_candidate | 55 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 12 | 5 | candidate_5@example.com | bpt_candidate | 56 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 13 | 6 | candidate_6@example.com | bpt_candidate | 57 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 14 | 7 | candidate_7@example.com | bpt_candidate | 58 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 15 | 8 | candidate_8@example.com | bpt_candidate | 59 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |
| 8 | 1 | candidate_1@example.com | bpt_candidate | 52 | 2026-10-16 17:04:09.857360+00:00 | True | Seeded blocking entry |

### Shd-C20 — analytics: source-channel fact rows (sample)

```sql
SELECT af.id, af.application_id, af.candidate_identity_id,
       af.job_requirement_id, af.employer_organisation_id,
       af.source_channel_code, af.applied_at, af.date_key
FROM analytics_fact_source_channel af
WHERE af.deleted_at IS NULL
ORDER BY af.applied_at DESC
LIMIT 8;
```

**Result:** Query execution failed — `column af.deleted_at does not exist`.

`analytics_fact_source_channel` does not have a `deleted_at` column in the seeded schema, so a `WHERE af.deleted_at IS NULL` predicate cannot run. That is a schema-coverage gap for soft-delete on this analytics fact, not a data-corruption failure; the fact rows themselves are present and queryable without that predicate.

## Observations for Member C

- **Notifications** queries confirm preferences, job alerts, multilingual/privacy settings, support tickets with replies, and FAQ are present and joinable; one community-post query fails on `GROUP BY` and should be corrected rather than treated as missing data.
- **Analytics** dimension and fact queries confirm the star schema is populated: `analytics_dim_date` is flagged as current, and the pipeline / source-channel / time-to-hire / gig facts return grouped results for the current month window. Two facts (`analytics_fact_candidate_activity` and `analytics_fact_employer_activity`) have no rows in the current month window, which is a seed-population observation, not a query error.
- **Shared items** queries confirm notification deliveries, credential verification, credential recovery, consent, audit events, and blocking entries are all present and queryable; one analytics fact query fails because the analytics table lacks a `deleted_at` column.

## Companion artifacts

- Raw output for every query above: `scripts/reports/B69_member_C_Notifications_Analytics_Shared.txt`
- Validation of the underlying seed data: `docs/team_deliverables/B66_seed_validation_report.md`
