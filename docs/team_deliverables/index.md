# Milestone 20 — Queries and validation across all modules

**Team deliverables index**

This folder collects the Milestone 20 deliverables for backlogs B65–B69. Each item has a Markdown document with the query intent, results, and observations, and a raw report file under `scripts/reports/` with the exact SQL output and execution plans that were captured from the live database.

**Database used for the runs:** `talentra` on `localhost:5431`
**Run captured:** 2026-10-16

## B65 — Query set with output and execution plans

**Owner:** Team  
**Deliverable:** Query set with output and execution plans

Fixed query set covering functional, transactional, lookup, and performance cases, with execution plans for the top ten.

- Document: `B65_query_set_with_output_and_execution_plans.md`
- Raw report: `scripts/reports/B65_query_set_with_output_and_execution_plans.txt`

## B66 — Seed validation report

**Owner:** Team  
**Deliverable:** Seed validation report

Validates the seeded data against the data standards in Section 5 and the coverage gap register, and records any failures.

- Document: `B66_seed_validation_report.md`
- Raw report: `scripts/reports/B66_seed_validation_report.txt`

## B67 — Module query results: Administration, Organisation, Gig

**Owner:** Member A  
**Deliverable:** Module query results for Administration, Organisation and Gig

Module-specific queries validating the seeded data for Administration, Organisation, and Gig Marketplace.

- Document: `B67_member_A_Admin_Org_Gig.md`
- Raw report: `scripts/reports/B67_member_A_Admin_Org_Gig.txt`

## B68 — Module query results: Licences, Sourcing, Subscriptions

**Owner:** Member B  
**Deliverable:** Module query results for Licences, Sourcing and Subscriptions

Module-specific queries validating the seeded data for Licences, Sourcing, and Subscriptions.

- Document: `B68_member_B_Licences_Sourcing_Subs.md`
- Raw report: `scripts/reports/B68_member_B_Licences_Sourcing_Subs.txt`

## B69 — Module query results: Notifications, Analytics, shared items

**Owner:** Member C  
**Deliverable:** Module query results for Notifications, Analytics and shared items

Module-specific queries validating the seeded data for Notifications, Analytics, and shared team items.

- Document: `B69_member_C_Notifications_Analytics_Shared.md`
- Raw report: `scripts/reports/B69_member_C_Notifications_Analytics_Shared.txt`

## Notes on this run

- Where a query in the fixed set or a member module referenced a table that is not present in the current seeded schema, the query was either skipped or recorded as a failure in the result, and the missing table was listed in the B66 coverage gap register.
- Queries that failed are documented in-line with the reason for failure, so the result is auditable rather than silently dropped.

## Related documentation

- Repository documentation index: `docs/index.md`
- Query catalog: `docs/query_catalog.md`
- Module index: `docs/module_index.md`
