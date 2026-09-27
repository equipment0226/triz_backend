# Isolate project lists and recover stopped analysis checkpoints

## Observed production failures

- The dry LFP project persisted `solve.ariz.unresolved_reason: null` after a
  successful ARIZ Part 5 response. Assignment bypassed schema validation; the
  next checkpoint load failed. List endpoints loaded every full checkpoint just
  to resolve display labels, so this one project caused both owner and public
  paginated lists to return HTTP 500. Orphan recovery also stopped on it.
- The WET project returned 21 representatives after repair. The Micro LED
  project assigned the same source to representative groups 9 and 10. Their
  semantic partition checks correctly stopped execution; budget was available.
- Thin-film hot-air drying was waiting for a user's constraint decision, not
  failing. The glass rotation project had completed through S10 after the prior
  ranking response patch.

## Changes

- ARIZ accepts null for its optional unresolved reason as an empty string on
  load, and Part 5 no longer assigns null to this field. No failure is invented;
  the existing checker still requires a reason when Part 5 yields no ideas.
- Typical library rows use the lightweight runs table without hydrating report
  histories. Legacy titles containing known identifier syntax retain label
  resolution with a safe fallback for invalid checkpoints.
- Notifications project only seven scalar JSON fields in the database rather
  than transferring and validating entire analysis histories. Owner scoping,
  consent, pagination, search, and stable notice IDs are unchanged.
- Invalid checkpoints are isolated per run during orphan recovery, keeping API
  startup and recovery of other projects available.
- S5 repeats the ten-representative contract after legacy injected viewpoints,
  reports exact duplicate IDs and both assignment locations, and allows up to
  three bounded repairs under the existing budget gate. Grouped deferrals are
  expanded without changing IDs or reasons. Ambiguous cross-group assignments
  require the model's decision; no clipping or arbitrary deduplication occurs.

## Validation and rollout

Regression coverage includes concurrent owner/public/notification requests with
unreadable analysis details, account isolation, legacy null ARIZ recovery,
independent orphan recovery, exact duplicate diagnostics, and actual agent
repair from 21 representatives through a duplicate correction to ten valid
representatives with all 21 sources retained. Existing ARIZ, consolidation,
display, product, notifications, and execution lifecycle checks are retained.

Deploy backend only. Verify live source hashes, public HTTP listing, concurrent
read-only list/notification queries, and readable LFP checkpoint. Do not change
budgets, delete history, approve pending constraints, or dispatch paid project
continuations. Startup may mark a demonstrably orphaned run as interrupted.
