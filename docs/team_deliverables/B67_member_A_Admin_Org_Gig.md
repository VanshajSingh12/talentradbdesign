# B67 — Module query results: Administration, Organisation, Gig

**Owner:** Member A
**Milestone:** 20 — Queries and validation across all modules
**Database:** `talentra` on `localhost:5431`
**Run time:** 2026-10-16T13:33:14.362658+00:00

Raw module output lives in `scripts/reports/B67_member_A_Admin_Org_Gig.txt`.

## Administration

### Admin-A1 — users active count by actor_type

```sql
SELECT actor_type_code, count(*) AS users
FROM users
WHERE deleted_at IS NULL
GROUP BY actor_type_code
ORDER BY users DESC;
```

**Result:** 1 row.

| actor_type_code | users |
|---|---|
| candidate | 1,010,000 |

The seeded user base is almost entirely candidates, which matches the Milestone 19 profile-scale intent.

### Admin-A2 — roles and active role assignments

```sql
SELECT rl.code, rl.name, count(ra.id) AS assignments
FROM role_lookup rl
LEFT JOIN role_assignment ra
       ON ra.role_id = rl.id
      AND ra.is_active = true
      AND ra.deleted_at IS NULL
WHERE rl.is_active = true
GROUP BY rl.id, rl.code, rl.name
ORDER BY rl.code;
```

**Result:** 8 rows.

| code | name | assignments |
|---|---|---|
| account_admin | Account Admin | 0 |
| admin | Administrator | 20 |
| candidate | Candidate | 1,009,774 |
| consultant | Consultant | 28 |
| employer | Employer | 212 |
| recruiter | Recruiter | 65 |
| super_admin | Super Admin | 0 |
| viewer | Viewer | 28 |

Most candidates have an active role assignment; admin-style roles are much smaller counts.

### Admin-A3 — role assignments per active user (sample)

```sql
SELECT u.id, u.email, u.first_name, u.last_name,
       rl.code AS role_code, ra.assigned_at
FROM users u
JOIN role_assignment ra
       ON ra.user_id = u.id
      AND ra.is_active = true
      AND ra.deleted_at IS NULL
JOIN role_lookup rl ON rl.id = ra.role_id
WHERE u.deleted_at IS NULL
ORDER BY u.id
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | email | first_name | last_name | role_code | assigned_at |
|---|---|---|---|---|---|
| 1 | user_0@example.com |  |  | admin | 2026-10-16 12:07:12.366619+00:00 |
| 28 | user_27@example.com |  |  | super_admin | 2026-10-16 12:07:13.044012+00:00 |
| 29 | user_28@example.com |  |  | employer | 2026-10-16 12:07:13.044012+00:00 |
| 55 | user_54@example.com |  |  | recruiter | 2026-10-16 12:07:13.471212+00:00 |
| 112 | user_111@example.com |  |  | consultant | 2026-10-16 12:07:14.030845+00:00 |
| 116 | user_115@example.com |  |  | viewer | 2026-10-16 12:07:14.030845+00:00 |
| 139 | user_138@example.com |  |  | account_admin | 2026-10-16 12:07:14.166716+00:00 |
| 213 | user_212@example.com |  |  | employer | 2026-10-16 12:07:14.242951+00:00 |
| 581 | user_580@example.com |  |  | employer | 2026-10-16 12:07:14.739209+00:00 |
| 10196 | user_10195@example.com |  |  | candidate | 2026-10-16 12:07:15.154326+00:00 |

The first seeded users carry administrative roles; candidate assignments dominate by volume.

### Admin-A4 — active sessions per user, last activity (sample)

```sql
SELECT u.id, u.email, sr.id AS session_id,
       sr.started_at, sr.last_activity_at, sr.expires_at,
       sr.is_revoked
FROM users u
JOIN session_record sr ON sr.user_id = u.id
WHERE u.deleted_at IS NULL AND sr.deleted_at IS NULL
ORDER BY sr.last_activity_at DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | email | session_id | started_at | last_activity_at | expires_at | is_revoked |
|---|---|---|---|---|---|---|
| 8 | user_7@example.com | 8 | 2026-10-16 12:07:14.202845+00:00 | 2026-10-16 12:07:14.202845+00:00 | 2026-10-17 12:07:14.202845+00:00 | False |
| 9 | user_8@example.com | 9 | 2026-10-16 12:07:14.319856+00:00 | 2026-10-16 12:07:14.319856+00:00 | 2026-10-17 12:07:14.319856+00:00 | False |
| 10 | user_9@example.com | 10 | 2026-10-16 12:07:14.430810+00:00 | 2026-10-16 12:07:14.430810+00:00 | 2026-10-17 12:07:14.430810+00:00 | False |
| 11 | user_10@example.com |  |  |  |  |  |
| 12 | user_11@example.com |  |  |  |  |  |
| 13 | user_12@example.com |  |  |  |  |  |
| 14 | user_13@example.com |  |  |  |  |  |
| 15 | user_14@example.com |  |  |  |  |  |
| 589 | user_588@example.com |  |  |  |  |  |
| 10170 | user_10169@example.com |  |  |  |  |  |

