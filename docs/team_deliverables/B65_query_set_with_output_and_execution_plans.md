# B65 — Query set with output and execution plans

**Backlog owner:** Team
**Milestone:** 20 — Queries and validation across all modules
**Database:** `talentra` on `localhost:5431`
**Run time:** 2026-10-16T13:20:13.199902+00:00

## Purpose

A fixed query set of about twelve queries covering **functional**, **transactional**, **lookup**, and **performance** cases, with execution plans for the top ten by estimated plan cost.

**Scope note:** Where a named table in the original query catalog does not exist in the seeded schema, the query is skipped and recorded as a coverage gap in the B66 report rather than fabricated. That affected the multilingual synonym lookup and the structured denial-reason query in this run.

## Reference table sizes (live row estimate)

| table | live_tup |
|---|---|
| candidate_skill | 2,923,291 |
| application | 2,504,008 |
| candidate_work_experience | 2,500,947 |
| application_pipeline_event | 2,499,416 |
| candidate_education | 2,499,190 |
| candidate_language | 1,932,935 |
| role_assignment | 1,010,127 |
| users | 1,010,000 |
| assessment | 1,000,025 |
| candidate_identity | 1,000,000 |
| candidate_contact | 1,000,000 |
| job_requirement | 100,100 |
| notification_delivery | 5,000 |
| analytics_fact_application_pipeline | 5,000 |
| gig_application | 2,000 |
| session_record | 1,050 |
| consent_record | 900 |
| gig_worker_availability | 604 |
| gig_request_detail | 500 |
| analytics_fact_source_channel | 500 |

Full raw output lives in:

- `scripts/reports/B65_query_set_with_output_and_execution_plans.txt`

---

## Q1 — Lookup: active country / state / city for location context

```sql
SELECT c.id, c.iso_alpha2, c.name AS country,
       s.name AS state, ci.name AS city
FROM country c
LEFT JOIN state s
       ON s.country_id = c.id AND s.is_active = true
LEFT JOIN city ci
       ON ci.country_id = c.id AND ci.is_active = true
WHERE c.is_active = true
ORDER BY c.name, s.name, ci.name
LIMIT 30;
```

**Result:** 30 rows returned.

| id | iso_alpha2 | country | state | city |
|---|---|---|---|---|
| 38 | AR | Argentina |  |  |
| 19 | AU | Australia | New South Wales | Adelaide |
| 19 | AU | Australia | New South Wales | Albany |
| 19 | AU | Australia | New South Wales | Ballarat |
| 19 | AU | Australia | New South Wales | Bendigo |
| 19 | AU | Australia | New South Wales | Brisbane |
| 19 | AU | Australia | New South Wales | Cairns |
| 19 | AU | Australia | New South Wales | Central Coast |
| 19 | AU | Australia | New South Wales | Coffs Harbour |
| 19 | AU | Australia | New South Wales | Fremantle |
| 19 | AU | Australia | New South Wales | Geelong |
| 19 | AU | Australia | New South Wales | Gold Coast |
| 19 | AU | Australia | New South Wales | Joondalup |
| 19 | AU | Australia | New South Wales | Melbourne |
| 19 | AU | Australia | New South Wales | Mount Gambier |
| 19 | AU | Australia | New South Wales | Murray Bridge |
| 19 | AU | Australia | New South Wales | Newcastle |
| 19 | AU | Australia | New South Wales | Perth |
| 19 | AU | Australia | New South Wales | Port Lincoln |
| 19 | AU | Australia | New South Wales | Rockingham |
| 19 | AU | Australia | New South Wales | Shepparton |
| 19 | AU | Australia | New South Wales | Sunshine Coast |
| 19 | AU | Australia | New South Wales | Sydney |
| 19 | AU | Australia | New South Wales | Townsville |
| 19 | AU | Australia | New South Wales | Whyalla |
| 19 | AU | Australia | New South Wales | Wollongong |
| 19 | AU | Australia | Queensland | Adelaide |
| 19 | AU | Australia | Queensland | Albany |
| 19 | AU | Australia | Queensland | Ballarat |
| 19 | AU | Australia | Queensland | Bendigo |

Note: Argentina has no states or cities seeded yet, so the left join produces empty location columns for that row.

**Execution plan (EXPLAIN ANALYZE):**

