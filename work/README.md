# work/ — kept worker artifacts

Worker scratch lives in `build/workers/NAME/` (untracked, disposable). This directory keeps
only the worker files that the docs, evidence, layout or sources cite, plus the handoff
deliverables (see docs/next-steps.md). Nothing here is canonical: sources, manifest and
registries are published only through the tools (promote.py, rename.py, symbols.py, …).

| Directory | What it holds |
|---|---|
| align/ | CODEALIGN-1 + root:19A9 boundary fix: FINDINGS, patch/, migrate.sh, sandbox_run.sh (ready to install, see docs/next-steps.md §4) |
| autosearch/ | rule-driven search results (results.md/json), best drafts per function (runs/*/best.c), promote --note patch |
| resI/, resJ/, resE/, resF/, resG/, resH/, s09/, mem/, win/, resC/ | best drafts and residue notes of the still-open functions (resI/survey.txt, resJ/residue.txt) |
| rtlink/ | RTLink trial-link findings, experiments, derived link script (linkscripts/SIMANT_derived.lnk), proposal patch |
| vec/ | VEC-1 evidence: vector table classification and scripts |
| link/ | whole-build harness design notes, collect hook patch, unit tests |
| audit/ | adversarial audit report (findings F-1..F-14, all addressed by the gate) |
| asmrole/ | genuine-vs-C classification scripts and probes (result: evidence/asm-classification.json) |
| data/, relorder/ | S27 data map and relocation-order experiments |
| ovlA/, misc/, rt/ | d2a generator versions named in manifest source_origin, ASM-2 probe, SZ expander (unsz.py) |
| big/, zifix/, rootD/, rootF/, snd/ | minimal reproducers cited by docs/codegen-rules.md and asm_evidence |