Only a small number of users have seeded sessions; the rest have none.

### Admin-A5 — credential verification state per seeded candidate user (sample)

```sql
SELECT u.id, u.email, cv.credential_type_code,
       cv.credential_status_code, cv.verified_at,
       cv.last_used_at, cv.failure_count, cv.locked_until
FROM users u
JOIN credential_verification cv ON cv.user_id = u.id
WHERE u.actor_type_code = 'candidate' AND u.deleted_at IS NULL
ORDER BY cv.credential_type_code
LIMIT 8;
```

**Result:** 8 rows.

| id | email | credential_type_code | credential_status_code | verified_at | last_used_at | failure_count | locked_until |
|---|---|---|---|---|---|---|---|
| 10196 | user_10195@example.com | email | verified | 2026-10-16 12:07:15.455381+00:00 |  | 0 |  |
| 30434 | user_30433@example.com | email | verified | 2026-10-16 12:07:16.293531+00:00 |  | 0 |  |
| 59127 | user_59126@example.com | email | verified | 2026-10-16 12:07:16.924263+00:00 |  | 0 |  |
| 87925 | user_87924@example.com | email | verified | 2026-10-16 12:07:17.526358+00:00 |  | 0 |  |
| 120375 | user_120374@example.com | email | verified | 2026-10-16 12:07:18.216955+00:00 |  | 0 |  |
| 151177 | user_151176@example.com | email | verified | 2026-10-16 12:07:18.904256+00:00 |  | 0 |  |
| 180389 | user_180388@example.com | email | verified | 2026-10-16 12:07:19.637783+00:00 |  | 0 |  |
| 209663 | user_209662@example.com | email | verified | 2026-10-16 12:07:20.257368+00:00 |  | 0 |  |

The credential verification state is present and active for the sampled candidates.

### Admin-A6 — credential recovery requests (sample)

```sql
SELECT u.id, u.email, cr.recovery_type_code,
       cr.requested_at, cr.used_at, cr.status_code
FROM users u
JOIN credential_recovery cr ON cr.user_id = u.id
WHERE u.deleted_at IS NULL
ORDER BY cr.requested_at DESC
LIMIT 8;
```

**Result:** 8 rows. Sample:

| id | email | recovery_type_code | requested_at | used_at | status_code |
|---|---|---|---|---|---|
| 10196 | user_10195@example.com | password_reset | 2026-10-16 12:07:15.455381+00:00 |  | pending |
| 30434 | user_30433@example.com | password_reset | 2026-10-16 12:07:16.293531+00:00 |  | pending |
| 59127 | user_59126@example.com | password_reset | 2026-10-16 12:07:16.924263+00:00 |  | pending |
| 87925 | user_87924@example.com | password_reset | 2026-10-16 12:07:17.526358+00:00 |  | pending |
| 120375 | user_120374@example.com | password_reset | 2026-10-16 12:07:18.216955+00:00 |  | pending |
| 151177 | user_151176@example.com | password_reset | 2026-10-16 12:07:18.904256+00:00 |  | pending |
| 180389 | user_180388@example.com | password_reset | 2026-10-16 12:07:19.637783+00:00 |  | pending |
| 209663 | user_209662@example.com | password_reset | 2026-10-16 12:07:20.257368+00:00 |  | pending |

### Admin-A7 — consent records (sample)

```sql
SELECT u.id, u.email, cr.consent_type_code,
       cr.consent_value_code, cr.recorded_at
FROM users u
JOIN consent_record cr ON cr.user_id = u.id
WHERE u.deleted_at IS NULL
ORDER BY cr.recorded_at DESC
LIMIT 8;
```

**Result:** 8 rows. Sample:

| id | email | consent_type_code | consent_value_code | recorded_at |
|---|---|---|---|---|
| 10196 | user_10195@example.com | marketing_opt_in | granted | 2026-10-16 12:07:15.455381+00:00 |
| 10196 | user_10195@example.com | terms_acceptance | granted | 2026-10-16 12:07:15.455381+00:00 |
| 30434 | user_30433@example.com | marketing_opt_in | granted | 2026-10-16 12:07:16.293531+00:00 |
| 30434 | user_30433@example.com | terms_acceptance | granted | 2026-10-16 12:07:16.293531+00:00 |
| 59127 | user_59126@example.com | marketing_opt_in | granted | 2026-10-16 12:07:16.924263+00:00 |
| 59127 | user_59126@example.com | terms_acceptance | granted | 2026-10-16 12:07:16.924263+00:00 |
| 87925 | user_87924@example.com | marketing_opt_in | granted | 2026-10-16 12:07:17.526358+00:00 |
| 87925 | user_87924@example.com | terms_acceptance | granted | 2026-10-16 12:07:17.526358+00:00 |

### Admin-A8 — audit events (sample with actor role)

```sql
SELECT a.id, a.actor_user_id, a.event_type_code,
       a.target_table, a.target_id,
       u.email AS actor_email, a.occurred_at
FROM audit_event a
LEFT JOIN users u ON u.id = a.actor_user_id
ORDER BY a.occurred_at DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | actor_user_id | event_type_code | target_table | target_id | actor_email | occurred_at |
|---|---|---|---|---|---|---|
| 300 | 28 | login | credential_verification | 28 | user_27@example.com | 2026-10-16 12:07:13.044012+00:00 |
| 299 | 55 | login | session_record | 55 | user_54@example.com | 2026-10-16 12:07:13.471212+00:00 |
| 298 | 112 | login | credential_verification | 112 | user_111@example.com | 2026-10-16 12:07:14.030845+00:00 |
| 297 | 116 | login | credential_verification | 116 | user_115@example.com | 2026-10-16 12:07:14.030845+00:00 |
| 296 | 139 | login | credential_verification | 139 | user_138@example.com | 2026-10-16 12:07:14.166716+00:00 |
| 295 | 213 | login | credential_verification | 213 | user_212@example.com | 2026-10-16 12:07:14.242951+00:00 |
| 294 | 581 | login | credential_verification | 581 | user_580@example.com | 2026-10-16 12:07:14.739209+00:00 |
| 293 | 10170 | login | credential_verification | 10170 | user_10169@example.com | 2026-10-16 12:07:15.154326+00:00 |
| 292 | 10171 | login | credential_verification | 10171 | user_10170@example.com | 2026-10-16 12:07:15.154326+00:00 |
| 291 | 10172 | login | credential_verification | 10172 | user_10171@example.com | 2026-10-16 12:07:15.154326+00:00 |

### Admin-A9 — blocking list (active entries)

```sql
SELECT b.id, b.blocker_user_id, b.blocked_party_type_code,
       b.blocked_party_id, b.blocked_at, b.is_active
FROM blocking_list b
LEFT JOIN users rp ON rp.id = b.blocker_user_id
WHERE b.is_active = true AND b.deleted_at IS NULL
ORDER BY b.blocked_at DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | blocker_user_id | blocked_party_type_code | blocked_party_id | blocked_at | is_active |
|---|---|---|---|---|---|
| 50 | 1 | candidate | 1 | 2026-10-16 12:07:12.366619+00:00 | True |
| 49 | 1 | candidate | 2 | 2026-10-16 12:07:12.366619+00:00 | True |
| 48 | 1 | candidate | 3 | 2026-10-16 12:07:12.366619+00:00 | True |
| 47 | 1 | candidate | 4 | 2026-10-16 12:07:12.366619+00:00 | True |
| 46 | 1 | candidate | 5 | 2026-10-16 12:07:12.366619+00:00 | True |
| 45 | 1 | candidate | 6 | 2026-10-16 12:07:12.366619+00:00 | True |
| 44 | 1 | candidate | 7 | 2026-10-16 12:07:12.366619+00:00 | True |
| 43 | 1 | candidate | 8 | 2026-10-16 12:07:12.366619+00:00 | True |
| 42 | 1 | candidate | 9 | 2026-10-16 12:07:12.366619+00:00 | True |
| 41 | 1 | candidate | 10 | 2026-10-16 12:07:12.366619+00:00 | True |

## Organisation

### Org-A10 — tenant accounts

```sql
SELECT id, account_type_code, name, status_code,
       is_active, created_at
FROM tenant_account
ORDER BY created_at DESC;
```

