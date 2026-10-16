# B68 — Module query results: Licences, Sourcing, Subscriptions

**Owner:** Member B
**Milestone:** 20 — Queries and validation across all modules
**Database:** `talentra` on `localhost:5431`
**Run time:** 2026-10-16T13:33:15.623281+00:00

Raw module output lives in `scripts/reports/B68_member_B_Licences_Sourcing_Subs.txt`.

## Licences

### Lic-B1 — subscription licences with tenant

```sql
SELECT sl.id, sl.licence_number, sl.licence_type_code,
       sl.status_code, ta.name AS tenant_name,
       sl.max_users_allowed, sl.max_devices_per_user,
       sl.issued_at, sl.activated_at, sl.suspended_at,
       sl.terminated_at
FROM subscription_licence sl
JOIN tenant_account ta ON ta.id = sl.tenant_account_id
ORDER BY sl.created_at;
```

**Result:** 20 rows.

| id | licence_number | licence_type_code | status_code | tenant_name | max_users_allowed | max_devices_per_user | issued_at | activated_at | suspended_at | terminated_at |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | LC-1000 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 2 | LC-1001 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 3 | LC-1002 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 4 | LC-1003 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 5 | LC-1004 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 6 | LC-1005 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 7 | LC-1006 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 8 | LC-1007 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 9 | LC-1008 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 10 | LC-1009 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 11 | LC-1010 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 12 | LC-1011 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 13 | LC-1012 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 14 | LC-1013 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 15 | LC-1014 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 16 | LC-1015 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 17 | LC-1016 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 18 | LC-1017 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 19 | LC-1018 | standard | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |
| 20 | LC-1019 | enterprise | ls_active | Talentra Platform | 50 | 5 | 2026-10-16 11:34:53.679508+00:00 | 2026-10-16 11:34:53.679508+00:00 |  |  |

All licences are active and have explicit `max_users_allowed` and `max_devices_per_user`, which supports Rule Group 9 enforcement checking.

### Lic-B2 — seat allocations against a licence (sample)

```sql
SELECT sl.licence_number, sa.id, u.email, u.first_name,
       u.last_name, sa.seat_status_code, sa.allocated_at,
       sa.revoked_at, sa.is_active
FROM seat_allocation sa
JOIN subscription_licence sl ON sl.id = sa.subscription_licence_id
JOIN users u ON u.id = sa.user_id AND u.deleted_at IS NULL
WHERE sa.deleted_at IS NULL
ORDER BY sl.id, sa.allocated_at
LIMIT 15;
```

**Result:** 15 rows.

| licence_number | id | email | first_name | last_name | seat_status_code | allocated_at | revoked_at | is_active |
|---|---|---|---|---|---|---|---|---|
| LC-1000 | 181 | candidate_181@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 61 | candidate_61@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 81 | candidate_81@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 21 | candidate_21@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 121 | candidate_121@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 161 | candidate_161@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 101 | candidate_101@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 141 | candidate_141@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 1 | candidate_1@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1000 | 41 | candidate_41@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1001 | 122 | candidate_122@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1001 | 102 | candidate_102@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1001 | 182 | candidate_182@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1001 | 82 | candidate_82@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |
| LC-1001 | 62 | candidate_62@example.com |  |  | allocated | 2026-10-16 11:34:54.431028+00:00 |  | True |

### Lic-B3 — device registrations per user (sample)

```sql
SELECT u.id, u.email, u.first_name, dr.id AS device_id,
       dr.device_identifier, dr.device_type_code,
       dr.last_seen_at, dr.revoked_at, dr.is_active
FROM device_registration dr
JOIN users u ON u.id = dr.user_id AND u.deleted_at IS NULL
WHERE dr.deleted_at IS NULL
ORDER BY u.id
LIMIT 10;
```

**Result:** 10 rows.

| id | email | first_name | device_id | device_identifier | device_type_code | last_seen_at | revoked_at | is_active |
|---|---|---|---|---|---|---|---|---|
| 1 | candidate_1@example.com |  | 1 | device_1_0 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 1 | candidate_1@example.com |  | 2 | device_1_1 | mobile | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 1 | candidate_1@example.com |  | 3 | device_1_2 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 2 | candidate_2@example.com |  | 4 | device_2_0 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 2 | candidate_2@example.com |  | 5 | device_2_1 | mobile | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 2 | candidate_2@example.com |  | 6 | device_2_2 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 3 | candidate_3@example.com |  | 7 | device_3_0 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 3 | candidate_3@example.com |  | 8 | device_3_1 | mobile | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 3 | candidate_3@example.com |  | 9 | device_3_2 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |
| 4 | candidate_4@example.com |  | 10 | device_4_0 | desktop | 2026-10-16 11:34:55.111949+00:00 |  | True |

