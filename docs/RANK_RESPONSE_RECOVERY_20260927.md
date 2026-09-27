# Recover complete portfolio ranking responses

The glass rotation project completed its six independent role reviews, then
stopped at `s8_rank` (steps 499 and 500). Provider responses contained all ten
rankings and the notes/roadmap, but included stray `]` characters after scalar
note fields. The old JSON extractor returned the nested ranking array after
failing to parse the outer object. Object coercion then overwrote repeated row
keys, retaining only the last candidate. The resulting `FATAL-RANK` repeated
during repair. This interruption was not caused by insufficient project budget.

## Behavior

- Repair at most two unmatched closing delimiters, outside JSON strings and at
  parser error positions. Accept only when the entire result is valid JSON.
  Never synthesize fields, scores, IDs, ranks, or narrative text.
- Extract the first root container, not a nested array/object from an invalid
  root. Other complete malformed responses require the existing model repair.
- When a stored result contains an array, reparse its original response to
  recover a complete object without an additional model call.
- Preserve repeated-key arrays as `items` instead of silently overwriting rows.
  Disjoint objects retain the existing merge behavior.
- Keep full candidate coverage and unique contiguous ranking validation.
  Do not change review phases, prompt inputs, meeting cache, limits, or budget.

## Validation

Offline reproduction restores all ten rows and all metadata from each of the
four affected production responses. Regression tests cover fresh and durable
responses through the actual ranking agent, quoted bracket literals, fenced and
prose-wrapped JSON, invalid roots, missing candidates, and non-destructive object
coercion. Existing ranking, meeting, provider, and durable gateway tests apply.

Deployment does not resume/reset the project or delete stored evaluation data.
Live verification reparses existing responses and checks candidate coverage
without model calls or database writes. Full project completion requires a
user-initiated continuation.