**Result:** 1 row.

| id | account_type_code | name | status_code | is_active | created_at |
|---|---|---|---|---|---|
| 1 | tenant | Talentra Platform | active | True | 2026-10-16 12:07:12.225436+00:00 |

The seed uses a single tenant for simplicity.

### Org-A11 — employer organisations (sample) with verification status

```sql
SELECT eo.id, eo.company_name, eo.legal_name, eo.industry_name,
       eo.type_code, eo.is_verified, eo.verification_status_code,
       eo.mapped_recruiter_count, eo.city, eo.state, eo.country,
       eo.created_at
FROM employer_organisation eo
WHERE eo.deleted_at IS NULL
ORDER BY eo.company_name
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | company_name | legal_name | industry_name | type_code | is_verified | verification_status_code | mapped_recruiter_count | city | state | country | created_at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Acme Corp | Acme Corp Ltd | Technology | enterprise | True | verified | 1 | Sydney | New South Wales | Australia | 2026-10-16 12:07:12.366619+00:00 |
| 2 | Beta Industries | Beta Industries Pty Ltd | Healthcare | mid_market | False | pending | 1 | Melbourne | Victoria | Australia | 2026-10-16 12:07:12.366619+00:00 |
| 3 | Gamma Solutions | Gamma Solutions Pty Ltd | Finance | enterprise | False | pending | 1 | Brisbane | Queensland | Australia | 2026-10-16 12:07:12.366619+00:00 |
| 4 | Delta Retail | Delta Retail Pty Ltd | Retail | sme | True | verified | 1 | Perth | Western Australia | Australia | 2026-10-16 12:07:12.366619+00:00 |
| 5 | Epsilon Logistics | Epsilon Logistics Pty Ltd | Logistics | sme | False | pending | 1 | Adelaide | South Australia | Australia | 2026-10-16 12:07:12.366619+00:00 |
| 6 | Zeta Manufacturing | Zeta Manufacturing Pty Ltd | Manufacturing | enterprise | True | verified | 1 | Auckland |  | New Zealand | 2026-10-16 12:07:12.366619+00:00 |
| 7 | Eta Construction | Eta Construction Pty Ltd | Construction | sme | False | pending | 1 | Christchurch |  | New Zealand | 2026-10-16 12:07:12.366619+00:00 |
| 8 | Theta Energy | Theta Energy Ltd | Energy | enterprise | False | pending | 1 | Wellington |  | New Zealand | 2026-10-16 12:07:12.366619+00:00 |
| 9 | Iota Hospitality | Iota Hospitality Ltd | Hospitality | sme | False | pending | 1 | Brisbane | Queensland | Australia | 2026-10-16 12:07:12.366619+00:00 |
| 10 | Kappa Media | Kappa Media Pty Ltd | Media | sme | False | pending | 1 | Melbourne | Victoria | Australia | 2026-10-16 12:07:12.366619+00:00 |

### Org-A12 — company locations per employer (sample)

```sql
SELECT eo.company_name, cl.id, cl.location_name,
       cl.city, cl.country, cl.is_head_office, cl.is_active
FROM employer_organisation eo
JOIN company_location cl
       ON cl.employer_organisation_id = eo.id
      AND cl.deleted_at IS NULL
WHERE eo.deleted_at IS NULL
ORDER BY eo.company_name, cl.id
LIMIT 15;
```

**Result:** 15 rows. Sample:

| company_name | id | location_name | city | country | is_head_office | is_active |
|---|---|---|---|---|---|---|
| Acme Corp | 1 |  | Sydney | Australia | True | True |
| Acme Corp | 2 | Sydney Branch Office | Sydney | Australia | False | True |
| Beta Industries | 3 |  | Melbourne | Australia | True | True |
| Beta Industries | 4 | Melbourne Branch Office | Melbourne | Australia | False | True |
| Gamma Solutions | 5 |  | Brisbane | Australia | True | True |
| Gamma Solutions | 6 | Brisbane Branch Office | Brisbane | Australia | False | True |
| Delta Retail | 7 |  | Perth | Australia | True | True |
| Delta Retail | 8 | Perth Branch Office | Perth | Australia | False | True |
| Epsilon Logistics | 9 |  | Adelaide | Australia | True | True |
| Epsilon Logistics | 10 | Adelaide Branch Office | Adelaide | Australia | False | True |
| Zeta Manufacturing | 11 |  | Auckland | New Zealand | True | True |
| Zeta Manufacturing | 12 | Auckland Branch Office | Auckland | New Zealand | False | True |
| Eta Construction | 13 |  | Christchurch | New Zealand | True | True |
| Eta Construction | 14 | Christchurch Branch Office | Christchurch | New Zealand | False | True |
| Theta Energy | 15 |  | Wellington | New Zealand | True | True |

### Org-A13 — tax registration identifiers (sample)

```sql
SELECT eo.company_name, tri.id, tri.country_code,
       tri.identifier_type_code, tri.identifier_value,
       tri.is_primary, tri.verification_status_code,
       tri.valid_from, tri.valid_to