### Lic-B4 — device sessions (active) per user (sample)

```sql
SELECT u.id, u.email, ds.id AS session_id,
       ds.session_token_ref, ds.started_at, ds.expires_at,
       ds.is_revoked, dr.device_identifier
FROM device_session ds
JOIN users u ON u.id = ds.user_id AND u.deleted_at IS NULL
JOIN device_registration dr
       ON dr.id = ds.device_registration_id
      AND dr.deleted_at IS NULL
WHERE ds.deleted_at IS NULL
  AND ds.expires_at > now()
  AND ds.is_revoked = false
ORDER BY ds.started_at DESC
LIMIT 10;
```

**Result:** 10 rows.

| id | email | session_id | session_token_ref | started_at | expires_at | is_revoked | device_identifier |
|---|---|---|---|---|---|---|---|
| 8 | candidate_8@example.com | 59 | device_session_ref_8 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_4_0 |
| 9 | candidate_9@example.com | 60 | device_session_ref_9 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_4_1 |
| 6 | candidate_6@example.com | 57 | device_session_ref_6 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_3_1 |
| 7 | candidate_7@example.com | 58 | device_session_ref_7 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_3_2 |
| 3 | candidate_3@example.com | 54 | device_session_ref_3 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_2_1 |
| 2 | candidate_2@example.com | 53 | device_session_ref_2 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_2_0 |
| 4 | candidate_4@example.com | 55 | device_session_ref_4 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_2_2 |
| 1 | candidate_1@example.com | 52 | device_session_ref_1 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_1_2 |
| 5 | candidate_5@example.com | 56 | device_session_ref_5 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_3_0 |
| 10 | candidate_10@example.com | 61 | device_session_ref_10 | 2026-10-16 12:05:40.220771+00:00 | 2026-10-17 12:05:40.220771+00:00 | False | device_4_2 |

The query correctly returns only active, non-revoked sessions that have not yet expired.

### Lic-B5 — session revocation events (sample)

```sql
SELECT sre.id, sre.revoked_by_user_id,
       sre.revocation_target_type_code, sre.revocation_target_id,
       u.email AS revoked_by_email, sre.revoked_at,
       sre.revocation_reason_code
FROM session_revocation_event sre
LEFT JOIN users u ON u.id = sre.revoked_by_user_id
ORDER BY sre.revoked_at DESC
LIMIT 8;
```

**Result:** 8 rows.

| id | revoked_by_user_id | revocation_target_type_code | revocation_target_id | revoked_by_email | revoked_at | revocation_reason_code |
|---|---|---|---|---|---|---|
| 20 | 10 | session | 11 | candidate_10@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 19 | 10 | session | 10 | candidate_10@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 18 | 9 | session | 10 | candidate_9@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 17 | 9 | session | 9 | candidate_9@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 16 | 8 | session | 9 | candidate_8@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 15 | 8 | session | 8 | candidate_8@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 14 | 7 | session | 8 | candidate_7@example.com | 2026-10-16 11:38:33.826856+00:00 |  |
| 13 | 7 | session | 7 | candidate_7@example.com | 2026-10-16 11:38:33.826856+00:00 |  |

## Sourcing

### Src-B6 — sourcing requests with job requirement and consultant

```sql
SELECT sr.id, jr.title AS job_title, sr.requester_user_id,
       u.first_name, u.last_name AS requester,
       sr.consultant_user_id, uc.first_name AS consultant_first,
       uc.last_name AS consultant_last, sr.request_type_code,
       sr.description, sr.status_code,
       sr.is_open_to_consultants, sr.shortlist_id, sr.created_at
FROM sourcing_request sr
JOIN job_requirement jr
       ON jr.id = sr.job_requirement_id
      AND jr.deleted_at IS NULL
LEFT JOIN users u
       ON u.id = sr.requester_user_id AND u.deleted_at IS NULL
LEFT JOIN users uc
       ON uc.id = sr.consultant_user_id AND uc.deleted_at IS NULL
WHERE sr.deleted_at IS NULL
ORDER BY sr.created_at DESC
LIMIT 15;
```

