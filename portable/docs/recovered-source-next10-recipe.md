# Reviewed History UI profile

Next10 extends the reviewed Next9 profile with one bounded native lowering in
S24 and a read-only accessor for the source-owned private History UI arrays.
The original removal copies one word beyond shownGraphs and then overwrites
that destination word with its sentinel. The native copy preserves the four
resulting list elements while avoiding that host out-of-bounds read. Historical
sources and the original DOS oracle retain the original operation.

The [paired event receipt](../tests/history_event_lowering/comparison_report_closure_next10.json)
checks 29 original-DOS/native events, including every removal position and full
list eviction. Its negative control detects the original one-past access. The
receipt records all 25 TU dependency closures and stable source, evaluator,
header, object, oracle, and parent identities. Earlier diagnostic profiles and
receipts remain archived with their original metadata defects.

After reproducing the [reviewed Next9 inputs](recovered-source-next9-recipe.md),
run from the repository root:

```powershell
python portable/tools/recover_source_next10.py
python portable/tests/recovered/test_next10_admission.py
python portable/build.py --core-profile build/workers/recovered_source_next10/generated
```

The producer reads the reviewed Next9 snapshot and copies it into its own output
directory. It never regenerates or modifies Next9. Exactly one generated C file
changes; all 25 TUs are recompiled with their inherited warning policy. Current
source paths and primary object hashes identify the actual Next10 inputs, with
parent object hashes separately retained as historical metadata.

The build validates the unchanged Next9 parent through every existing profile
gate, then checks the complete reviewed Next10 metadata and actual source/header
copies independently. Nine negative admission controls reject altered ancestry,
source state, unrelated modules, removal width, accessor extent, missing modules,
stale object identity, and stale source paths. This admits an explicit native
profile; it changes no frozen EXACT or BEHAVIOR_EXACT claim.