FROM employer_organisation eo
JOIN tax_registration_identifier tri
       ON tri.employer_organisation_id = eo.id
      AND tri.deleted_at IS NULL
WHERE eo.deleted_at IS NULL
ORDER BY eo.company_name
LIMIT 10;
```

**Result:** 10 rows. Sample:

| company_name | id | country_code | identifier_type_code | identifier_value | is_primary | verification_status_code | valid_from | valid_to |
|---|---|---|---|---|---|---|---|---|
| Acme Corp | 1 | AU | ABN | 12345678901 | True | verified | 2025-01-01 |  |
| Beta Industries | 2 | AU | ACN | 12345678901 | True | pending | 2025-01-01 |  |
| Gamma Solutions | 3 | AU | ABN | 12345678901 | True | pending | 2025-01-01 |  |
| Delta Retail | 4 | AU | ABN | 12345678901 | True | verified | 2025-01-01 |  |
| Epsilon Logistics | 5 | AU | ABN | 12345678901 | True | pending | 2025-01-01 |  |
| Zeta Manufacturing | 6 | NZ | GST | 123456789.0 | True | verified | 2025-01-01 |  |
| Eta Construction | 7 | NZ | GST | 123456789.0 | True | pending | 2025-01-01 |  |
| Theta Energy | 8 | NZ | GST | 123456789.0 | True | pending | 2025-01-01 |  |
| Iota Hospitality | 9 | AU | ABN | 12345678901 | True | pending | 2025-01-01 |  |
| Kappa Media | 10 | AU | ABN | 12345678901 | True | pending | 2025-01-01 |  |

### Org-A14 — verification status records (sample)

```sql
SELECT eo.company_name, vsr.verification_type_code,
       vsr.verification_status_code, vsr.verified_at,
       vsr.outcome_notes
FROM employer_organisation eo
JOIN verification_status_record vsr
       ON vsr.employer_organisation_id = eo.id
      AND vsr.deleted_at IS NULL
WHERE eo.deleted_at IS NULL
ORDER BY vsr.verified_at DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| company_name | verification_type_code | verification_status_code | verified_at | outcome_notes |
|---|---|---|---|---|
| Kappa Media | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Iota Hospitality | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Theta Energy | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Eta Construction | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Zeta Manufacturing | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Delta Retail | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Epsilon Logistics | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Gamma Solutions | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Beta Industries | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |
| Acme Corp | business_verification | verified | 2026-10-16 12:07:12.366619+00:00 |  |

### Org-A15 — recruiter mappings (effective-dated) sample

```sql
SELECT eo.company_name, u.first_name, u.last_name,
       rm.mapping_type_code, rm.is_primary, rm.is_active,
       rm.effective_start, rm.effective_end
FROM recruiter_mapping rm
JOIN employer_organisation eo
       ON eo.id = rm.employer_organisation_id
      AND eo.deleted_at IS NULL
JOIN users u
       ON u.id = rm.recruiter_user_id
      AND u.deleted_at IS NULL
WHERE rm.deleted_at IS NULL
ORDER BY eo.company_name, rm.is_primary DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| company_name | first_name | last_name | mapping_type_code | is_primary | is_active | effective_start | effective_end |
|---|---|---|---|---|---|---|---|
| Acme Corp |  |  | recruiter | True | True | 2026-01-01 |  |
| Acme Corp |  |  | recruiter | False | True | 2026-01-01 |  |
| Beta Industries |  |  | recruiter | True | True | 2026-01-01 |  |
| Beta Industries |  |  | recruiter | False | True | 2026-01-01 |  |
| Gamma Solutions |  |  | recruiter | True | True | 2026-01-01 |  |
| Gamma Solutions |  |  | recruiter | False | True | 2026-01-01 |  |
| Delta Retail |  |  | recruiter | True | True | 2026-01-01 |  |
| Delta Retail |  |  | recruiter | False | True | 2026-01-01 |  |
| Epsilon Logistics |  |  | recruiter | True | True | 2026-01-01 |  |
| Epsilon Logistics |  |  | recruiter | False | True | 2026-01-01 |  |

The recruiter names are empty in this seed, but the mapping structure (primary/recruiter, effective-dated) is present.

### Org-A16 — organisation hierarchy (active)

```sql
SELECT eo_parent.company_name AS parent,
       eo_child.company_name AS child,
       oh.relationship_type_code, oh.effective_start,
       oh.effective_end, oh.is_active