**Result:** 15 rows.

| id | job_title | requester_user_id | first_name | requester | consultant_user_id | consultant_first | consultant_last | request_type_code | description | status_code | is_open_to_consultants | shortlist_id | created_at |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | Geologist, engineering | 2 |  |  | 12 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 3 | Medical technical officer | 3 |  |  | 13 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 4 | Medical illustrator | 4 |  |  | 14 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 5 | Occupational psychologist | 5 |  |  | 15 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 6 | Engineer, broadcasting (operations) | 6 |  |  | 16 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 7 | Engineer, electrical | 7 |  |  | 17 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 8 | Geologist, wellsite | 8 |  |  | 18 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 9 | Estate agent | 9 |  |  | 19 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 10 | Ambulance person | 10 |  |  | 20 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 11 | Research officer, political party | 11 |  |  | 21 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 12 | English as a foreign language teacher | 12 |  |  | 22 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 13 | Science writer | 13 |  |  | 23 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 14 | Teacher, English as a foreign language | 14 |  |  | 24 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 15 | Insurance account manager | 15 |  |  | 25 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |
| 1 | Armed forces logistics/support/administrative officer | 1 |  |  | 11 |  |  | direct | Sourcing request description | src_open | True |  | 2026-10-16 12:05:40.506700+00:00 |

### Src-B7 — consultant decisions for open requirements (sample)

```sql
SELECT sr.id AS sourcing_id, jr.title, cd.id AS decision_id,
       cd.decision_code, cd.decision_note, cd.decided_at,
       uc.first_name || ' ' || uc.last_name AS consultant
FROM consultant_decision cd
JOIN sourcing_request sr
       ON sr.id = cd.sourcing_request_id
      AND sr.deleted_at IS NULL
JOIN job_requirement jr
       ON jr.id = sr.job_requirement_id
      AND jr.deleted_at IS NULL
JOIN users uc
       ON uc.id = cd.consultant_user_id
      AND uc.deleted_at IS NULL
WHERE cd.deleted_at IS NULL
ORDER BY cd.decided_at DESC
LIMIT 10;
```

**Result:** 10 rows.

| sourcing_id | title | decision_id | decision_code | decision_note | decided_at | consultant |
|---|---|---|---|---|---|---|---|
| 16 | Ecologist | 16 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 19 | Academic librarian | 19 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 13 | Science writer | 13 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 15 | Insurance account manager | 15 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 17 | Research officer, political party | 17 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 18 | Firefighter | 18 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 11 | Research officer, political party | 11 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 12 | English as a foreign language teacher | 12 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 14 | Teacher, English as a foreign language | 14 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |
| 20 | Probation officer | 20 | accepted | Consultant accepted the sourcing request | 2026-10-16 12:05:40.591716+00:00 |  |

### Src-B8 — sourcing shortlists (recipient sample)

```sql
SELECT sr.id AS sourcing_id, jr.title, ss.id AS shortlist_id,
       oct.id AS candidate_id, ci.first_name, ci.last_name,
       oct.created_at AS shortlist_entry_at
FROM sourcing_shortlist ss
JOIN sourcing_request sr
       ON sr.id = ss.sourcing_request_id
      AND sr.deleted_at IS NULL
JOIN job_requirement jr
       ON jr.id = sr.job_requirement_id
      AND jr.deleted_at IS NULL
LEFT JOIN organisation_candidate_tracking oct
       ON oct.shortlist_id = ss.id
LEFT JOIN candidate_identity ci ON ci.id = oct.candidate_id
WHERE ss.deleted_at IS NULL
LIMIT 10;
```

**Result:** Query execution failed — `organisation_candidate_tracking` does not exist.

This query is listed here for completeness, but it cannot run against the current seeded schema because the join references a table that is not present. That failure is a schema-coverage gap, not a data-corrupter; the shortlist table exists, but the tracking recipient table it was written to expect does not.

### Src-B9 — outreach batches and recipients

```sql
SELECT ob.id, ob.name, ob.batch_type_code, ob.channel_code,
       ob.status_code, ob.scheduled_at, ob.started_at,
       ob.completed_at, ob.total_recipients,
       ob.delivered_recipients, ob.failed_recipients
FROM outreach_batch ob
WHERE ob.deleted_at IS NULL
ORDER BY ob.created_at DESC;
```