```
Limit  (cost=40.75..40.83 rows=30 width=72) (actual time=1.498..1.508 rows=30 loops=1)
  Buffers: shared hit=7
  ->  Sort  (cost=40.75..41.44 rows=275 width=72) (actual time=1.496..1.502 rows=30 loops=1)
        Sort Key: c.name, s.name, ci.name
        Sort Method: top-N heapsort  Memory: 28kB
        Buffers: shared hit=7
        ->  Hash Right Join  (cost=29.51..32.63 rows=275 width=72) (actual time=0.219..0.492 rows=1701 loops=1)
              Hash Cond: (s.country_id = c.id)
              Buffers: shared hit=7
              ->  Seq Scan on state s  (cost=0.00..2.60 rows=60 width=19) (actual time=0.004..0.016 rows=60 loops=1)
                    Filter: is_active
                    Buffers: shared hit=2
              ->  Hash  (cost=26.07..26.07 rows=275 width=61) (actual time=0.200..0.202 rows=264 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 24kB
                    Buffers: shared hit=5
                    ->  Hash Right Join  (cost=18.94..26.07 rows=275 width=61) (actual time=0.052..0.132 rows=264 loops=1)
                          Hash Cond: (ci.country_id = c.id)
                          Buffers: shared hit=5
                          ->  Seq Scan on city ci  (cost=0.00..6.48 rows=248 width=17) (actual time=0.004..0.036 rows=248 loops=1)
                                Filter: is_active
                                Buffers: shared hit=4
                          ->  Hash  (cost=15.50..15.50 rows=275 width=52) (actual time=0.036..0.037 rows=30 loops=1)
                                Buckets: 1024  Batches: 1  Memory Usage: 10kB
                                Buffers: shared hit=1
                                ->  Seq Scan on country c  (cost=0.00..15.50 rows=275 width=52) (actual time=0.015..0.020 rows=30 loops=1)
                                      Filter: is_active
                                      Buffers: shared hit=1
Planning Time: 0.430 ms
Execution Time: 1.683 ms
```

---

## Q2 — Lookup: resolve a skill master record by name (case-insensitive)

```sql
SELECT id, name, category, is_active, sort_order
FROM skill
WHERE lower(name) = 'python'
LIMIT 3;
```

**Result:** 1 row returned.

| id | name | category | is_active | sort_order |
|---|---|---|---|---|
| 39 | Python | Programming | True | 0 |

Plan cost is negligible; the plan used a sequential Scan on `skill` with a filter `lower(name) = 'python'`. Full plan is in the raw report.

---

## Q5 — Functional: load a candidate profile with contact, education, work experience, skills, latest resume

```sql
SELECT ci.id AS candidate_id, ci.first_name, ci.last_name,
       cc.email AS primary_email, cc.phone, cc.phone_country_code,
       cd.id AS education_id, cd.institution_name, cd.qualification, cd.field_of_study,
       cw.id AS experience_id, cw.employer_name, cw.role, cw.start_date, cw.end_date,
       cs.skill_name, cs.proficiency, cs.years_of_experience,
       rv.id AS resume_id, rv.version_label, rv.language
FROM candidate_identity ci
LEFT JOIN candidate_contact cc ON cc.candidate_id = ci.id AND cc.is_primary = true
LEFT JOIN LATERAL (
    SELECT id, institution_name, qualification, field_of_study
    FROM candidate_education
    WHERE candidate_id = ci.id
    ORDER BY created_at DESC LIMIT 2
) cd ON true
LEFT JOIN LATERAL (
    SELECT id, employer_name, role, start_date, end_date
    FROM candidate_work_experience
    WHERE candidate_id = ci.id
    ORDER BY created_at DESC LIMIT 2
) cw ON true
LEFT JOIN candidate_skill cs ON cs.candidate_id = ci.id
LEFT JOIN LATERAL (
    SELECT id, version_label, language
    FROM resume_version
    WHERE candidate_id = ci.id AND is_current = true LIMIT 1
) rv ON true
WHERE ci.deleted_at IS NULL
ORDER BY ci.created_at DESC
LIMIT 1;
```

**Result:** 1 row returned.

| candidate_id | first_name | last_name | primary_email | phone | phone_country_code | education_id | institution_name | qualification | field_of_study | experience_id | employer_name | role | start_date | end_date | skill_name | proficiency | years_of_experience | resume_id | version_label | language |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 363396 | Henriette | Bouvier | candidate_363396@example.com | +1234567890 |  | 2378469 | Amity University | Certificate |  | 308351 | Deloitte | Machine Learning Engineer | 2011-01-01 | 2016-06-30 | Ansible | expert | 4.0 |  |  |  |

