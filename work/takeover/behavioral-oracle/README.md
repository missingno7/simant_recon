# Behavioral oracle inventory and current status

Current snapshot (2026-10-02): see [current-status.md](current-status.md) for the six registered BEHAVIOR_EXACT functions, 23 remaining behavioral targets, and current 113-byte data debt. The inventory below remains the original dated 2026-10-01 baseline and is intentionally unchanged.

This directory preserves the original dated inventory for the two-proof system. It does not
alter canonical sources, ownership, historical validation, promotions, or EXACT
claims. Its per-function status is the 2026-10-01 baseline; use current-status.md
and the separate behavior registry for the updated state.

`inventory.json` is the machine-readable record. `inventory.md` is its compact
29-function view. Rebuild both from the retained main hard-tail report and catalog:

```powershell
python tools/behavior_inventory.py --out work/takeover/behavioral-oracle/inventory.json
```

The builder binds the source report hash, catalog-selected whole-module source and
source hash, original target/candidate extents, diagnostic CFG/skeleton, relocation
sites, retained negative-search references, exact-name cross-version evidence, and
per-function proposed oracle boundary. The 29 function extents sum to 15,039 bytes;
the separate 316 code-span bytes and 129 data bytes remain open historical debt.

The category labels describe current source-level purpose. They are not proof of
behavioral correctness. Original normalized streams preserve far-call sites and
relocations, but those bound markers do not identify the target symbol names; the
current source declarations are hypotheses for the dependency ABI until the DOS
oracle can trace them.

The three simulation contracts are intentionally more detailed. SpiderScan has a
HIGH Win16 correspondence, but only differential execution can establish that the
candidate's omitted BP-2 initialization is unobservable. EnterNest's matching
normalized skeleton and CFG support a register-allocation explanation, but helper
effects still require comparison. GetMyRandDirs currently has a CFG mismatch; its
source predicates must be reconciled before large randomized results could support
closure.

Use `EXACT` only with the existing historical gate and retain its evidence. Use
`BEHAVIOR_EXACT` only after a reproducible harness runs both implementations from
equivalent controlled state, compares the function-specific observable boundary,
records domain and seeds, and reports zero unexplained mismatches. No such proof is
claimed by this draft.