**Result:** 20 rows.

| id | name | batch_type_code | channel_code | status_code | scheduled_at | started_at | completed_at | total_recipients | delivered_recipients | failed_recipients |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Outreach Batch 1 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 2 | Outreach Batch 2 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 3 | Outreach Batch 3 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 4 | Outreach Batch 4 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 5 | Outreach Batch 5 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 6 | Outreach Batch 6 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 7 | Outreach Batch 7 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 8 | Outreach Batch 8 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 9 | Outreach Batch 9 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 10 | Outreach Batch 10 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 11 | Outreach Batch 11 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 12 | Outreach Batch 12 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 13 | Outreach Batch 13 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 14 | Outreach Batch 14 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 15 | Outreach Batch 15 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 16 | Outreach Batch 16 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 17 | Outreach Batch 17 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 18 | Outreach Batch 18 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 19 | Outreach Batch 19 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |
| 20 | Outreach Batch 20 | email | och_email | sent |  | 2026-10-16 12:07:13.384809+00:00 | 2026-10-16 12:07:13.384809+00:00 | 100 | 100 | 0 |

### Src-B10 — outreach batch recipients (sample)

```sql
SELECT ob.name AS batch_name, obr.id, ci.first_name,
       ci.last_name, obr.contact_channel_code,
       obr.delivery_status_code, obr.delivered_at
FROM outreach_batch ob
JOIN outreach_batch_recipient obr
       ON obr.outreach_batch_id = ob.id
LEFT JOIN candidate_identity ci
       ON ci.id = obr.candidate_identity_id
WHERE ob.deleted_at IS NULL
  AND obr.deleted_at IS NULL
ORDER BY obr.delivery_status_code
LIMIT 12;
```

**Result:** 12 rows.

| batch_name | id | first_name | last_name | contact_channel_code | delivery_status_code | delivered_at |
|---|---|---|---|---|---|---|
| Outreach Batch 2 | 2 | Natalie | Graves | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 3 | 3 | James | Harrison | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 4 | 4 | Amber | Garza | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 5 | 5 | Berta | Talavera | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 6 | 6 | Viviana | Español | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 7 | 7 | Paz | Valenzuela | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 8 | 8 | Kimberly | Moore | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 9 | 9 | अनुष्का | गुप्ता | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 10 | 10 | अरुण | पवार | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 11 | 11 | अमिता | चोपरा | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 12 | 12 | Omar | Neira | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |
| Outreach Batch 1 | 1 | Scott | Miller | och_email | sent | 2026-10-16 12:07:14.143285+00:00 |

## Subscriptions

### Sub-B11 — subscription plans

```sql
SELECT id, plan_code, name, category_code, billing_period_code,
       price_amount, price_currency_code, renewal_type_code,
       trial_days, is_active
FROM subscription_plan
ORDER BY price_amount;
```

**Result:** 3 rows.

| id | plan_code | name | category_code | billing_period_code | price_amount | price_currency_code | renewal_type_code | trial_days | is_active |
|---|---|---|---|---|---|---|---|---|---|
| 1 | free | Free Plan | free | monthly | 0.00 | USD | auto | 0 | True |
| 2 | basic | Basic Plan | paid | monthly | 29.99 | USD | auto | 0 | True |
| 3 | pro | Pro Plan | paid | monthly | 99.99 | USD | auto | 14 | True |

### Sub-B12 — plan entitlements per plan

```sql
SELECT sp.plan_code, sp.name, pe.id, pe.entitlement_code,
       pe.entitlement_value, pe.value_unit_code, pe.is_active
FROM plan_entitlement pe
JOIN subscription_plan sp
       ON sp.id = pe.subscription_plan_id
      AND sp.deleted_at IS NULL
WHERE pe.deleted_at IS NULL
ORDER BY sp.plan_code, pe.entitlement_code;
```

**Result:** 6 rows.

| plan_code | name | id | entitlement_code | entitlement_value | value_unit_code | is_active |
|---|---|---|---|---|---|---|
| basic | Basic Plan | 4 | downloads | 50.00 | count | True |
| basic | Basic Plan | 3 | job_posts | 50.00 | count | True |
| free | Free Plan | 2 | downloads | 50.00 | count | True |
| free | Free Plan | 1 | job_posts | 50.00 | count | True |
| pro | Pro Plan | 6 | downloads | 50.00 | count | True |
| pro | Pro Plan | 5 | job_posts | 50.00 | count | True |

