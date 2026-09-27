# S6 prompt chamber wording correction

The literal `찤4버` was stored in `verify.taboo_block()`'s example of a
zone-specific prohibition and in the `Constraint.zone` source comment. It was
not an intentional technical term. The available Git history already contained
both strings in its initial 2026-09-08 revision; it does not establish how the
typo was originally introduced.

Both occurrences now read `챔버`. The runtime example is injected by
`quality.generate_concepts()` into the `taboo_block` placeholder of
`P_S6_CONCEPT`. It appears when confirmed prohibitions exist. Subsequent S6
prompt construction uses the correction; historical saved prompt traces retain
their original execution text.

The two-line change passed 32 existing pipeline-quality tests. Commit `3769838`
was pushed to `fix/chamber-prompt-20260927` and deployed to the backend as
Railway `fea04747-f52f-4a26-84cc-ec58ecff0ea7` (SUCCESS).

Read-only production verification matched both changed file hashes and rendered
the actual S6 template with an in-memory confirmed-prohibition fixture. It
contained `예: 챔버 내부는 금지` and no typo. Health returned 200 and the catalog
still contained 2,000 effects. No analysis jobs, model calls or database writes
were made. All other service deployment IDs and all seven volume identities
were unchanged.

The separate [idea-selection audit](IDEA_SELECTION_AUDIT_20260927.md) documents
the current 46-to-8 allocation, actual project counts and discovered limitations.
This release changes wording only; it does not change candidate selection.