FROM organisation_hierarchy oh
JOIN employer_organisation eo_parent
       ON eo_parent.id = oh.parent_organisation_id
JOIN employer_organisation eo_child
       ON eo_child.id = oh.child_organisation_id
WHERE oh.is_active = true AND oh.deleted_at IS NULL
LIMIT 10;
```

**Result:** 10 rows. Sample:

| parent | child | relationship_type_code | effective_start | effective_end | is_active |
|---|---|---|---|---|---|
| Acme Corp | Acme Corp Sub 1 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 2 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 3 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 4 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 5 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 6 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 7 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 8 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 9 | subsidiary | 2025-01-01 |  | True |
| Acme Corp | Acme Corp Sub 10 | subsidiary | 2025-01-01 |  | True |

### Org-A17 — account administrators (sample)

```sql
SELECT a.id, u.email, u.first_name, u.last_name,
       ta.name AS tenant_name, a.admin_role_code,
       a.is_primary, a.is_active
FROM account_administrator a
JOIN tenant_account ta ON ta.id = a.tenant_account_id
JOIN users u
       ON u.id = a.administrator_user_id
      AND u.deleted_at IS NULL
ORDER BY a.id
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | email | first_name | last_name | tenant_name | admin_role_code | is_primary | is_active |
|---|---|---|---|---|---|---|---|
| 1 | user_0@example.com |  |  | Talentra Platform | admin | True | True |
| 2 | user_1@example.com |  |  | Talentra Platform | admin | False | True |
| 3 | user_2@example.com |  |  | Talentra Platform | admin | False | True |
| 4 | user_3@example.com |  |  | Talentra Platform | admin | False | True |
| 5 | user_4@example.com |  |  | Talentra Platform | admin | False | True |
| 6 | user_5@example.com |  |  | Talentra Platform | admin | False | True |
| 7 | user_6@example.com |  |  | Talentra Platform | admin | False | True |
| 8 | user_7@example.com |  |  | Talentra Platform | admin | False | True |
| 9 | user_8@example.com |  |  | Talentra Platform | admin | False | True |
| 10 | user_9@example.com |  |  | Talentra Platform | admin | False | True |

## Gig marketplace

### Gig-A18 — gig requests with job requirement title and pricing

```sql
SELECT jr.title, grd.id, grd.pricing_model_code,
       grd.fixed_price, grd.fixed_price_currency_code,
       grd.rate_per_time_unit, grd.rate_time_unit_code,
       grd.fulfillment_status_code, grd.window_start_at,
       grd.window_end_at, grd.apply_by_at
FROM gig_request_detail grd
JOIN job_requirement jr
       ON jr.id = grd.job_requirement_id
      AND jr.deleted_at IS NULL
ORDER BY grd.created_at DESC
LIMIT 12;
```

**Result:** 12 rows. Sample:

| title | id | pricing_model_code | fixed_price | fixed_price_currency_code | rate_per_time_unit | rate_time_unit_code | fulfillment_status_code | window_start_at | window_end_at | apply_by_at |
|---|---|---|---|---|---|---|---|---|---|---|
| Senior Data Engineer | 500 | fixed | 10000.00 | USD |  |  | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Senior Backend Engineer | 499 | hourly |  |  | 100.00 | hour | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Senior Frontend Engineer | 498 | fixed | 8000.00 | USD |  |  | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Senior Fullstack Engineer | 497 | hourly |  |  | 120.00 | hour | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Data Analyst | 496 | fixed | 5000.00 | USD |  |  | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Data Scientist | 495 | hourly |  |  | 150.00 | hour | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| DevOps Engineer | 494 | fixed | 12000.00 | USD |  |  | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Cloud Architect | 493 | hourly |  |  | 200.00 | hour | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Cybersecurity Analyst | 492 | fixed | 7000.00 | USD |  |  | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| IT Support Specialist | 491 | hourly |  |  | 60.00 | hour | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Network Engineer | 490 | fixed | 9000.00 | USD |  |  | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |
| Systems Administrator | 489 | hourly |  |  | 80.00 | hour | fulfilled | 2026-10-01 00:00:00+00:00 | 2026-10-31 00:00:00+00:00 | 2026-10-15 00:00:00+00:00 |

