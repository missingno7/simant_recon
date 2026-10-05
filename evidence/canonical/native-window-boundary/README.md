# Native window boundary evidence

This is a bounded static receipt for installed window ABI adapters and the
source observer/resource domain. `review.md` states the exact correspondence,
normalizations, native failure policies and unsupported cases. It does not
establish complete native-game parity or raw window-memory equality.

`installed-correspondence.json` records the installed files and their actual
hashes, plus the reviewed original/LF hashes and exact normalized-text identity.
`receipt.json` is the unmodified original audit receipt; draft/build paths there
are provenance, and neither it nor a historical checkout is needed by replay.
The annotated DOS `.txt` files retain instruction/address anchors. The full
`resources.json` records all 34 active shipped window records and asset hashes.
No game asset or executable is included in this evidence delivery.

Replay current source/helper controls with local game assets and a C11 compiler:

```powershell
python evidence/canonical/native-window-boundary/replay.py --out build/window-boundary-current
```

Use a fresh `--out` under repository `build/`. `--cc` can select a compiler.
The script verifies current audited source text and asset/resource identity,
then tests required 0/2/4 counts, missing/count-1 rejection before writes, and
successful int16 parameter stores on all actual records. It produces
`report.json`, `resources.json`, compiler output and the control executable
only under `build/`. Neither the permanent evidence nor sources are modified.

`manifest-statement.json` supplies a concrete replacement for the outdated
root:218D/window-ABI preview limitation; the actual owner is root:20E8 and both
win_Open and win_Swap normalize omitted words. The parent repository writer
chooses/applies the manifest row. The copy manifest is delivered separately,
so scratch paths do not become permanent evidence dependencies.