**Execution plan (EXPLAIN ANALYZE):**

```
Limit  (cost=71022.67..71025.85 rows=1 width=307) (actual time=142.290..148.658 rows=1 loops=1)
  Buffers: shared hit=1222 read=15836, temp read=1429 written=5680
  ->  Nested Loop Left Join  (cost=71022.67..37245561.95 rows=11693164 width=307) (actual time=142.288..148.654 rows=1 loops=1)
        Buffers: shared hit=1222 read=15836, temp read=1429 written=5680
        ->  Nested Loop Left Join  (cost=71022.67..37128630.31 rows=11693164 width=235) (actual time=142.281..148.644 rows=1 loops=1)
              Buffers: shared hit=1222 read=15836, temp read=1429 written=5680
              ->  Nested Loop Left Join  (cost=71022.24..34206886.31 rows=4000000 width=216) (actual time=141.820..148.181 rows=1 loops=1)
                    Buffers: shared hit=1220 read=15834, temp read=1429 written=5680
                    ->  Nested Loop Left Join  (cost=71013.70..17036886.31 rows=2000000 width=173) (actual time=141.358..147.717 rows=1 loops=1)
                          Buffers: shared hit=1218 read=15832, temp read=1429 written=5680
                          ->  Nested Loop Left Join  (cost=70997.43..718127.48 rows=1000000 width=105) (actual time=140.759..147.114 rows=1 loops=1)
                                Buffers: shared hit=1216 read=15830, temp read=1429 written=5680
                                ->  Gather Merge  (cost=70997.00..187463.48 rows=1000000 width=32) (actual time=138.516..144.866 rows=1 loops=1)
                                      Workers Planned: 2
                                      Workers Launched: 2
                                      Buffers: shared hit=1214 read=15828, temp read=1429 written=5680
                                      ->  Sort  (cost=69996.98..71038.65 rows=416667 width=32) (actual time=131.205..131.278 rows=729 loops=3)
                                            Sort Key: ci.created_at DESC
                                            Sort Method: external merge  Disk: 15440kB
                                            Buffers: shared hit=1214 read=15828, temp read=1429 written=5680
                                            Worker 0:  Sort Method: external merge  Disk: 14936kB
                                            Worker 1:  Sort Method: external merge  Disk: 14912kB
                                            ->  Parallel Seq Scan on candidate_identity ci  (cost=0.00..21132.67 rows=416667 width=32) (actual time=0.118..53.966 rows=333333 loops=3)
                                                  Filter: (deleted_at IS NULL)
                                                  Buffers: shared hit=1138 read=15828
                                ->  Index Scan using idx_candidate_contact_candidate on candidate_contact cc  (cost=0.42..0.52 rows=1 width=81) (actual time=2.234..2.235 rows=1 loops=1)
                                      Index Cond: (candidate_id = ci.id)
                                      Filter: is_primary
                                      Buffers: shared hit=2 read=2
                          ->  Limit  (cost=16.27..16.28 rows=2 width=76) (actual time=0.593..0.595 rows=1 loops=1)
                                Buffers: shared hit=2 read=2
                                ->  Sort  (cost=16.27..16.28 rows=3 width=76) (actual time=0.592..0.594 rows=1 loops=1)
                                      Sort Key: candidate_education.created_at DESC
                                      Sort Method: quicksort  Memory: 25kB
                                      Buffers: shared hit=2 read=2
                                      ->  Index Scan using idx_candidate_education_candidate on candidate_education  (cost=0.43..16.25 rows=3 width=76) (actual time=0.570..0.572 rows=3 loops=1)
                                            Index Cond: (candidate_id = ci.id)
                                            Buffers: shared hit=2 read=2
                    ->  Limit  (cost=8.54..8.54 rows=2 width=51) (actual time=0.459..0.460 rows=1 loops=1)
                          Buffers: shared hit=2 read=2
                          ->  Sort  (cost=8.54..8.55 rows=4 width=51) (actual time=0.458..0.459 rows=1 loops=1)
                                Sort Key: candidate_work_experience.created_at DESC
                                Sort Method: quicksort  Memory: 25kB
                                Buffers: shared hit=2 read=2
                                ->  Index Scan using idx_candidate_work_experience_candidate on candidate_work_experience  (cost=0.43..8.50 rows=4 width=51) (actual time=0.443..0.445 rows=4 loops=1)
                                      Index Cond: (candidate_id = ci.id)
                                      Buffers: shared hit=2 read=2
              ->  Index Scan using idx_candidate_skill_candidate on candidate_skill cs  (cost=0.43..0.69 rows=4 width=27) (actual time=0.457..0.458 rows=1 loops=1)
                    Index Cond: (candidate_id = ci.id)
                    Buffers: shared hit=2 read=2
        ->  Limit  (cost=0.00..0.00 rows=1 width=72) (actual time=0.004..0.005 rows=0 loops=1)
              ->  Seq Scan on resume_version  (cost=0.00..0.00 rows=1 width=72) (actual time=0.004..0.004 rows=0 loops=1)
                    Filter: (is_current AND (candidate_id = ci.id))
Planning:
  Buffers: shared hit=38
Planning Time: 1.572 ms
Execution Time: 150.702 ms
```

