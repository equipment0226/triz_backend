# Bounded balanced patent-review queue v1

This workflow prepares public patent abstracts for direct conversation review.
It does not analyze them, call a model, update the canonical effect catalog, or
change the existing 81 sequential pages, their review ledger, or their cursor.
The queue starts in `pilot/data/patent_effects_balanced_v1`; use a separate working
directory for each set of request/response files.

## Selection and accounting

- Read at most 2,000 metadata points from the existing configured Qdrant collection
  in default point-ID order, with `with_vectors=False`. The UUIDs are deterministic
  hashes of publication numbers. This avoids a publication-number alphabetical
  prefix, but is **not a statistically random sample**. No CPC/IPC filter is sent.
- Classify using every stored CPC and IPC code, preserving all A-H memberships.
  IPC-only records participate. Y remains a cross-cutting tag; no valid A-H
  membership means `UNCLASSIFIED`. A selected patent receives one scheduling
  bucket, while its complete membership remains in the audit record.
- Give priority to buckets with fewer previously queued records. Break ties with
  lower coverage in the previous directly reviewed corpus, sparse availability in
  the current pool, and a rotating bucket pointer. Prefer single-section candidates
  when possible so a multi-section candidate can serve a scarce section. Country
  and year counts break candidate ties; these are not population-proportional quotas.
- Exclude previous `LINK`, `DEFER`, `DESIGN_ONLY`, `REJECT_CLAIM`, and `NO_ABSTRACT`
  publication numbers, plus their known families. Also exclude previously attempted
  queue numbers, queued families, and within-batch family duplicates. Missing/zero
  family IDs cannot establish family identity and do not collapse unrelated patents.
- Hydrate only the chosen maximum 72 publication primary keys in SQL. No corpus
  scan, index creation, table initialization, vector writes, embeddings, or model
  calls occur. The remote helper has only `scroll()` and `fetch(selected_numbers)`
  read paths.
- Only actual nonempty SQL abstracts become `PENDING_REVIEW`. Recheck classifications
  and families against the hydrated document; stale bucket assignments and new
  family duplicates get explicit dispositions. Record actual country/year/section
  counts and missing-bucket deficits after hydration. Country falls back to the
  publication authority when source metadata is missing; unknown years stay unknown.

Every immutable batch stores the complete bounded metadata pool, selection,
dispositions, source content hashes/fingerprints, and the next independent Qdrant
cursor. Unselected candidates are recorded as `ELIGIBLE_NOT_SELECTED_UNREVIEWED`;
they have **not** been examined. Advancing the scroll does not mark them analyzed.
They remain available in the batch audit if a later explicitly prepared selection
is needed. There is no claim that every corpus record will be queued or reviewed.
`scroll_exhausted` only means Qdrant returned no next offset for this pass. A changing
index is not a transaction snapshot and can lag SQL ingestion.

The state counts queued records, not completed reviews. Existing reviewed-coverage
counts are used only to prioritize tied fields; this workflow does not repair the
old review distribution retroactively. Multi-section membership counts can sum to
more than the number of documents.

## Explicit execution

Run from the repository root. Commands below are a procedure, not evidence that a
remote read has been performed. `patent_remote.py` uses the existing authenticated
backend connection; configuration files contain only public IDs and queue metadata.

```powershell
$balancedWork = '.deployment/balanced-patent-review-000001'
New-Item -ItemType Directory -Force -Path $balancedWork

.venv/Scripts/python.exe pilot/scripts/prepare_balanced_patent_review.py request --output "$balancedWork/pool-request.json"
.venv/Scripts/python.exe deploy/patent_remote.py deploy/harvest_balanced_patent_page.py --params "$balancedWork/pool-request.json" --output "$balancedWork/pool.json"

.venv/Scripts/python.exe pilot/scripts/prepare_balanced_patent_review.py select --pool "$balancedWork/pool.json" --output "$balancedWork/selection.json" --hydrate-request "$balancedWork/hydrate-request.json"
.venv/Scripts/python.exe deploy/patent_remote.py deploy/harvest_balanced_patent_page.py --params "$balancedWork/hydrate-request.json" --output "$balancedWork/hydration.json"

.venv/Scripts/python.exe pilot/scripts/prepare_balanced_patent_review.py commit --pool "$balancedWork/pool.json" --selection "$balancedWork/selection.json" --hydration "$balancedWork/hydration.json"
.venv/Scripts/python.exe pilot/scripts/prepare_balanced_patent_review.py status
```

