#!/bin/bash
# The 1986/19A9 boundary correction (CODEALIGN-1), as the supervisor would run it on the canonical
# tree, in this order.  Run from the repository root (or a sandbox copy of it):
#   A=work/align bash work/align/migrate.sh
# Needs the patched tools/promote.py (--drop-extent).  Every step is a sanctioned writer:
# promote.py (manifest, src, journal) and functions.py reframe (function table + names registry).
set -eu
export MSYS_NO_PATHCONV=1
A=${A:-work/align}
WHY_ALIGN="CODEALIGN-1 (work/align/FINDINGS.json): an MSC 6.00 code segment is WORD aligned, so no object starts at the odd 19A95; the three unreferenced retf at 19A95-19A97 end the index module 1986 (Win16 index TU order OpenIndex, CreateIndex, CloseIndex, FindIndex, DeleteCurrentIndex, AddIndex, DeleteIndex; the DOS build stubs the write side empty like CreateIndex), and 19A9 starts at 19A9:0008"

echo "== 1. root:19A9 back to a partial module, stubs released (corrected source without them)"
python tools/promote.py "$A/m19A9.c" --module root:19A9 --drop-extent "$WHY_ALIGN" \
    --release "f_19A9_0005=$WHY_ALIGN" --release "f_19A9_0006=$WHY_ALIGN" --release "f_19A9_0007=$WHY_ALIGN"

echo "== 2. re-frame the three unreferenced rows to 1986 (same linear addresses)"
for o in 0005 0006 0007; do
    python tools/functions.py reframe "root:19A9:$o" 1986 "$WHY_ALIGN"
done

echo "== 3. root:1986 claims them (still partial: FindIndex is scaffold)"
python tools/promote.py "$A/m1986.c" --module root:1986 \
    --claim f_1986_0235 --claim f_1986_0236 --claim f_1986_0237

echo "== 4. root:19A9 complete TU again, at 19A98"
python tools/promote.py "$A/m19A9.c" --module root:19A9 --extent 19A98:19DC7
