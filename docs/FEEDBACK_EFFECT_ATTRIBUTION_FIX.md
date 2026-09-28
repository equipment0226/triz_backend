# Feedback effect attribution and current RAG cases

## Observed defects

The September 29 audit found that generated S6 responses omitted
`active_effect_ids`. The schema accepted omission as an empty list, so saved
common evaluations could not label any scientific effect even when H_EFFECTS
applications and source IDs existed. Exposure does not establish adoption, so
historical empty lists cannot safely be filled from source prose.

RAG also retained both positive `fb-` and negative `fx-` documents after a score
revision. An actual 5 → 2 revision left its old positive example available to a
later problem. Model registration and learned-policy use were zero at audit
time; these defects were not failures of an active trained model.

## Changes

- Newly created AX bundles pin `explicit-active-effects-v1`. Every S6 concept
  must explicitly return a unique string list of the effects retained in its
  final mechanism, restricted to that concept's assigned, saved source lineage.
  Empty lists are valid. Missing, duplicate, foreign and malformed IDs fail the
  output contract; exposure is never automatically converted to adoption.
- Recovery and joint design have separately versioned output schemas and saved
  source context. They reassess adoption instead of silently losing or
  inheriting the baseline list. Joint designs retain both source lineages.
- A shared saved-source traversal handles nested sources, archived
  representatives and representatives that retain a source leaf's ID. Missing,
  cyclic or conflicting lineage abstains from source-derived attribution.
  Exact candidate snapshots and semantic episodes remain required for effects
  to enter common evaluations and training projections.
- RAG projects the latest saved final feedback per run and candidate. New writes
  deactivate the opposite class transactionally; neutral/unobserved revisions
  cannot resurrect old positive examples. Read-time checks exclude stale
  historical documents without changing their original feedback or reports.
  Consent, owner/project boundaries and source revisions remain enforced.
- A score revision alone does not invalidate an already-paid response. Existing
  bundles omit the new effect contract and retain their request schemas and S6
  checker identity, including the BCI lineage normalization/replay path.
  Freshness checks concern references in the actual new request and occur before
  a new paid reservation, so an unrelated later step or refreshed retry does not
  become stuck on a rejected task. New bundles also pin
  `latest-final-feedback-case-v2` to identify lesson sources in new requests.
  Legacy S6 retries reuse the recorded first-batch case block only when its
  complete request identity still matches and its completed paid response is
  usable. This preserves replay when a changed retrieval corpus alters ranking
  scores. Changed inputs and new calls use current retrieval.

## Verification and limits

Offline tests exercise the actual generation, independent review, constraint
gate, user feedback and effect dataset join with isolated provider fixtures and
settled fixture costs. They cover explicit empty adoption, invalid IDs, archived
lineage, both recovery families, codesign, RAG re-rating and consent changes,
idempotence, late writers and durable paid-response reuse.

CONDITIONAL remains an unobserved technical judgment; an explicit keep remains
weak positive user utility. Existing raw responses, frozen reports and common
evaluation events are not retroactively relabeled. No paid production analysis,
training, policy promotion or manual production-data migration is part of this
fix. The tests establish behavior, not production cost or quality improvement.

## AI-only reward verification

The existing reward projection uses the lowest current observed quality verdict
per mechanism, including independent concept, constraint, evaluation and
structural coverage reviews. The effect label is `0.7 * quality + 0.3 * utility`;
missing user utility contributes zero without being invented. When N effects
are explicitly active, each receives sample weight `1/N` as a shared candidate
proxy, not proof of its individual physical contribution. These coefficients are
configured weights, not learned coefficients or evidence of an active model.

Seven additional offline integration cases run a saved H producer, concept
generation, AI review, constraint gate and the dataset projection with no user
feedback. PASS produces +0.7, REVISE 0, REJECT/FAIL -0.7. A CONDITIONAL constraint
remains unobserved and does not override a PASS concept. Revisions replace prior
reviews; empty adoption does not produce effect samples.

The pre-deployment production audit at 2026-09-29 07:36 KST found 163 actual
model reviews, including 144 project-consented records. None had active effect
or application links. Structural reviews had the same missing links. Thus the
existing formula had not produced actual effect learning from those reviews;
the missing attribution addressed here must not be mistaken for learned weight
updates. Historical missing adoption is not backfilled.

The same read-only audit found 903 stored S8 final scores across nine completed
meetings absent from common evaluations. Their source steps were WARN because
policy skipped an additional rubric review (`UNVERIFIED`, `source=policy`), even
though the meeting's deterministic score/batch validation accepted the output.
The adapter previously considered only OK/SKIPPED steps. The fix also accepts
this narrowly identified policy-skip case when completed meeting, persona,
accepted final score and exact validated source output agree. Generic warnings,
failed responses and partial or mismatched scores remain ineligible. Existing
scores are not inserted retroactively into production evaluation events.