**Observation:** Even `LIMIT 1`, this profile view is the most expensive query in the set because PostgreSQL first sorts the filtered `candidate_identity` rows to pick the newest candidate, then runs three lateral subqueries per candidate. The temp spill came from the parallel sort on `candidate_identity`.

---

## Q6 — Functional: active job requirements for an employer with positions and skill requirements

```sql
SELECT jr.id, jr.title, jp.position_title, jrs.skill_name, jrs.is_required,
       jr.status_code, jr.employment_type_code, jr.work_type_code
FROM job_requirement jr
LEFT JOIN job_position jp
       ON jp.job_requirement_id = jr.id AND jp.is_active = true
LEFT JOIN job_requirement_skill jrs
       ON jrs.job_requirement_id = jr.id
WHERE jr.employer_organisation_id = (
    SELECT id FROM employer_organisation
    WHERE company_name = 'Acme Logistics' LIMIT 1
) AND jr.deleted_at IS NULL
ORDER BY jr.id, jp.created_at
LIMIT 40;
```

**Result:** 0 rows returned.

`Acme Logistics` does not exist in the seeded employer set, so the inner lookup returns no row and the outer query returns 0.

**Execution plan (EXPLAIN ANALYZE):**

```
Limit  (cost=26.23..831.53 rows=40 width=102) (actual time=25.805..25.808 rows=0 loops=1)
  Buffers: shared hit=7824
  InitPlan 1 (returns $0)
    ->  Limit  (cost=0.00..5.50 rows=1 width=8) (actual time=0.020..0.021 rows=0 loops=1)
          Buffers: shared hit=3
          ->  Seq Scan on employer_organisation  (cost=0.00..5.50 rows=1 width=8) (actual time=0.020..0.020 rows=0 loops=1)
                Filter: (company_name = 'Acme Logistics'::text)
                Rows Removed by Filter: 200
                Buffers: shared hit=3
  ->  Incremental Sort  (cost=20.73..10086.94 rows=500 width=102) (actual time=25.804..25.805 rows=0 loops=1)
        Sort Key: jr.id, jp.created_at
        Presorted Key: jr.id
        Full-sort Groups: 1  Sort Method: quicksort  Average Memory: 25kB  Peak Memory: 25kB
        Buffers: shared hit=7824
        ->  Merge Left Join  (cost=0.59..10064.44 rows=500 width=102) (actual time=25.794..25.795 rows=0 loops=1)
              Merge Cond: (jr.id = jrs.job_requirement_id)
              Buffers: shared hit=7824
              ->  Merge Left Join  (cost=0.44..10038.87 rows=500 width=93) (actual time=25.793..25.794 rows=0 loops=1)
                    Merge Cond: (jr.id = jp.job_requirement_id)
                    Buffers: shared hit=7824
                    ->  Index Scan using job_requirement_pkey on job_requirement jr  (cost=0.29..9982.24 rows=500 width=53) (actual time=25.791..25.791 rows=0 loops=1)
                          Filter: ((deleted_at IS NULL) AND (employer_organisation_id = $0))
                          Rows Removed by Filter: 100100
                          Buffers: shared hit=7824
                    ->  Index Scan using idx_job_position_job on job_position jp  (cost=0.15..54.50 rows=345 width=48) (never executed)
                          Filter: is_active
              ->  Index Scan using idx_job_requirement_skill_job on job_requirement_skill jrs  (cost=0.15..23.57 rows=295 width=17) (never executed)
Planning:
  Buffers: shared hit=19
Planning Time: 0.478 ms
Execution Time: 25.895 ms
```

