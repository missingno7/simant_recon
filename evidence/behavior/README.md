# Separate behavioral evidence registry

`manifest.json` is independent of `layout/manifest.json` and `evidence/promotions.jsonl`.
It begins with the 29 open hard-tail functions marked `UNRESOLVED`. Existing `EXACT`
claims remain owned by the historical acceptance flow. These tools never write
historical source, object, layout, or promotion files.

## Evidence packet

An input packet uses schema `simant-behavior-evidence-v1`. It must pin:

- the complete whole-module source path and SHA-256;
- the behavior suite source and suite ID;
- the exact imported `tools/behavior.py` bytes plus all execution/compiler/Binder
  dependencies listed in `tools/behavior_validate.py` (including `layout/toolchain.json`
  and `tools/behavior_ledger.py`);
- the original `assets/SIMANT.EXE`, `layout/oracle.lock.json`, and current
  `layout/manifest.json` hashes;
- a reviewed test contract, a complete run report, and a negative-control report;
- the known historical residue, reason exact reconstruction stopped, source/semantic
  evidence, evidence date, and source checkpoint.

The run report schema `behavior-run-evidence-v1` requires completed directed and
randomized lanes, per-lane generated and executed counts, actual original and
candidate invocation counts, zero errors and mismatches, the exact compared effects,
and zero unmodeled boundaries. Its SHA-pinned JSONL case ledger must have one unique
  row per invocation, attest execution in both VMs, hash each controlled input and
  both normalized observations, and compare every required effect for each case.
  Equal cases must have identical normalized observation hashes. Use deterministic
  gzip JSONL (`.jsonl.gz`) for large campaigns; the report pins compressed bytes,
  row count, lane counts, and run identity. It must identify the
`PreparedPair.compare` execution path, compiler profile/flags, and pass whole-module
peer/private-data checks. A modeled or trace-only helper
must have its own pinned `behavior-helper-cert-v1` record, a positive and detected
negative control, and an approved review. Simulation helpers receive the same gate.

The negative-control report schema `behavior-negative-controls-v1` pins the source,
oracle, harness and historical manifest identity, and pins each mutant source and
compiled object. It must show every expected mismatch was detected with no execution
error. A passing original-vs-candidate suite without sensitivity controls is
insufficient.

Use `CaseLedger(path, pair, compared_effects)` from `tools/behavior_ledger.py`; call
`record(case, result, lane=...)` immediately after each completed
`PreparedPair.compare(case)`, then place `finalize()`'s returned report in
`run_report.case_ledger`. The ledger normalizes final observations to return value,
observed ranges, call trace, I/O, state, preserved registers and final bytes in the
union of modified non-stack addresses. It excludes execution block counts, raw
traces and write-history addresses alone.

The runner is the byte snapshot captured by `HARNESS_SOURCE` when the pair was
prepared. If that differs from current `tools/behavior.py`, retain the exact snapshot
under `evidence/behavior/harnesses/<run-id>/tools/behavior.py` and include an approved
`runner_snapshot_review` explaining why it is the harness that ran. Each compiler,
Binder and executor component must still match its current hash unless that exact
component file is also retained at the corresponding path in the same harness bundle
and explicitly included in that review. A source report cannot silently bless stale
components. Suite source, candidate source, original EXE and historical manifest
must match current pins at verification time.

## Read-only verification and explicit registration

First validate and write a receipt:

```powershell
python tools/behavior_promote.py --verify-only evidence/behavior/runs/SpiderScan.json `
  --receipt build/workers/behavior/SpiderScan/verified.json
```

After the supervisory agent has reviewed the concrete contract and evidence,
explicitly register:

```powershell
python tools/behavior_promote.py --register evidence/behavior/runs/SpiderScan.json `
  --receipt build/workers/behavior/SpiderScan/verified.json `
  --reviewed-by "reviewer" --review-note "reviewed differential boundary and evidence"
```

Registration revalidates all files and hashes and requires the registry to remain
unchanged since verify-only. Verification recompiles the complete pinned module using
the current historical compiler context, and checks object, compiled-source, profile,
flags and whole-module peer/data gates against the run report. The registry row then becomes `BEHAVIOR_EXACT` and pins
the evidence packet hash. Registered packets are immutable through this tool. Run
`python tools/behavior_validate.py --all` for a read-only integrity audit and separate
EXACT/BEHAVIOR_EXACT/UNRESOLVED function counts; historical nonfunction/data claims
are reported separately. No packet is currently registered.
