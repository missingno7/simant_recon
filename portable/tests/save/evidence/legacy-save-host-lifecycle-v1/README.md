# Legacy save/load host lifecycle contract, V1

`contract.json` records the source-grounded sequence and side effects for `LoadGame`, `SaveGame`, the file selector, the dirty-state prompt, load reset/rebuild helpers, and `RandYard`. It gives the integration owner explicit DOS behavior to preserve or deliberately version when defining the real host file service.

Load selection clears the dirty flag before opening, calls `RandYard` before reading any saved record, mutates rows directly, accepts no read unless one call returns the full row length, and does not roll back after a later failure. `RandYard` clears arrays and control state, sets yard dimensions, generates 192 seed-table words with `RRand`, passes one to `RandWorld` (which initializes S-RNG), and restores the active ant location before the first read. Save treats only `write == -1` as failure, ignores close results, does not truncate a previously existing file after overwrite confirmation, and clears dirty before success reporting and close. These are original implementation facts, not recommendations for a safe modern filesystem API.

Regenerate from the repository root with:

```powershell
python portable/tests/save/write_lifecycle_contract.py
```

The contract pins exact function-body hashes and the 307-row stream inventory. It does not implement or certify a filesystem service. A staged/atomic load, write-all loop, or automatic truncation would be a deliberate behavioral policy change and should be separated from source-compatible behavior.
