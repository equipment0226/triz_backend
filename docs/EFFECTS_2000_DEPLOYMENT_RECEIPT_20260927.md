# Verified deployment: effects 2,000 and ARIZ 4.1

Verified on 2026-09-27 at approximately 12:02 KST. Both Railway deployments
reported SUCCESS, and `https://trizstudio.online` served the updated application.

| Component | Deployed Git commit | Railway deployment |
| --- | --- | --- |
| Backend | `bccb809185342579b619b40973ff1d3515d70ede` | `8732e42e-d64d-45e6-a720-895bd6119517` |
| Frontend | `745f898abe7e627bfd0f4db0d1c19e73f6347726` | `4317a880-e85e-431e-8e1d-f75fe6aea488` |

Both commits were pushed to `deploy/effects2000-20260927` in their respective
GitHub repositories. This receipt is a subsequent documentation-only commit;
it does not require an application redeployment. The packaged research progress
file describes the source-time snapshot, while this receipt confirms deployment.

## Production checks

- All 1,140 expected backend image files matched their release hashes.
- The backend served 2,000 distinct source-linked effects. All 1,500 baseline
  identities and source identifier/URL pairs were retained.
- The custom-domain browser showed 2,000 effects, opened four new card examples,
  and resolved all 24 merged legacy URLs to the correct representative cards,
  without JavaScript errors.
- The actual Micro LED report `run-bbe70a45d710`, ARIZ 4.1 `ariz-step-17`, kept
  three nodes and two arrows. The lower legends and numbered badges changed
  from two each to zero; both action labels remained. Node and edge data hashes
  matched the predeployment baseline. A rendered SVG screenshot was inspected.
- A different public report, `run-5408bf496fbc`, preserved the two legends and
  two badges of its ARIZ 2.2 diagram. Suppression is specific to step 4.1.
- The custom domain and Railway domain returned the application and health 200,
  public report-list 200 and protected unauthenticated run-list 401. Authentication
  configuration remained available. No account or analysis job was created.
- All 11 service statuses were SUCCESS; all seven volume identities were
  unchanged. The patent indexer retained deployment
  `9c9e621d-b1a8-42bd-93f1-6dfbbeba0842` and continued IMPORT/INDEX activity.

The in-memory Part 6 rendering probe passed without persistence. The earlier
workflow release separately verified routing and contracts, plus Edge/WebKit
desktop/mobile report behavior. This subsequent receipt does not claim a new
paid model run, a physical iPhone test or a full scientific validation.

## Patent snapshot

At 2026-09-27 03:02:25 UTC, the corpus reported **11,832,140 stored documents**,
**11,832,140 indexed** and **0 pending** at that instant. Qdrant separately
reported 11,832,199 points with green/OK status. Counts are read while ingestion
continues and are not an atomic SQL/vector snapshot. The source scan remained
incomplete. Zero pending does not mean all source data has been ingested or
that all stored patents have been analyzed.

Direct research remains 10,851 previously reviewed abstract fields plus the new
balanced batch's 48 technical abstract fields and one examined placeholder.
See [the release scope](EFFECTS_2000_20260927.md) for distinctions between
ingestion, abstract review, source attachment and scientific-effect cards.

Verification artifacts retained locally under `.deployment`:
`effects2000-release-20260927.json`, `effects2000-live-source-20260927.json`,
`effects2000-20260927-browser.json`, `slp41-live-20260927-result.json`,
`effects2000-worker-20260927.json`, `effects2000-public-progress-20260927.json`,
and `patent-inventory-effects2000-final-20260927.json`.