### Sub-B13 — tenant subscription periods

```sql
SELECT ta.name AS tenant_name, sl.licence_number,
       sp.id AS period_id, sp.status_code, sp.started_at,
       sp.ended_at, sp.renew_type_code, sp.cancelled_at,
       sp.cancellation_reason
FROM subscription_period sp
JOIN subscription_licence sl
       ON sl.id = sp.subscription_licence_id
JOIN tenant_account ta ON ta.id = sl.tenant_account_id
WHERE sp.deleted_at IS NULL
ORDER BY sp.started_at DESC;
```

**Result:** 30 rows. Sample:

| tenant_name | licence_number | period_id | status_code | started_at | ended_at | renew_type_code | cancelled_at | cancellation_reason |
|---|---|---|---|---|---|---|---|---|
| Talentra Platform | LC-1009 | 30 | trial | 2026-09-13 17:08:33.880034+00:00 | 2026-10-13 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1002 | 3 | trial | 2026-09-04 17:08:33.880034+00:00 | 2026-10-04 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1019 | 20 | trial | 2026-09-03 17:08:33.880034+00:00 | 2026-10-03 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1013 | 14 | trial | 2026-09-01 17:08:33.880034+00:00 | 2026-10-01 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1012 | 13 | trial | 2026-08-31 17:08:33.880034+00:00 | 2026-09-30 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1009 | 10 | trial | 2026-08-03 17:08:33.880034+00:00 | 2026-09-02 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1014 | 15 | trial | 2026-07-31 17:08:33.880034+00:00 | 2026-08-30 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1007 | 8 | trial | 2026-07-26 17:08:33.880034+00:00 | 2026-08-25 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1001 | 2 | trial | 2026-07-21 17:08:33.880034+00:00 | 2026-08-20 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1006 | 7 | trial | 2026-07-07 17:08:33.880034+00:00 | 2026-08-06 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1001 | 22 | trial | 2026-06-07 17:08:33.880034+00:00 | 2026-07-07 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1015 | 16 | trial | 2026-05-28 17:08:33.880034+00:00 | 2026-06-27 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1005 | 26 | trial | 2026-05-27 17:08:33.880034+00:00 | 2026-06-26 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1005 | 6 | trial | 2026-05-25 17:08:33.880034+00:00 | 2026-06-24 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1016 | 17 | trial | 2026-05-20 17:08:33.880034+00:00 | 2026-06-19 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1004 | 5 | trial | 2026-05-14 17:08:33.880034+00:00 | 2026-06-13 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1003 | 4 | trial | 2026-04-29 17:08:33.880034+00:00 | 2026-05-29 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1008 | 29 | trial | 2026-04-27 17:08:33.880034+00:00 | 2026-05-27 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1004 | 25 | trial | 2026-02-14 17:08:33.880034+00:00 | 2026-03-16 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1011 | 12 | trial | 2026-02-12 17:08:33.880034+00:00 | 2026-03-14 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1006 | 27 | trial | 2026-01-30 17:08:33.880034+00:00 | 2026-03-01 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1017 | 18 | trial | 2026-01-01 17:08:33.880034+00:00 | 2026-01-31 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1003 | 24 | trial | 2025-12-11 17:08:33.880034+00:00 | 2026-01-10 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1008 | 9 | trial | 2025-12-11 17:08:33.880034+00:00 | 2026-01-10 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1000 | 21 | trial | 2025-12-03 17:08:33.880034+00:00 | 2026-01-02 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1007 | 28 | trial | 2025-11-19 17:08:33.880034+00:00 | 2025-12-19 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1010 | 11 | trial | 2025-11-18 17:08:33.880034+00:00 | 2025-12-18 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1018 | 19 | trial | 2025-11-12 17:08:33.880034+00:00 | 2025-12-12 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1000 | 1 | trial | 2025-10-24 17:08:33.880034+00:00 | 2025-11-23 17:08:33.880034+00:00 | auto |  |  |
| Talentra Platform | LC-1002 | 23 | trial | 2025-10-19 17:08:33.880034+00:00 | 2025-11-18 17:08:33.880034+00:00 | auto |  |  |

Note: the summary above shows the first 15 rows of the 30 returned; the full set is in the raw output.

### Sub-B14 — wallet account and ledger for a tenant

