# TRIZ AX v3.1.2

New projects retain source ideas omitted from an incomplete merge response. The
merge model cannot silently discard an unmentioned idea. Each retained idea must
still pass the normal concept, coherence and constraint checks.

When fewer than five candidates remain, a bounded alternative-mechanism search
gets a place alongside repair tasks. An uncovered original problem has priority.
Existing limits (two recovery targets, two attempts each, four additions overall)
and validation budget reservation remain in force. Five is a target; invalid or
unsupported mechanisms are not promoted to meet a quota. Every retained solution
is displayed, including portfolios larger than five.

The change is pinned by `portfolio_completion_v1` in new execution bundles.
Existing pinned bundles, original schema/state contracts, global model settings,
project budgets and the 13-stage workflow remain unchanged. Merge and concept
counts are recorded in the new bundle's scratch namespace for diagnosis.

Report output uses readable terms such as QUICK WIN, BIG BET and Korean change
scope labels. Known internal fields are localized in prose and table cells;
stored enum values, hyperlinks, source code and technical identifiers are preserved.

Verification: `python -m pytest -q pilot/tests` — **508 passed**. The initial run
had one stale version assertion; it was updated to v3.1.2 and the full suite rerun.
No paid model calls or production database writes were part of these tests.
Actual engineering performance and new live model-generated portfolio size are
not established by these deterministic regression tests.

Deploy with the matching frontend progress-card update. Preserve the v3.1.1 tag;
use the new `triz-ax-v3.1.2` release tag. The patent draft prototype is excluded.
