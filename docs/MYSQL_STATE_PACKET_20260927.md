# MySQL state persistence packet fix

After the S6 classification repair, concept batches succeeded but aggregate
project persistence failed with MySQL 1153 (`max_allowed_packet`), followed by
2013 (lost connection). The stored project JSON was approximately 31 MB, but
the MySQL upsert bound it both as an insert value and as a duplicate-key update
value. Quoting and the duplicated JSON pushed the request past the 64 MiB limit.

Conflict updates now refer to the inserted column values. Each payload is sent
once, retaining existing atomic upsert behavior and excluding primary keys from
updates. SQLite behavior is unchanged. Histories, outputs, budgets and schema
remain intact. No database-wide limit is increased.

Regression coverage includes MySQL statement compilation with a single JSON
binding, partial conflict updates, full state round trips, project execution
lifecycle, budget management, AX recovery persistence and full idea review.
An additional deployment check reconstructs the failed aggregate from saved
successful S6 calls, compares actual driver-escaped packet sizes, and verifies
MySQL write/read fidelity inside a transaction that is always rolled back.

No project restart is performed: the user retains control of continuing S6.
Durable successful provider responses remain available for replay without
additional model charges when their request identities match.