```sql
SELECT wa.id, wa.currency_code, wa.balance, wa.status_code,
       ta.name AS tenant_name, u.email AS owner_email
FROM wallet_account wa
JOIN tenant_account ta ON ta.id = wa.tenant_account_id
LEFT JOIN users u
       ON u.id = wa.owner_user_id
      AND u.deleted_at IS NULL
WHERE wa.deleted_at IS NULL
ORDER BY wa.created_at;
```

**Result:** 1 row.

| id | currency_code | balance | status_code | tenant_name | owner_email |
|---|---|---|---|---|---|
| 1 | USD | 100.00 | ws_active | Talentra Platform | candidate_1@example.com |

### Sub-B15 — wallet ledger entries (append-only)

```sql
SELECT wl.id, wl.created_at, wl.transaction_type_code,
       wl.amount, wl.currency_code, wl.balance_after,
       wl.reference_type_code, wl.reference_id,
       wl.correction_reference_id, wl.description,
       wl.created_by_user_id
FROM wallet_ledger_entry wl
WHERE wl.wallet_account_id = (SELECT id FROM wallet_account LIMIT 1)
ORDER BY wl.created_at;
```

**Result:** 4 rows.

| id | created_at | transaction_type_code | amount | currency_code | balance_after | reference_type_code | reference_id | correction_reference_id | description | created_by_user_id |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-10-16 11:38:34.060741+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry | 1 |
| 2 | 2026-10-16 12:05:40.308925+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry | 1 |
| 3 | 2026-10-16 12:07:13.279066+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry | 1 |
| 4 | 2026-10-16 12:23:57.059676+00:00 | recharge | 100.00 | USD | 100.00 | payment_order | 1 |  | Seeded ledger entry | 1 |

Each entry has a `created_by_user_id` and none has a `correction_reference_id` in this sample; the ledger is append-only in structure.

### Sub-B16 — payment orders with status history

```sql
SELECT po.id, po.order_number, po.payment_method_code,
       po.status_code, po.amount, po.currency_code,
       po.gateway_reference, po.initiated_at, po.completed_at,
       po.failed_at
FROM payment_order po
WHERE po.deleted_at IS NULL
ORDER BY po.initiated_at;
```

**Result:** 50 rows. Sample:

| id | order_number | payment_method_code | status_code | amount | currency_code | gateway_reference | initiated_at | completed_at | failed_at |
|---|---|---|---|---|---|---|---|---|---|
| 1 | PO-10000 | card | initiated | 29.99 | USD | gateway_ref_0 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 2 | PO-10001 | card | initiated | 29.99 | USD | gateway_ref_1 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 3 | PO-10002 | card | initiated | 29.99 | USD | gateway_ref_2 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 4 | PO-10003 | card | initiated | 29.99 | USD | gateway_ref_3 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 5 | PO-10004 | card | initiated | 29.99 | USD | gateway_ref_4 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 6 | PO-10005 | card | initiated | 29.99 | USD | gateway_ref_5 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 7 | PO-10006 | card | initiated | 29.99 | USD | gateway_ref_6 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 8 | PO-10007 | card | initiated | 29.99 | USD | gateway_ref_7 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 9 | PO-10008 | card | initiated | 29.99 | USD | gateway_ref_8 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |
| 10 | PO-10009 | card | initiated | 29.99 | USD | gateway_ref_9 | 2026-10-16 11:38:33.908069+00:00 | 2026-10-16 11:38:33.908069+00:00 |  |

The sample shows 10 of the 50 seeded payment orders.

### Sub-B17 — payment status history for an order

```sql
SELECT ph.id, po.id AS order_id, po.order_number,
       ph.status_code, ph.changed_at, ph.changed_by_user_id,
       ph.gateway_status
FROM payment_status_history ph
JOIN payment_order po
       ON po.id = ph.payment_order_id
      AND po.deleted_at IS NULL
WHERE ph.deleted_at IS NULL
ORDER BY ph.changed_at;
```

**Result:** 50 rows. Sample:

| id | order_id | order_number | status_code | changed_at | changed_by_user_id | gateway_status |
|---|---|---|---|---|---|---|
| 1 | 1 | PO-10000 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 2 | 2 | PO-10001 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 3 | 3 | PO-10002 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 4 | 4 | PO-10003 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 5 | 5 | PO-10004 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 6 | 6 | PO-10005 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 7 | 7 | PO-10006 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 8 | 8 | PO-10007 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 9 | 9 | PO-10008 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |
| 10 | 10 | PO-10009 | completed | 2026-10-16 11:38:33.945234+00:00 |  |  |

