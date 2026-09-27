# S6 classification repair

S6 concept generation repeatedly stopped when model responses supplied novelty
classes `ADAPTATION` or `DERIVATIVE`, or change scale `SUBSYSTEM`. These values
are outside ConceptSpec's enums. Validation replaced the useful Pydantic errors
with a generic field/title instruction, so the repair call repeated the error.

The S6 prompt now defines allowed novelty, change-scale and maturity values and
their meanings. Existing saved prompt bundles render this corrected contract via
the existing compatibility path. Schema repair feedback identifies the assigned
idea, nested field and expected value/type without echoing the rejected input.
No automatic relabelling, idea deletion, coverage relaxation, candidate cap or
constraint-policy change is introduced. Prompt changes invalidate old call cache
keys; already generated records remain intact but S6 calls can be regenerated.

Validation: 62 tests passed across test_s6_schema_repair, test_full_idea_review,
test_pipeline_quality and test_retry_notifications. Tests reproduce the invalid
production enums, verify nested-field diagnostics, and exercise the real
run_agent repair loop with offline model responses, retaining every assigned ID.

The targeted project was observed interrupted at S6 before deployment, with no
running model tasks. No project reset, history deletion, budget change or paid
project restart is performed by this patch. The user controls continuing the run.
