# Current-idea identity in legacy reconsolidation

The glass project resumed S6 under the ten-representative policy. Its 65 current
ideas retained 90 ancestral source identities inside nested lineage metadata.
The merge model used archived IDs in keep_ids, causing unknown-ID, duplicate and
missing-coverage failures. The most recent attempt was not stopped by budget:
the durable ledger reported $5.111548 spent of $6, with no active reservations.

Merge input now exposes only top-level current IDs as selectable identities and
supplies their complete allowlist explicitly. Nested identity/previous-grouping
metadata is removed from the model-facing copy; semantic descriptions, conditions
and stored source lineage remain unchanged. Unknown IDs, missing coverage and
more than ten representatives still fail validation rather than being guessed or
silently normalized. The full source records remain available in reports.

S6 is set before its legacy reconsolidation prerequisite, so interruptions and
costs are no longer labelled as the previous S8 evaluation stage.

The independently confirmed accumulated-history packet problem is addressed
operationally by persisting MySQL max_allowed_packet at 128 MiB instead of 64 MiB.
This is transmission headroom, not a project budget increase. No history is
deleted and no project is resumed. New backend connections inherit the setting.
It is finite headroom; archival/storage normalization remains a separate change.