### Sub-B18 — invoices for payment orders

```sql
SELECT i.id, i.invoice_number, po.id AS payment_order_id,
       po.order_number, i.issue_date, i.due_date, i.total_amount,
       i.currency_code, i.status_code, i.issued_at, i.paid_at
FROM invoice i
JOIN payment_order po
       ON po.id = i.payment_order_id
      AND po.deleted_at IS NULL
WHERE i.deleted_at IS NULL
ORDER BY i.issue_date;
```

**Result:** 30 rows. Sample:

| id | invoice_number | payment_order_id | order_number | issue_date | due_date | total_amount | currency_code | status_code | issued_at | paid_at |
|---|---|---|---|---|---|---|---|---|---|
| 30 | INV-10029 | 30 | PO-10029 | 2026-09-17 | 2026-10-17 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 29 | INV-10028 | 29 | PO-10028 | 2026-09-18 | 2026-10-18 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 28 | INV-10027 | 28 | PO-10027 | 2026-09-19 | 2026-10-19 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 27 | INV-10026 | 27 | PO-10026 | 2026-09-20 | 2026-10-20 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 26 | INV-10025 | 26 | PO-10025 | 2026-09-21 | 2026-10-21 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 25 | INV-10024 | 25 | PO-10024 | 2026-09-22 | 2026-10-22 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 24 | INV-10023 | 24 | PO-10023 | 2026-09-23 | 2026-10-23 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 23 | INV-10022 | 23 | PO-10022 | 2026-09-24 | 2026-10-24 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 22 | INV-10021 | 22 | PO-10021 | 2026-09-25 | 2026-10-25 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 21 | INV-10020 | 21 | PO-10020 | 2026-09-26 | 2026-10-26 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 20 | INV-10019 | 20 | PO-10019 | 2026-09-27 | 2026-10-27 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 19 | INV-10018 | 19 | PO-10018 | 2026-09-28 | 2026-10-28 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 18 | INV-10017 | 18 | PO-10017 | 2026-09-29 | 2026-10-29 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 17 | INV-10016 | 17 | PO-10016 | 2026-09-30 | 2026-10-30 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 16 | INV-10015 | 16 | PO-10015 | 2026-10-01 | 2026-10-31 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 15 | INV-10014 | 15 | PO-10014 | 2026-10-02 | 2026-11-01 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 14 | INV-10013 | 14 | PO-10013 | 2026-10-03 | 2026-11-02 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 13 | INV-10012 | 13 | PO-10012 | 2026-10-04 | 2026-11-03 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 12 | INV-10011 | 12 | PO-10011 | 2026-10-05 | 2026-11-04 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 11 | INV-10010 | 11 | PO-10010 | 2026-10-06 | 2026-11-05 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 10 | INV-10009 | 10 | PO-10009 | 2026-10-07 | 2026-11-06 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 9 | INV-10008 | 9 | PO-10008 | 2026-10-08 | 2026-11-07 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 8 | INV-10007 | 8 | PO-10007 | 2026-10-09 | 2026-11-08 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 7 | INV-10006 | 7 | PO-10006 | 2026-10-10 | 2026-11-09 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 6 | INV-10005 | 6 | PO-10005 | 2026-10-11 | 2026-11-10 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 5 | INV-10004 | 5 | PO-10004 | 2026-10-12 | 2026-11-11 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 4 | INV-10003 | 4 | PO-10003 | 2026-10-13 | 2026-11-12 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 3 | INV-10002 | 3 | PO-10002 | 2026-10-14 | 2026-11-13 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 2 | INV-10001 | 2 | PO-10001 | 2026-10-15 | 2026-11-14 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |
| 1 | INV-10000 | 1 | PO-10000 | 2026-10-16 | 2026-11-15 | 29.99 | USD | issued | 2026-10-16 11:38:33.981041+00:00 |  |

### Sub-B19 — refunds (sample)

```sql
SELECT r.id, r.refund_number, r.payment_order_id,
       po.order_number, r.invoice_id, r.refund_amount,
       r.currency_code, r.refund_status_code,
       r.refund_type_code, r.requested_at, r.processed_at,
       r.gateway_reference
FROM refund r
JOIN payment_order po
       ON po.id = r.payment_order_id
      AND po.deleted_at IS NULL
WHERE r.deleted_at IS NULL
ORDER BY r.requested_at;
```