### Gig-A19 — gig worker profiles with availability (sample)

```sql
SELECT gwp.id, gwp.worker_name, gwp.headline,
       gwp.service_offerings, gwp.charge_rate_min,
       gwp.charge_currency_code, gwp.status_code,
       gwp.is_available, gwa.availability_start_at,
       gwa.availability_end_at, gwa.is_recurring
FROM gig_worker_profile gwp
LEFT JOIN gig_worker_availability gwa
       ON gwa.gig_worker_profile_id = gwp.id
      AND gwa.is_active = true
      AND gwa.deleted_at IS NULL
WHERE gwp.deleted_at IS NULL
ORDER BY case when gwp.is_available then 0 else 1 end,
         gwp.created_at DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| id | worker_name | headline | service_offerings | charge_rate_min | charge_currency_code | status_code | is_available | availability_start_at | availability_end_at | is_recurring |
|---|---|---|---|---|---|---|---|---|---|---|
| 300 | Gig Worker 300 | Gig Worker 300 |  |  |  |  | False |  |  |  |
| 299 | Gig Worker 299 | Gig Worker 299 |  |  |  |  | False |  |  |  |
| 298 | Gig Worker 298 | Gig Worker 298 |  |  |  |  | False |  |  |  |
| 297 | Gig Worker 297 | Gig Worker 297 |  |  |  |  | False |  |  |  |
| 296 | Gig Worker 296 | Gig Worker 296 |  |  |  |  | False |  |  |  |
| 295 | Gig Worker 295 | Gig Worker 295 |  |  |  |  | False |  |  |  |
| 294 | Gig Worker 294 | Gig Worker 294 |  |  |  |  | False |  |  |  |
| 293 | Gig Worker 293 | Gig Worker 293 |  |  |  |  | False |  |  |  |
| 292 | Gig Worker 292 | Gig Worker 292 |  |  |  |  | False |  |  |  |
| 291 | Gig Worker 291 | Gig Worker 291 |  |  |  |  | False |  |  |  |

The worker profile names and availability are empty in this seed; the structure is present and queryable.

### Gig-A20 — gig applications for a gig request detail (sample)

```sql
SELECT gwd.job_requirement_id, jr.title AS job_title,
       ga.id AS gig_application_id, gwp.worker_name,
       ga.bid_amount, ga.bid_currency_code,
       ga.application_status_code, ga.applied_at,
       ga.reviewed_at, ga.rejection_reason
FROM gig_application ga
JOIN gig_request_detail gwd ON gwd.id = ga.gig_request_detail_id
JOIN job_requirement jr
       ON jr.id = gwd.job_requirement_id
      AND jr.deleted_at IS NULL
JOIN gig_worker_profile gwp
       ON gwp.id = ga.gig_worker_profile_id
      AND gwp.deleted_at IS NULL
WHERE ga.deleted_at IS NULL
ORDER BY ga.applied_at DESC
LIMIT 10;
```

**Result:** 10 rows. Sample:

| job_requirement_id | job_title | gig_application_id | worker_name | bid_amount | bid_currency_code | application_status_code | applied_at | reviewed_at | rejection_reason |
|---|---|---|---|---|---|---|---|---|---|
| 500 | Senior Data Engineer | 2000 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1999 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1998 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1997 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1996 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1995 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1994 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1993 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1992 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |
| 500 | Senior Data Engineer | 1991 |  | 5000.00 | USD | accepted | 2026-10-16 12:07:17.795424+00:00 | 2026-10-16 12:07:17.795424+00:00 |  |

Bid amounts are seeded; worker names are empty.

### Gig-A21 — gig assignments with handoffs and earnings

```sql
SELECT ga.gig_application_id, gwd.job_requirement_id,
       jr.title, gwp.worker_name, gaz.id AS assignment_id,
       gaz.assigned_at, gaz.assignment_status_code,
       ghr.handoff_system_code, ghr.external_reference,
       ghr.handoff_status_code, ger.earnings_type_code,
       ger.earnings_amount, ger.earnings_currency_code
FROM gig_assignment gaz
JOIN gig_application ga
       ON ga.id = gaz.gig_application_id
      AND ga.deleted_at IS NULL
