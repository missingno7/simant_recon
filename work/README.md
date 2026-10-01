# work/ â€” kept worker artifacts

Worker scratch lives in `build/workers/NAME/` (untracked, disposable). This directory keeps
only the worker files that the docs, evidence, layout or sources cite, plus the handoff
deliverables (see docs/next-steps.md). Nothing here is canonical: sources, manifest and
registries are published only through the tools (promote.py, rename.py, symbols.py, â€¦).

| Directory | What it holds |
|---|---|
| align/ | CODEALIGN-1 and root:19A9 boundary fix: installed and validated; archived patch and experiments are historical references |
| autosearch/ | rule-driven search results (results.md/json), best drafts per function (runs/*/best.c), archived promote --note patch (already installed) |
| resI/, resJ/, resE/, resF/, resG/, resH/, s09/, mem/, win/, resC/ | best drafts and residue notes of the still-open functions (resI/survey.txt, resJ/residue.txt) |
| takeover/ | accepted game-code controls, current linker catalogue search, and checkpoint evidence |
| rtlink/ | RTLink trial-link findings, experiments, derived link script (linkscripts/SIMANT_derived.lnk), proposal patch |
| vec/ | VEC-1 evidence: vector table classification and scripts |
| link/ | whole-build harness design notes, collect hook patch, unit tests |
| audit/ | adversarial audit report (findings F-1..F-14, all addressed by the gate) |
| asmrole/ | genuine-vs-C classification scripts and probes (result: evidence/asm-classification.json) |
| data/, relorder/ | S27 data map and relocation-order experiments |
| ovlA/, misc/, rt/ | d2a generator versions named in manifest source_origin, ASM-2 probe, SZ expander (unsz.py) |
| big/, zifix/, rootD/, rootF/, snd/ | minimal reproducers cited by docs/codegen-rules.md and asm_evidence |

* `takeover/randworld/`: accepted 1,355-byte body, literal-zero/dead-y controls,
  ZERO-1 probe and refused complete-TU order controls; initializer explicitly STEERED.
* `takeover/exp-menu/`: accepted complete DoExpMenu TU and BYTE-1 low-byte controls.
* `takeover/adlib-setter/`: accepted setter and CONST-1 private-segment ordering controls;
  the earlier volume-function body remains unclaimed.
* `takeover/delta/`: accepted complete sample decoder TU, natural-C and inline-assembly
  controls, latest validation and whole-build check.
* `takeover/full-search/`: whole-module snapshots, with later acceptances marked;
  its 33-function snapshot predates later recovery (32 now remain; see docs/next-steps.md).
  Merge hypotheses into current sources and recheck all claims before acceptance.
* `takeover/antmove/`: accepted DoAntMoveY, STEERED USE-1 controls and full validation.
* `takeover/mpu/`: complete MPU TU, STEERED LIFE-1 controls, relocation-record
  label trials, acceptance validation and current hybrid check.
* `takeover/fileselect/`: complete saved-game/file-selector TU, USE-2 folded-use
  controls, one-byte and five-byte near drafts, validation and hybrid integration.
* `takeover/freeblock/`: 362-byte free-block acceptance, WIDTH-1 mixed-width
  paragraph-address controls, all-module verification, full 45-probe/test validation.
* `takeover/residue-controls/`: later compiler-residue searches, compact verdicts,
  unclaimed near sources and semantic cautions for historical search snapshots.
* `takeover/blockers/`: 909 additional failed whole-module variants, retained drafts,
  semantic cautions, full validation and identical-hybrid checkpoint evidence.
* `takeover/rtlink400/`: checksum-verifying toolkit extraction, pinned payload hashes,
  library inventory and paired 4.00/6.10 trial summaries; stock 4.00 manager excluded.