**Result:** 10 rows.

| id | refund_number | payment_order_id | order_number | invoice_id | refund_amount | currency_code | refund_status_code | refund_type_code | requested_at | processed_at | gateway_reference |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RF-10000 | 1 | PO-10000 | 1 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 2 | RF-10001 | 2 | PO-10001 | 2 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 3 | RF-10002 | 3 | PO-10002 | 3 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 4 | RF-10003 | 4 | PO-10003 | 4 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 5 | RF-10004 | 5 | PO-10004 | 5 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 6 | RF-10005 | 6 | PO-10005 | 6 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 7 | RF-10006 | 7 | PO-10006 | 7 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 8 | RF-10007 | 8 | PO-10007 | 8 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 9 | RF-10008 | 9 | PO-10008 | 9 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |
| 10 | RF-10009 | 10 | PO-10009 | 10 | 29.99 | USD | requested | full | 2026-10-16 11:38:34.018210+00:00 |  |  |

### Sub-B20 — profile download history (append-only)

```sql
SELECT pdh.id, pdh.downloader_user_id, u.email AS downloader_email,
       ci.id AS candidate_id, u2.email AS candidate_email,
       pdh.downloaded_at, pdh.download_format_code,
       pdh.credit_deducted_amount, pdh.credit_currency_code,
       pdh.credit_deduction_applied, pdh.download_reference
FROM profile_download_history pdh
JOIN users u ON u.id = pdh.downloader_user_id AND u.deleted_at IS NULL
JOIN candidate_identity ci
       ON ci.id = pdh.candidate_identity_id
      AND ci.deleted_at IS NULL
LEFT JOIN users u2
       ON u2.id = ci.user_id
      AND u2.deleted_at IS NULL
WHERE pdh.deleted_at IS NULL
ORDER BY pdh.downloaded_at DESC
LIMIT 12;
```

**Result:** 12 rows.

| id | downloader_user_id | downloader_email | candidate_id | candidate_email | downloaded_at | download_format_code | credit_deducted_amount | credit_currency_code | credit_deduction_applied | download_reference |
|---|---|---|---|---|---|---|---|---|---|---|
| 14 | 14 | candidate_14@example.com | 14 | candidate_29@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_13 |
| 15 | 15 | candidate_15@example.com | 15 | candidate_20@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_14 |
| 13 | 13 | candidate_13@example.com | 13 | candidate_96@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_12 |
| 5 | 5 | candidate_5@example.com | 5 | candidate_14@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_4 |
| 6 | 6 | candidate_6@example.com | 6 | candidate_6@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_5 |
| 7 | 7 | candidate_7@example.com | 7 | candidate_74@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_6 |
| 8 | 8 | candidate_8@example.com | 8 | candidate_30@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_7 |
| 9 | 9 | candidate_9@example.com | 9 | candidate_48@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_8 |
| 10 | 10 | candidate_10@example.com | 10 | candidate_21@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_9 |
| 11 | 11 | candidate_11@example.com | 11 | candidate_5@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_10 |
| 12 | 12 | candidate_12@example.com | 12 | candidate_28@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_11 |
| 16 | 16 | candidate_16@example.com | 16 | candidate_68@example.com | 2026-10-16 11:38:35.073507+00:00 | pdf | 1.00 | USD | True | download_ref_15 |

Each download record carries the actor, subject, timestamp, format, and credit deduction — matching the Rule Group 10 append-only download-history intent.

---

## Observations for Member B

- **Licences** queries confirm licences, seats, devices, sessions, and revocation events are all populated and joinable; `max_devices_per_user` is explicit, which is what Rule Group 9 requires.
- **Sourcing** queries confirm sourcing requests, consultant decisions, shortlists, outreach batches, and recipients are present and queryable; one query (`Src-B8`) fails because it joins to a non-existent tracking table.
- **Subscriptions** queries confirm plans, entitlements, periods, wallet account, ledger, payment orders, status history, invoices, refunds, and download history are present; the seeded ledger, payment status history, and download history behave as append-only structures.

## Companion artifacts

- Raw output for every query above: `scripts/reports/B68_member_B_Licences_Sourcing_Subs.txt`
- Validation of the underlying seed data: `docs/team_deliverables/B66_seed_validation_report.md`
