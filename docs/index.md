# Talentra Database Design — Documentation index

## Repository layout

```text
ddl/                    # executable schema + documentation artifact
  01_master_data.sql            # Master data (Section 4 Tier 1 + unique skill/taxonomy/tag extensions)
  02_profile.sql                # Candidate profile (Tier 1 + all Tier 2 + unique affinity/tag extensions)
  03_jobs_applications.sql      # Jobs & applications (Tier 1 + Tier 2 + unique tagging/denial-code extensions)
  04_administration.sql         # Users, credentials, roles/permissions, sessions, consent, audit, blocking
  05_organisation.sql           # Tenant account, employer org, hierarchy, recruiter mapping, new classification/intel
  06_gig_marketplace.sql        # Gig marketplace (shared-core job model + gig-specific extensions)
  07_licences.sql               # Licences, seats, devices, sessions (Rule Group 9)
  08_sourcing.sql               # Sourcing requests, consultant decisions, shortlists, outreach
  09_subscriptions.sql          # Subscriptions, wallet, payments, invoice/refund, download history (Rule Group 10)
  10_notifications.sql          # Notifications, preferences, community, support, FAQ
  11_analytics.sql              # Star-schema analytics dims/facts/aggregates
  12_tier3_stretch.sql          # Optional Tier 3 stretch (salary benchmarks, company ratings, trending, dashboard, feature flags)
  99_documentation.sql          # Executable documentation artifact (decisions + Section 6 + compliance register + milestone map)
  seed/generate_seed.py         # Milestone 19 laptop-scale seed generator
docs/                   # human-readable documentation
  README.md              # this file
  decisions.md           # design decisions in prose + reasons
  compliance_register.md   # Rule Group 1-10 compliance register (paraphrased from 99_documentation.sql)
  integration_boundaries.md # Section 6 integration boundaries
  module_index.md        # module-by-module purpose + key entities + relationships + rules applied + unique differentiators
  query_catalog.md       # representative queries the schema is meant to answer
  reserved_identifiers.md # why reserved-name checks were done and what was found
  wallet_table_note.md   # why the `wallet` table name is acceptable in this design
tools/checks/           # validation/conversion scripts
  check_reserved.py     # scans ddl/*.sql for PostgreSQL reserved-identifier usage
  inject_map.py          # injects the milestone-order context-menu map into 99_documentation.sql

After running inject_map.py once, the milestone-order map was appended to 99_documentation.sql. If you re-run inject_map.py later, verify that it does not duplicate the map block before committing.
```

## Why `.sql` is used for documentation here

The file `ddl/99_documentation.sql` is the single source of truth for:

- DB-provider decision reason (B1, PostgreSQL chosen over MySQL)
- gig model decision (shared core job + application model) and its justification
- credential store decision (best-practice industry choice: separate credential_verification + credential_recovery)
- Tier 2 scope decision (all included, no omissions)
- Tier 3 scope decision (all five included as a separate, clearly labelled module)
- Section 6 integration boundaries table
- Rule Group 1-10 compliance register (deviation + reason per rule)
- milestone-order entities → relationships → columns context menu (`schema_map_milestone_order`)

It is written as **runnable SQL comments plus light DDL** for one reason:

1. **It travels with the schema.** The same artifact that defines the tables can also carry the rationale, the compliance register, and the integration boundaries. That avoids splitting the source of truth between a doc file and a schema file that can drift apart.
2. **Enterprise reviewers can read it in their SQL tool.** DBA/tech-review workflows in a hackathon context often end up inside SQL editors or migration tools. A `.sql` file with structured comment blocks is directly readable there, without requiring a separate markdown viewer.
3. **It stays mechanically checkable.** Reserved-word scans, naming scans, and FK-target checks can be run against the same files that hold the decisions. If docs were only in `.md`, the schema and its rationale could diverge silently.
4. **Decisions can be versioned with schema changes.** When a table or rule changes, the corresponding decision/register line can be edited in the same commit as the DDL change.

### Why a `docs/` folder still exists

`.sql` is good as the executable, reviewable, versioned truth. But prose explanations, summaries, query examples, and onboarding reading are often easier in Markdown. So:

- `99_documentation.sql` = authoritative artifact (decisions, register, boundaries, milestone map).
- `docs/*.md` = readable paraphrase + context for humans who prefer Markdown.
- The docs are **derived from, and must stay consistent with, the `.sql` artifacts**. If they ever disagree, the `.sql` version is the real one.

### Why not only Markdown

- Markdown cannot be executed against the database, so it cannot be the authoritative schema+rationale artifact.
- Markdown is easy to drift from the DDL if two artifacts both claim to be authoritative.
- Keeping decisions inside the DDL package reduces the chance that a schema change is committed without its justification.

### When you would change this approach

If the project later needs a processed doc site (search, cross-linking, generated API docs, bilingual rendering), you would add a generator that reads `99_documentation.sql` and the DDL comments and emits Markdown/HTML. The source of truth would still be the SQL + comments; the docs site would be derived output.

## Reading order

- **Module scope / rationale / unique differentiators**: `docs/module_index.md`
- **Decisions + reasons**: `docs/decisions.md` and `ddl/99_documentation.sql`
- **Compliance evidence**: `docs/compliance_register.md` and `ddl/99_documentation.sql`
- **Integration boundaries**: `docs/integration_boundaries.md` and `ddl/99_documentation.sql`
- **Milestone-order context menu**: `ddl/99_documentation.sql::schema_map_milestone_order`
- **Representative queries**: `docs/query_catalog.md`
- **Validation evidence**: `docs/reserved_identifiers.md` and `tools/checks/check_reserved.py`
- **Wallet table naming note**: `docs/wallet_table_note.md`
- **Seed data**: `ddl/seed/generate_seed.py`

## Conventions used in the DDL package

- PostgreSQL 16 target.
- Rule Group 1 naming: `snake_case`, singular table names, PK `id`, FK `<referenced>_id`, `idx_/uq_fk_/chk_/ex_/pk_` prefixes.
- Reserved-word handling recorded where it affected naming.
- Soft-delete where stated; append-only/audit where stated.
- Sensitive classification recorded in `COMMENT` where required by Rule Group 6.
- Multilingual UI + language preference handled per Rule Group 7.
- Analytics objects prefixed `analytics_` per Rule Group 8.
- Licences/seats/devices/sessions handled per Rule Group 9.
- Subscriptions/wallet/payments/download history handled per Rule Group 10.