JOIN gig_request_detail gwd ON gwd.id = ga.gig_request_detail_id
JOIN job_requirement jr
       ON jr.id = gwd.job_requirement_id
      AND jr.deleted_at IS NULL
JOIN gig_worker_profile gwp
       ON gwp.id = ga.gig_worker_profile_id
      AND gwp.deleted_at IS NULL
LEFT JOIN gig_handoff_reference ghr
       ON ghr.gig_assignment_id = gaz.id
LEFT JOIN gig_earnings_reference ger
       ON ger.gig_assignment_id = gaz.id
WHERE gaz.deleted_at IS NULL
LIMIT 8;
```

**Result:** 8 rows. Sample:

| gig_application_id | job_requirement_id | title | worker_name | assignment_id | assigned_at | assignment_status_code | handoff_system_code | external_reference | handoff_status_code | earnings_type_code | earnings_amount | earnings_currency_code |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2000 | 500 | Senior Data Engineer |  | 200 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1999 | 500 | Senior Data Engineer |  | 199 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1998 | 500 | Senior Data Engineer |  | 198 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1997 | 500 | Senior Data Engineer |  | 197 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1996 | 500 | Senior Data Engineer |  | 196 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1995 | 500 | Senior Data Engineer |  | 195 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1994 | 500 | Senior Data Engineer |  | 194 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |
| 1993 | 500 | Senior Data Engineer |  | 193 | 2026-10-16 12:07:17.795424+00:00 | completed |  |  |  | milestone | 10000.00 | USD |

### Gig-A22 — gig ratings (sample)

```sql
SELECT gwp.worker_name, gaz.assignment_id, gr.id,
       gr.rating_by_user_id, gr.rating_value,
       gr.rating_text, gr.rated_at
FROM gig_rating gr
JOIN gig_assignment gaz
       ON gaz.id = gr.gig_assignment_id
      AND gaz.deleted_at IS NULL
JOIN gig_application ga
       ON ga.id = gaz.gig_application_id
      AND ga.deleted_at IS NULL
JOIN gig_worker_profile gwp
       ON gwp.id = ga.gig_worker_profile_id
      AND gwp.deleted_at IS NULL
ORDER BY gr.rated_at DESC
LIMIT 8;
```

**Result:** 8 rows. Sample:

| worker_name | assignment_id | id | rating_by_user_id | rating_value | rating_text | rated_at |
|---|---|---|---|---|---|---|
|  | 200 | 50 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 199 | 49 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 198 | 48 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 197 | 47 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 196 | 46 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 195 | 45 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 194 | 44 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |
|  | 193 | 43 | 1 | 5.0 |  | 2026-10-16 12:07:17.795424+00:00 |

### Gig-A23 — gig favourites / blacklist (sample)

```sql
SELECT 'favourite' AS type, gf.id, gf.requester_user_id,
       gwp.worker_name, gf.favourited_at
FROM gig_favourite gf
JOIN gig_worker_profile gwp
       ON gwp.id = gf.gig_worker_profile_id
      AND gwp.deleted_at IS NULL
UNION ALL
SELECT 'blacklist', gb.id, gb.requester_user_id,
       gwp.worker_name, gb.blacklisted_at
FROM gig_blacklist gb
JOIN gig_worker_profile gwp
       ON gwp.id = gb.gig_worker_profile_id
      AND gwp.deleted_at IS NULL
ORDER BY type, id
LIMIT 10;
```

**Result:** 10 rows.

| type | id | requester_user_id | worker_name | favourited_at / blacklisted_at |
|---|---|---|---|---|
| favourite | 50 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 49 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 48 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 47 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 46 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 45 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 44 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 43 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 42 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |
| favourite | 41 | 1 |  | 2026-10-16 12:07:12.366619+00:00 |

---

## Observations for Member A

- **Administration** queries confirm the expected role distribution, sessions, credentials, consent, audit, and blocking structures are present and queryable; only a small subset of users have sessions or audit detail seeded.
- **Organisation** queries confirm tenant, employers, locations, tax identifiers, verification records, recruiter mappings, hierarchy, and account administrators are all populated and joinable.
- **Gig marketplace** queries confirm gig requests, worker profiles, applications, assignments, handoffs, earnings, ratings, favourites, and blacklists are present; several descriptive columns are empty placeholders, but the relationships hold.

## Companion artifacts

- Raw output with all row counts and sample rows: `scripts/reports/B67_member_A_Admin_Org_Gig.txt`
- Validation of the underlying seed data: `docs/team_deliverables/B66_seed_validation_report.md`