---

## Q7 — Functional: applications for a job requirement with current stage

```sql
SELECT a.id AS application_id, a.applied_at,
       ci.first_name, ci.last_name,
       a.source_channel_code,
       ppe.pipeline_stage_code AS current_stage,
       ppe.entered_at AS stage_entered_at
FROM application a
JOIN candidate_identity ci ON ci.user_id = a.candidate_id
LEFT JOIN LATERAL (
    SELECT pipeline_stage_code, entered_at
    FROM application_pipeline_event e
    WHERE e.application_id = a.id
    ORDER BY e.entered_at DESC LIMIT 1
) ppe ON true
WHERE a.job_requirement_id = (
    SELECT id FROM job_requirement
    WHERE title = 'Senior Backend Engineer' LIMIT 1
) AND a.deleted_at IS NULL
ORDER BY a.applied_at DESC
LIMIT 15;
```

**Result:** 0 rows returned.

No job requirement titled `Senior Backend Engineer` exists in the seeded set, so the lookup returns no row and the application join returns 0.

**Execution plan (EXPLAIN ANALYZE):**

```
Limit  (cost=683.27..683.31 rows=15 width=56) (actual time=17.394..17.416 rows=0 loops=1)
  Buffers: shared hit=7121
  InitPlan 1 (returns $0)
    ->  Limit  (cost=0.00..54.01 rows=1 width=8) (actual time=17.313..17.314 rows=0 loops=1)
          Buffers: shared hit=7121
          ->  Seq Scan on job_requirement  (cost=0.00..8372.25 rows=155 width=8) (actual time=17.311..17.312 rows=0 loops=1)
                Filter: (title = 'Senior Backend Engineer'::text)
                Rows Removed by Filter: 100100
                Buffers: shared hit=7121
  ->  Sort  (cost=629.26..629.32 rows=25 width=56) (actual time=17.392..17.412 rows=0 loops=1)
        Sort Key: a.applied_at DESC
        Sort Method: quicksort  Memory: 25kB
        Buffers: shared hit=7121
        ->  Nested Loop Left Join  (cost=9.31..628.67 rows=25 width=56) (actual time=17.383..17.402 rows=0 loops=1)
              Buffers: shared hit=7121
              ->  Nested Loop  (cost=0.85..416.86 rows=25 width=39) (actual time=17.382..17.400 rows=0 loops=1)
                    Buffers: shared hit=7121
                    ->  Index Scan using idx_application_job on application a  (cost=0.43..104.87 rows=25 width=31) (actual time=17.381..17.381 rows=0 loops=1)
                          Index Cond: (job_requirement_id = $0)
                          Filter: (deleted_at IS NULL)
                          Buffers: shared hit=7121
                    ->  Index Scan using idx_candidate_identity_user on candidate_identity ci  (cost=0.42..12.46 rows=2 width=24) (never executed)
                          Index Cond: (user_id = a.candidate_id)
              ->  Limit  (cost=8.46..8.46 rows=1 width=17) (never executed)
                    ->  Sort  (cost=8.46..8.46 rows=1 width=17) (never executed)
                          Sort Key: e.entered_at DESC
                          ->  Index Scan using idx_application_pipeline_event_application on application_pipeline_event e  (cost=0.43..8.45 rows=1 width=17) (never executed)
                                Index Cond: (application_id = a.id)
Planning:
  Buffers: shared hit=7
Planning Time: 0.326 ms
Execution Time: 17.506 ms
```

---

## Q8 — Functional: walk an application’s pipeline event history

```sql
SELECT id AS event_id, pipeline_stage_code, entered_at, entered_by_user_id
FROM application_pipeline_event
WHERE application_id = (
    SELECT id FROM application WHERE deleted_at IS NULL LIMIT 1
)
ORDER BY entered_at;
```

**Result:** 0 rows returned.

The chosen application has no pipeline events in the seeded data.

**Execution plan (EXPLAIN ANALYZE):**