Use a new working-directory suffix for the next batch; `request` loads the last
committed Qdrant offset. Requests and selections cannot overwrite different existing
content. `commit` first writes the immutable batch, then atomically updates local
state. Repeating the same commit is safe; it recovers a failure between those writes.
A leftover `.commit.lock` after abrupt process termination requires checking that no
commit process is running before removing that local lock. Never copy this cursor
into the sequential review ledger.

If the old exclusion ledger changes between selection and commit, regenerate the
selection with a fresh filename and repeat hydration. If a scroll reaches its end,
start another explicitly versioned directory for a later pass; the script does not
silently reset the cursor or declare an exhaustive review complete.

Review `batch-000001.json`'s `documents` directly. Their source fingerprints use the
same fields as `effect_manual_review.source_fingerprint`. Existing sequential
`record_manual_effect_reviews.py` expects contiguous number-ordered pages and must
not receive these queue batches. Recording decisions and canonical bindings remains
an explicit subsequent operation; this queue does not manufacture such decisions.

Record authored decisions separately after directly reading the selected sources:

```powershell
.venv/Scripts/python.exe pilot/scripts/record_balanced_patent_reviews.py --batch pilot/data/patent_effects_balanced_v1/batch-000001.json --decisions pilot/research/effects/balanced-patents-2026-09-27-01.tsv --review-id 2026-09-27-01 --apply-links
```

This archives the public source batch in `research/effects/balanced_source_batches`,
binds decisions to exact source fingerprints in `balanced_reviews`, and derives
`balanced-patent-progress.json`. Only explicit LINK decisions attach sources to
existing canonical effects. Changed content cannot reuse an old decision. The
sequential ledger and `manual-progress.json` remain intact. The queue's own
`analysis_performed=false` still correctly describes what the **queue preparation**
did; the separate review ledger is the authority for completed human/conversation
review. Future batches must also be read and explicitly recorded.

### First execution, 2026-09-27

The first bounded pool contained 2,000 metadata points; 72 publication keys were
selected (8 per A-H/unclassified bucket). SQL returned 49 nonempty abstract fields
and 23 records without abstracts. All 49 fields were directly examined and recorded:
14 LINK, 24 DESIGN_ONLY, 11 DEFER. One DEFER is a literal `Pendiente` placeholder,
so these are **48 technical abstract fields plus one examined placeholder**, not
49 complete technical disclosures. No patent full text was read by this operation.

Actual reviewed assignment counts: A5, B5, C6, D7, E5, F6, G5, H6, unclassified4.
There are 28 publication authorities, years 2000-2026, and 68 distinct four-character
CPC/IPC subclasses. A document can contain many classification codes; code counts
must not be mistaken for patent counts. Prior sequential reviews remain 10,851
abstract fields, 2,309 without abstracts, cursor `AT-512674-A1`. The new 49 fields
have no previously attempted publication number or known reviewed family overlap.
The 1,925 eligible but unselected metadata candidates are still unreviewed.

Review evidence: `balanced-patents-2026-09-27-01.tsv`,
`balanced_reviews/2026-09-27-01.json`, and `balanced-patent-progress.json`.

## Deliberately separate follow-up

Runtime problem-solving retrieval still ranks ANN evidence using its existing
relevance score and family deduplication. Evidence-query diversification or reranking
is a separate product change. This offline review queue does not modify
`vector_patents.search_batch`, ingestion filters, or per-run evidence retrieval.

## Validation

```powershell
.venv/Scripts/python.exe -m pytest pilot/tests/test_balanced_patent_review.py pilot/tests/test_balanced_patent_records.py pilot/tests/test_manual_effect_reviews.py pilot/tests/test_patent_effect_sweep.py -q
```

Tests use local fixtures and fake remote clients; no production access is necessary.
