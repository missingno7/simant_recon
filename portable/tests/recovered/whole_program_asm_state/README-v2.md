# Fixed whole-program state plan v2

The v2 plan is frozen in `plan_v2.json` and records the reviewed v1 receipt
identity, immutable source/layout pins, archived generated consumer TU fixtures,
exact source declarations, and the resolved alias decisions. The runner does
not read or recollect aliases from the current `migration.json`.

Its one lexical pass renames the four scalar views to the canonical globals
(`g_19C0`, `g_19C6`, `g_19CA`, `g_19CE`) and maps the two interior pointers
`fd_55B3_1CE0` and `fd_55B3_1CE4` to entries 3 and 4 of the already-owned
`fd_55B3_1CD4` table. The pass leaves the table-base identifier itself
untouched and adds no storage owner. It also compiles the existing three-scalar
EMS provider without changing it.

Run `python portable/tests/recovered/whole_program_asm_state/validate_historical_pins_v2.py`
to check the fixed historical source and fixture hashes. Run
`python portable/tests/recovered/whole_program_asm_state/run_proof_v2.py` to
recreate the immutable receipt at
`portable/tests/recovered/evidence/whole-program-asm-state-v2/report.json`;
that command refuses to overwrite an existing report. The receipt covers
source/declaration/address controls and native compile-only checks, not a link,
runtime EMS test, or production integration.
