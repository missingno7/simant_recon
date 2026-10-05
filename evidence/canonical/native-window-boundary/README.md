# Native window boundary evidence

This is a bounded static receipt for installed window ABI adapters and the
source observer/resource domain. It does not establish complete native-game
parity or raw window-memory equality.

`review.md` describes the bounded correspondence, normalizations, native failure
policies and unsupported cases. `portable/platform.json` records the current
window-ABI limitation. `receipt.json` is the original audit receipt; its draft
and build paths are provenance, not replay dependencies. The annotated DOS
`.txt` files retain instruction/address anchors. `resources.json` records the
active shipped window records and asset hashes. No game asset or executable is
included in this evidence delivery.

Replay current source/helper controls with local game assets and a C11 compiler:

```powershell
python evidence/canonical/native-window-boundary/replay.py --out build/workers/native-window-boundary/replay-run-001
```

Use a fresh `--out` under repository `build/`. `--cc` can select a compiler.
The script verifies current audited source text and asset/resource identity,
then tests required 0/2/4 counts, missing/count-1 rejection before writes, and
successful int16 parameter stores on all actual records. It produces
`report.json`, `resources.json`, compiler output and the control executable
only under `build/`. Neither the permanent evidence nor sources are modified.

The current optional-word contract is registered in `portable/platform.json`
and classified in `layout/repository.json`; the original static receipt remains
evidence for its bounded source-observer/resource domain.
