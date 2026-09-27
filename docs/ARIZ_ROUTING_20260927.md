# ARIZ execution routing correction

The requested pattern-glass 180-degree rotation run (`run-baa72a38ef40c8c63155ffc7a1dd25ee`, created 2026-09-27 00:35:17 UTC) completed in DEEP mode with four displayed concepts. The saved ARIZ product was null and no ARIZ model calls occurred. This was an execution omission, not a report rendering issue.

Read-only review of all 59 stored projects belonging to the requesting owner found 34 DEEP runs: all 24 created through September 12 contained ARIZ execution records; all 10 created from September 16 onward lacked them. All 34 were completed. The former used the legacy workflow and the latter used `triz-ax-v3.1`.

Git history pinpoints the regression in `0e5f719edb24ed8a8312fc048bfdb47f3bcf24fe` (September 16, 11:10 KST): S5 began replacing mode-selected tracks with the new AX coordinator's selection. That coordinator selected matrix, separation and effects, without consulting DEEP mode. Later coherence expansion included ARIZ only as an optional queued track. The September 26 report-only Part 6 change occurred after this regression.

The original baseline ran matrix, separation and standards tracks. Its pending queue contained effects, trimming, FOS and ARIZ; the one permitted three-track expansion never reached ARIZ. A later S5 rerun retained the previous expansion counter, so only the baseline ran in that revision.

DEEP runs and explicit ARIZ selections now place ARIZ in the initial bounded track selection. Other tracks still obey the existing branch and budget limits. A deliberate rerun from S5 or an earlier stage clears its previous expansion plan, count and dependent inventory. Continuing an interrupted revision retains its count, preventing unbounded repeats.

The legacy S5 executor also restores ARIZ when a DEEP run's saved enabled-track list is incomplete. LITE and FULL modes do not force ARIZ into their baseline; explicit selection or an applicable optional expansion may still use it. Provider failures or exhausted execution budgets interrupt the run through the existing error handling rather than constituting a successful mandatory analysis.

S5 additionally checks the mandatory DEEP postcondition: both the executed `D_ARIZ` track and its saved ARIZ product must exist before concept assembly can proceed. A missing result interrupts execution instead of silently reporting a completed deep analysis.

ARIZ execution is independent of the Part 6 condition. Once the final displayed solution count is known, the existing S8 ranking call supplies optional 6.1–6.3 report advice when the count is at most three. A deterministic `s8_ariz_p6` trace records the threshold decision, individual advice provenance and that neither the problem nor S1 was restarted. Four or more solutions still produce the condition-check trace. This trace adds no model call or tokens.

Validation: the final mandatory-result guard passed all 78 targeted routing, reformulation, pipeline-quality and provider-interruption tests. Earlier checks also covered AX coordination and report generation. Tests prohibit real model calls. The original production run was inspected read-only; it was not rerun and no historical execution trace was fabricated.

At the user's request, this fix is released separately before the effects-2000 and mobile report improvements. Deployment evidence is tracked separately; this document alone does not claim deployment.
