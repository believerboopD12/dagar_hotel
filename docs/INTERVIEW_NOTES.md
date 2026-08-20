# Interview Notes

## 30-second explanation

I refactored a monolithic Streamlit restaurant app into a local-first operations system. It uses a service layer and SQLAlchemy over SQLite, with transactional orders, Decimal billing, controlled statuses, CSV exports, backups, tests, logging, and practical local security.

## 60-second explanation

The original app mixed Streamlit, direct MySQL calls, credentials, menu data, and business logic in one file, while storing order items as text. I preserved the actual restaurant workflow but normalized customers, menu items, orders, line items, and payments. Streamlit calls testable services inside SQLAlchemy transactions, so an order and its related records either all persist or all roll back. SQLite makes the application usable on one laptop without a cloud account. I added a state machine, payment rules, operational reporting, CSV export, timestamped backup/restore, PBKDF2 authentication, health checks, and isolated pytest coverage.

## 2-minute explanation

This is a modular monolith for one small restaurant. The interface has dashboards, customers, menu management, order entry, statuses, and payments. Services validate mobile/email, quantities, availability, discounts, transitions, and payments independently of Streamlit. SQLAlchemy models use foreign keys, uniqueness and check constraints, timestamps, indexes, and Numeric money. SQLite foreign keys are enabled on every connection. Order creation builds the order, line items, and payment in one transaction; tests simulate a failure and prove no partial data remains. The default database is `data/restaurant.db`, while PostgreSQL remains optional through the same ORM. Operators can download CSV records and create timestamped backups. This scope is intentionally understandable and maintainable by one developer.

## Original Problem and Refactor

The old version had committed credentials, a hard-coded admin password, direct connections per function, one denormalized order table, float totals, hard-coded menu values, and no tests or recovery tooling. Useful menu data and assets were preserved; persistence, rules, UI, configuration, and documentation were reorganized rather than inventing unrelated room-booking features.

## Architecture Walkthrough

`Streamlit page ? service ? SQLAlchemy session ? SQLite`. UI code collects inputs. Services enforce business rules. The session context commits on success and rolls back on failure. Reporting and export functions issue bounded, parameterized queries.

## Database and SQLAlchemy

Customers place orders. Orders own line items and one payment. Line items reference menu items but copy unit price so historical bills do not change. SQLAlchemy provides one model/query approach for SQLite and optional PostgreSQL.

## Transactions and Failure Scenarios

Order, items, and initial payment are atomic. SQL errors, unavailable items, invalid quantities, and simulated exceptions leave no partial order. Database downtime is logged internally while the UI gives a safe retry message. Restore requires explicit confirmation.

## Why Decimal?

Binary floating point cannot represent many decimal fractions exactly. Decimal plus Numeric columns makes tax, discounts, and totals predictable.

## Validation and State Machine

The service layer validates customers, quantity 1?100, availability, payment method, minimum order, discount, and tax. Valid progression is pending ? preparing ? ready ? completed. Active orders may be cancelled, but paid orders require a refund process before cancellation. Completed and cancelled orders are terminal.

## Authentication and Security

Passwords are PBKDF2-SHA256 hashes with random salts and constant-time verification. Secrets are environment-based, SQL is parameterized, logs exclude PII and credentials, and local DB/backups are ignored. Development can run without a password; production mode cannot.

## Logging

Startup, schema setup, order creation, payment recording, status changes, and rollbacks are logged. Customer details and secrets are not logged.

## Testing

Tests use temporary/in-memory SQLite, never the live database. They cover initialization, persistence, foreign keys, rollback, billing boundaries, customers, menu, orders, transitions, payments, reporting, exports, backup/restore, security, and configuration fallback.

## SQLite Persistence and Backup

The local DB lives at `data/restaurant.db`. Initialization and demo seeding are idempotent. Backups use unique timestamped names in ignored `backups/`; restore requires `--confirm`.

## Why No Async or Microservices?

Streamlit is synchronous and local transactions are short. Async is useful for concurrent network calls or a high-concurrency API, neither of which exists here. Microservices would multiply deployment and failure modes for one operator.

## Scaling Discussion

For multiple branches, add tenant/branch IDs, staff roles, central PostgreSQL, migrations, branch-aware reporting, and automated off-site backups. For roughly 100 concurrent users, replace Streamlit as the transaction UI with a web API, use PostgreSQL connection pooling, optimistic locking, pagination, load testing, and observability. Cloud deployment also needs HTTPS, managed secrets, automated migrations, monitoring, and disaster-recovery testing.

## 25 Interview Questions

1. **Why SQLite?** Zero configuration and simple recovery suit one local operator.
2. **Why SQLAlchemy?** It centralizes parameterized access, models, and transactions.
3. **Why a modular monolith?** The business is small and one deployment is easier to operate.
4. **Why normalize items?** It enables integrity, item reporting, and reliable updates.
5. **Why snapshot unit price?** Later menu changes must not rewrite old bills.
6. **Why Decimal?** It avoids binary float currency errors.
7. **Where is atomicity needed?** Order, items, and initial payment creation.
8. **How is rollback verified?** A test raises mid-transaction and asserts no records remain.
9. **How are SQLite foreign keys enabled?** A SQLAlchemy connection event runs the PRAGMA.
10. **What are valid statuses?** Pending, preparing, ready, completed, and cancelled.
11. **Why terminal states?** Reopening completed/cancelled orders creates audit ambiguity.
12. **Can paid orders be cancelled?** Not before an explicit refund flow.
13. **Are partial payments supported?** No; the recorded amount must match the order total.
14. **Are card details stored?** No, only a method label and optional reference.
15. **How is injection prevented?** SQLAlchemy uses bound parameters.
16. **How are passwords stored?** Salted PBKDF2-SHA256, never plaintext.
17. **What is exported?** Customer, order/sales, and payment operational data.
18. **What is excluded from exports?** Authentication data and application secrets.
19. **How are backups protected?** Unique names, ignored directory, and explicit restore confirmation.
20. **Are tests isolated?** Yes, using temporary or in-memory databases.
21. **What does health check verify?** Config, imports, writable data path, connection, SELECT, schema, and auth mode.
22. **Why no async?** There is no concurrent network I/O to justify it.
23. **Why no Redis or queue?** The local workload does not require distributed coordination.
24. **What changes for multiple servers?** Move to PostgreSQL and add concurrency controls/migrations.
25. **Largest current limitation?** It targets one small business rather than multi-user branch operations.