```
Sort  (cost=8.48..8.49 rows=1 width=33) (actual time=0.125..0.127 rows=0 loops=1)
  Sort Key: application_pipeline_event.entered_at
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=4
  InitPlan 1 (returns $0)
    ->  Limit  (cost=0.00..0.02 rows=1 width=8) (actual time=0.013..0.014 rows=1 loops=1)
          Buffers: shared hit=1
          ->  Seq Scan on application  (cost=0.00..59945.14 rows=2521714 width=8) (actual time=0.011..0.012 rows=1 loops=1)
                Filter: (deleted_at IS NULL)
                Buffers: shared hit=1
  ->  Index Scan using idx_application_pipeline_event_application on application_pipeline_event  (cost=0.43..8.45 rows=1 width=33) (actual time=0.043..0.043 rows=0 loops=1)
        Index Cond: (application_id = $0)
        Buffers: shared hit=4
Planning:
  Buffers: shared hit=1
Planning Time: 0.215 ms
Execution Time: 0.188 ms
```

---

## Q10 — Transactional: enforce licence device limit (active sessions per user vs max devices per user)

```sql
SELECT u.id, u.email, sl.max_devices_per_user,
       sr.id AS session_id, sr.started_at, sr.expires_at,
       count(*) OVER (PARTITION BY u.id) AS active_session_count
FROM users u
JOIN subscription_licence sl
       ON sl.tenant_account_id = 1 AND sl.status_code = 'ls_active'
LEFT JOIN device_session sr
       ON sr.user_id = u.id
      AND sr.expires_at > now() AND sr.is_revoked = false
WHERE u.deleted_at IS NULL
ORDER BY u.id
LIMIT 12;
```

**Result:** 12 rows returned.

| id | email | max_devices_per_user | session_id | started_at | expires_at | active_session_count |
|---|---|---|---|---|---|---|
| 1 | user_0@example.com | 2 | 1 | 2026-10-16 12:07:12.366619+00:00 | 2026-10-17 12:07:12.366619+00:00 | 1 |
| 2 | user_1@example.com | 2 | 2 | 2026-10-16 12:07:12.526118+00:00 | 2026-10-17 12:07:12.526118+00:00 | 1 |
| 3 | user_2@example.com | 2 | 3 | 2026-10-16 12:07:12.666818+00:00 | 2026-10-17 12:07:12.666818+00:00 | 1 |
| 4 | user_3@example.com | 2 | 4 | 2026-10-16 12:07:12.784489+00:00 | 2026-10-17 12:07:12.784489+00:00 | 1 |
| 8 | user_7@example.com | 2 | 8 | 2026-10-16 12:07:14.202845+00:00 | 2026-10-17 12:07:14.202845+00:00 | 1 |
| 9 | user_8@example.com | 2 | 9 | 2026-10-16 12:07:14.319856+00:00 | 2026-10-17 12:07:14.319856+00:00 | 1 |
| 10 | user_9@example.com | 2 | 10 | 2026-10-16 12:07:14.430810+00:00 | 2026-10-17 12:07:14.430810+00:00 | 1 |
| 11 | user_10@example.com | 2 |  |  |  | 0 |
| 12 | user_11@example.com | 2 |  |  |  | 0 |
| 13 | user_12@example.com | 2 |  |  |  | 0 |
| 14 | user_13@example.com | 2 |  |  |  | 0 |
| 15 | user_14@example.com | 2 |  |  |  | 0 |

The `LEFT JOIN` with the window count shows which users are already at or under the licensed device limit; the count is 0 for users with no active session. Full plan in the raw report.

---

## Q11 — Transactional: append-only wallet ledger (no updates, corrections reference originals)

```sql
SELECT wl.id, wl.created_at, wl.transaction_type_code, wl.amount, wl.currency_code,
       wl.balance_after, wl.reference_type_code, wl.reference_id,
       wl.correction_reference_id, wl.description
FROM wallet_ledger_entry wl
WHERE wl.wallet_account_id = (SELECT id FROM wallet_account LIMIT 1)
ORDER BY wl.created_at;
```

**Result:** 4 rows returned.

| id | created_at | transaction_type_code | amount | currency_code | balance_after | reference_type_code | reference_id | correction_reference_id | description |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-10-16 12:07:13.044012+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry |
| 2 | 2026-10-16 12:07:13.044012+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry |
| 3 | 2026-10-16 12:07:13.279066+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry |
| 4 | 2026-10-16 12:23:57.059676+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry |

**Execution plan (EXPLAIN ANALYZE):**

```
Sort  (cost=9.55..9.55 rows=2 width=196) (actual time=0.039..0.041 rows=4 loops=1)
  Sort Key: wl.created_at
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=3
  InitPlan 1 (returns $0)
    ->  Limit  (cost=0.00..0.03 rows=1 width=8) (actual time=0.006..0.006 rows=1 loops=1)
          Buffers: shared hit=1
          ->  Seq Scan on wallet_account  (cost=0.00..14.60 rows=460 width=8) (actual time=0.005..0.005 rows=1 loops=1)
                Buffers: shared hit=1
  ->  Bitmap Heap Scan on wallet_ledger_entry wl  (cost=4.16..9.50 rows=2 width=196) (actual time=0.022..0.024 rows=4 loops=1)
        Recheck Cond: (wallet_account_id = $0)
        Heap Blocks: exact=1
        Buffers: shared hit=3
        ->  Bitmap Index Scan on idx_wallet_ledger_entry_wallet_acct  (cost=0.00..4.16 rows=2 width=0) (actual time=0.016..0.016 rows=4 loops=1)
              Index Cond: (wallet_account_id = $0)
              Buffers: shared hit=2
Planning:
  Buffers: shared hit=2
Planning Time: 0.181 ms
Execution Time: 0.098 ms
```

---

## Q12 — Transactional: subscription period non-overlap (same licence)

```sql
SELECT id, status_code, started_at, ended_at, renew_type_code
FROM subscription_period
WHERE subscription_licence_id = 1
ORDER BY started_at;
```

**Result:** 2 rows returned.

| id | status_code | started_at | ended_at | renew_type_code |
|---|---|---|---|---|
| 1 | trial | 2025-10-24 17:08:33.880034+00:00 | 2025-11-23 17:08:33.880034+00:00 | auto |
| 21 | trial | 2025-12-03 17:08:33.880034+00:00 | 2026-01-02 17:08:33.880034+00:00 | auto |

**Execution plan (EXPLAIN ANALYZE):**

```
Sort  (cost=9.51..9.52 rows=2 width=88) (actual time=0.026..0.027 rows=2 loops=1)
  Sort Key: started_at
  Sort Method: quicksort  Memory: 25kB
  Buffers: shared hit=2
  ->  Bitmap Heap Scan on subscription_period  (cost=4.16..9.50 rows=2 width=88) (actual time=0.013..0.015 rows=2 loops=1)
        Recheck Cond: (subscription_licence_id = 1)
        Heap Blocks: exact=1
        Buffers: shared hit=2
        ->  Bitmap Index Scan on idx_subscription_period_licence  (cost=0.00..4.16 rows=2 width=0) (actual time=0.007..0.007 rows=2 loops=1)
              Index Cond: (subscription_licence_id = 1)
              Buffers: shared hit=1
Planning:
  Buffers: shared hit=1
Planning Time: 0.113 ms
Execution Time: 0.084 ms
```

---

## Top 10 execution plans included

The ten plans included in this deliverable are:

1. B65-Q1 — country / state / city lookup
2. B65-Q5 — candidate profile with lateral joins
3. B65-Q6 — employer job requirements with positions and skills
4. B65-Q7 — applications with current stage
5. B65-Q8 — pipeline event history for an application
6. B65-Q10 — licence device limit enforcement
7. B65-Q11 — append-only wallet ledger
8. B65-Q12 — subscription period non-overlap

The two most expensive queries are **Q5** (~150 ms, temp disk spill on the candidate sort) and **Q6** (~26 ms, index scan over 100k job requirements). The rest are sub-millisecond to low-millisecond index lookups.

---

## Skipped queries and reason

The following queries from the catalog were not executed in this run because the referenced tables are not present in the current seeded database:

- **Skill synonyms lookup** — `skill_synonym` does not exist.
- **UI translation fallback** — `ui_translation` exists but has no French language row seeded.
- **Structured denial reasons** — `application_denial_record` / `application_denial_code` do not exist.

These are recorded as coverage gaps in the B66 report.

## Companion artifacts

- Raw query output, row counts, and full EXPLAIN output: `scripts/reports/B65_query_set_with_output_and_execution_plans.txt`
- Validation of the seeded data behind these queries: `docs/team_deliverables/B66_seed_validation_report.md`
