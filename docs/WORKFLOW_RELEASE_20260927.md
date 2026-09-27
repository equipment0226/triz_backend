# Workflow coverage and report usability correction

This release follows the source and production-record audit in
[WORKFLOW_AUDIT_20260927.md](WORKFLOW_AUDIT_20260927.md). The affected Micro LED
project was inspected read-only; its completed report is not evidence of a
successful run of the new code. Deployment verification is recorded separately.

## Execution contract

S0–S10 retain their 13 execution stages. LITE/FULL/DEEP retain their configured
method sets. DEEP requires all eight implemented S5 methods to run or have an
explicit prerequisite-based inapplicability reason. The AX branch limit limits
each batch, not the total number of methods. Required coverage is independent
of optional coherence expansion, solution count and bundle age.

F/G/H receive the confirmed problem, success criteria, contradictions and scope
in their actual rendered request even when an old pinned prompt lacks the
corresponding placeholders. Empty applications require a recorded reason;
missing or malformed results interrupt rather than silently completing.

ARIZ Part 6 always runs immediately after Part 5 and before Part 7. Its model
output includes observations and reframing suggestions for 6.1, 6.2 and 6.3.
There is no solution-count threshold and no later S8 Part 6 trigger. Advice is
stored in the ARIZ product, does not create solutions, does not alter the
confirmed problem, and never dispatches S1 or a new project. Existing completed
reports without this model output do not receive fabricated retroactive advice.

Required ARIZ outputs are checked before subsequent analysis. A provider
failure recorded by a child agent cannot mark its track completed. Successful
parallel branches survive interruption and are not appended twice on continue.
An old partial S5 record lacking the new completion evidence is revalidated
only on explicit S5 entry; identical successful cached calls remain reusable.

## Ideas and data handoffs

All merged source ideas remain in the report. A curator omission is not treated
as a rejection. Source method provenance survives merging. Detailed concept
selection balances source methods, addressed problems and mechanisms within
its review limit; final recommendations have no method quota.

DEEP records pinned to the historical three-concept limit use the current
eight-concept review breadth. The pinned bundle is not modified. The number of
unassigned source ideas is reported explicitly, and an unreviewed idea is not
described as unsuitable. Existing cost reservations and budget ceilings are
unchanged; exhausted budgets interrupt analysis.

New S5 revisions clear S-curve, track execution and idea-review metadata. Only
the trends branch can write the S-curve. Dependent concept mappings, evidence
links and recovery-phase markers are cleared at their producer's rerun boundary.
S0–S4 reuse on an S5 rerun is intentional. A report-only or S6 rerun cannot
produce methods that were missing from the original S5 output.

## Reporting and validation scope

Empty expected method sections show their saved status and reason. Current S5
history is separated from preceding history using an explicit sequence boundary.
Older records without that boundary are labelled cumulative rather than guessed.
An unverified quality assessment remains visibly distinct from a passed check.

Detailed analysis records are closed by default and expand on request. The web
view defers their content DOM until expanded; long mobile reports are paginated.
Standalone exports preserve a closed, expandable details control.

Regression tests use isolated databases and prohibit paid model calls. They
verify dispatch, prompt inputs, output contracts, handoffs, failure/resume and
rendering. Browser checks cover desktop Edge and WebKit emulation; they do not
establish behavior on a physical iPhone. Model-call evidence and structural
checks do not establish engineering correctness or physical performance.

The catalog describes ARIZ Parts 8/9, but this application has no separate
Part 8/9 ARIZ executor. S8 evaluation and S10 feedback must not be presented as
proof that every original ARIZ-85C substep was executed.

## Verified deployment, 2026-09-27

Backend branch `fix/workflow-coverage-20260927`, commit `0a123fe`, passed 436
isolated regression tests and was deployed as Railway
`849f82ac-6b5e-4518-a62b-0585554ba9e8`. Frontend branch
`fix/report-details-20260927`, commit `5540cf4`, was deployed as
`6d4d994a-00f4-4b2d-998e-e0b43f507752`. Both deployments reported SUCCESS.
The production image matched 882 source-file hashes; six mode/bundle routing
scenarios, the Part 6 contract and health endpoint passed read-only checks.
No analysis jobs, model calls or production-record edits were made by these checks.

The public Micro LED report `run-bbe70a45d710` passed Edge and WebKit checks at
desktop and mobile viewports. Its 29 disclosure controls started closed, opened
on click, and removed the body DOM when closed. Mobile rendering used 54 pages;
page and tab changes reset disclosure state without extra document navigation,
JavaScript errors or horizontal viewport overflow. These were browser emulations,
not physical iPhone tests. The first bounded discovery scan found no suitable
case among the newest eight DEEP reports; the verified case was ninth and was
subsequently selected explicitly from the public list.

This workflow-only release retained the previously published 1,500-effect
catalog. Existing project analysis is unchanged; missing S5 methods and new
Part 6 model output require an explicit S5 rerun to generate new results.

## Subsequent ARIZ 4.1 presentation change

The subsequent [2,000-effect release](EFFECTS_2000_20260927.md) removes the
duplicated lower edge legend only from the small-people model in step 4.1.
Its three nodes, two arrows and meaningful action labels remain. Existing
reports and exports use the updated renderer without an analysis rerun;
other ARIZ diagram legends and saved step content are retained. The change
passed 22 focused rendering tests and a visual check with the Micro LED data.
