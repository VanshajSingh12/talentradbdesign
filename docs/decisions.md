# Design decisions

Source of truth: `ddl/99_documentation.sql`.  
This file is a readable paraphrase for humans who prefer Markdown.

## DB provider

- Chosen: **PostgreSQL** (over MySQL).
- Reason: the design uses PostgreSQL-native features and naming that is less awkward under PostgreSQL 16.
- If MySQL is required later, the design will need a separate reserved-word cross-check and some engine adaptations.

## Gig model

- Gigs share the core job + application model with other job types.
- Gig-specific fields are stored in `gig_request_detail` and the rest of the gig marketplace module, so the core job/application tables are not polluted with gig-only columns.
- This matches the selected decision to keep a single shared core job/application model and add gig specifics as an extension.

## Credentials

- Credential storage follows industry best practice and is documented as such.
- Password/auth state is not consolidated into the user row; verification and recovery are modeled separately where needed.

## Tier 2 scope

- All Tier 2 items are included. No Tier 2 omissions.

## Tier 3 scope

- All five selected Tier 3 items are included as a separate, clearly labelled optional stretch module: `12_tier3_stretch.sql`.
- Included: salary benchmarks, company ratings, trending job snapshots, dashboard aggregates, feature flags.

## Out-of-docket content

- No out-of-docket tables, columns, or features are added.
- Any later out-of-docket requirement is flagged before implementation.
