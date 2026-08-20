# Interview Notes

## Demo Authentication

The public `admin/admin123` and `staff/staff123` accounts are fictional local-demo
credentials. The development seed hashes both with PBKDF2-SHA256 before inserting them.
Seeding is idempotent and never overwrites an existing user's password. Production mode
does not create demo users; private users must be provisioned explicitly.

## Authentication vs Authorization

Authentication verifies username and password against the stored hash. Authorization is a
separate central role-action policy. Admin can access dashboard, customer records, exports,
menu management, orders, and payments. Staff can operate orders/payments, create or find
customers, and view menu availability, but cannot access admin menu editing or customer
exports. Authorization runs at route dispatch rather than relying only on hidden sidebar links.

## Local Persistence

SQLAlchemy stores users and restaurant records in the ignored `data/restaurant.db` SQLite
file. Foreign keys are enabled per connection. Initialization and demo seeding are safe to
repeat; backups are timestamped and ignored by Git.

## Product Image Strategy

The original application captions establish genuine mappings for tea, cold drink, dahi,
dal, paratha, sada roti, tandoori roti, shahi paneer, and matar mushroom assets. Current
seed-menu matches use those original files. Three optimized, original generic category
fallbacks cover curries, breads, and sides/drinks without pretending to be photographs of
the restaurant's actual food. A centralized resolver stores only repository-relative paths,
checks file existence, and safely falls back when an asset is missing.

## Production Evolution

A public deployment should disable demo seeding, provision private named users, enforce
strong password/reset policy, use HTTPS and managed secrets, and add audit records for
privileged changes. A larger organization would add branch-scoped permissions and user
administration; JWT/OAuth are unnecessary for this local Streamlit scope.

## Key Interview Questions

1. **Why are demo credentials public?** They make a cloned local portfolio immediately testable.
2. **Are demo passwords plaintext in the DB?** No, only salted PBKDF2 hashes are stored.
3. **Can production use demo accounts automatically?** No; the seed refuses outside development.
4. **How are duplicate demo users prevented?** Username uniqueness plus idempotent lookup.
5. **Authentication versus authorization?** Login establishes identity; the policy controls actions.
6. **Why is hiding navigation insufficient?** A caller could invoke a route directly, so dispatch checks roles.
7. **What can staff not do?** Menu edits, full customer management/exports, and other admin actions.
8. **Why centralized image mapping?** It avoids fragile conditional chains and absolute paths.
9. **What happens when an image is missing?** The resolver returns a checked category fallback.
10. **Are generated images actual restaurant dishes?** No, they are explicitly generic UI assets.
11. **Why SQLite?** It gives a zero-account, persistent local demo with simple backups.
12. **How would production auth change?** Private provisioning, stronger lifecycle controls, HTTPS, and auditing.
