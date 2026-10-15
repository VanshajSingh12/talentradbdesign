# Query catalog

This is a small set of representative queries the schema is designed to answer.  
These are illustrative; they are not the only queries, and they are not necessarily final SQL for production.

## Master data

- Lookup active countries/states/cities for location context.
- Resolve a skill name to its stable master record.
- Find skill synonyms for multilingual skill matching.
- Translate a UI key for a given language with default-language fallback.

## Profile

- Load a candidate profile with contact, education, work experience, skills, languages, latest resume version.
- Find candidates with a completed profile above a completion threshold.
- Retrieve candidate activity for a candidate over a time window.
- Count profile views per candidate over a period.
- Get a candidate’s current skill affinity snapshot.

## Jobs and applications

- List active job requirements for an employer with positions and skill requirements.
- Find applications for a job requirement with current stage.
- Walk an application’s pipeline event history.
- Tag a job requirement or application using the shared tag master.
- Get structured denial reasons for applications that did not progress.

## Administration

- Resolve a user’s current roles and effective assignments.
- Load a user’s active sessions and recent login history.
- Find blocked user pairs for safety/blocking concerns.
- Load credential verification/recovery state for a user.

## Organisation

- Load an employer organisation with its locations, tax registrations, verification status.
- Resolve effective recruiter mappings for an organisation.
- List an employer’s industry classifications, including multi-classification.
- Link an employer to competitor/salary/review reference records.

## Gig marketplace

- Find open gig requests with available gig workers.
- Load a gig worker profile with availability and recent assignments.
- List gig assignments with handoffs and earnings references.
- Enumerate gig ratings or blacklist entries for a gig request.

## Licences / seats / devices / sessions

- Count active seats allocated against a subscription licence.
- Count active device sessions for a user.
- Revoke sessions for a user and record the revocation event.
- Load login history for a user window.

## Sourcing and consultant

- List open sourcing requests with assigned consultants.
- Load consultant decisions for open requirements.
- Enumerate sourcing shortlists and outreach recipients for a request.

## Subscriptions / wallet / payments

- Load a tenant’s active subscription periods.
- Load a wallet and its append-only ledger entries.
- Reconstruct a payment order’s status history.
- Load invoice/refund history for an order.

## Notifications / preferences / community

- Resolve a user’s notification preferences by channel and event type.
- Load a candidate’s job alert preferences.
- Load multilingual preferences and privacy settings.
- List community posts with reactions.
- Load a support ticket with replies.
- Load FAQ by category and language.

## Analytics

- Pipeline funnel by stage over a date range, from the fact or aggregate.
- Time-to-hire summary from the fact/aggregate.
- Source/channel attribution reporting.
- Employer activity or candidate activity summaries.
- Skill-affinity distribution reporting.
- Denial-code funnel reporting from denial facts or aggregates.

## Tier 3 stretch

- Salary benchmark lookup by industry, role, geography.
- Company ratings aggregated or per employer.
- Trending job snapshots for a date.
- Dashboard aggregate summaries.
- Feature flag evaluation by tenant/candidate and scope.
