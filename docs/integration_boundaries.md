# Integration boundaries (Section 6)

Source of truth: `ddl/99_documentation.sql`.

## Principle

Each module has a documented boundary to external systems and to other modules. The schema does not assume live external integration in this artifact; it records what is shared and what is not.

## Boundaries by concern

- **Identity / credentials**: handled inside the administration module; external identity providers are an integration concern, not assumed here.
- **Payments**: payment orders, status history, invoices, refunds, wallet ledger, and related audit are internal; actual payment gateways are an external integration boundary.
- **Notifications/delivery**: delivery pipes are modeled for high-volume write patterns where the docket calls for it; the actual delivery providers are external.
- **Company review / salary data**: recorded as a boundary/relationship concern rather than a full inbound ETL of competitor data.
- **File storage**: large content such as resume templates and large text is referenced, not stored as unbounded in-db text where avoidable.
- **Cross-module sharing**: only what is documented (foreign keys, reference codes, shared masters) crosses module boundaries.

## What is intentionally not included

- No implicit integration with external services is encoded in the DDL.
- No undocumented shared mutable state across modules.
