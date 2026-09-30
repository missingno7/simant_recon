#!/bin/bash
# Sandbox proof of the CODEALIGN-1 patch (worker align).  Run from the repository root:
#   bash work/align/sandbox_run.sh
# 1. copies the repository (without build/) to a fresh build/workers/align/sb_<time>/;
# 2. baseline validate there with the unpatched tools;
# 3. installs the patch (tools/modules.py, tools/promote.py, tools/rtlink.py, tests/test_codealign.py,
#    tests/negatives/T13_m19A9_odd_start.c) and validates the UNCHANGED state (must refuse root:19A9
#    for CODEALIGN-1 only: a negative control on real data);
# 4. runs migrate.sh (drop-extent, reframe, re-promote) and validates again with the unit tests.
set -u
export MSYS_NO_PATHCONV=1
REPO=$(pwd)
A=$REPO/work/align
SB=$A/sb_$(date +%Y%m%d_%H%M%S)
L=$SB.logs
mkdir -p "$SB" "$L"
for d in AGENTS.md README.md assets docs evidence layout src tests tools; do cp -r "$d" "$SB/"; done
# validate checks that every build/ path named in an asm_evidence exists: copy those paths too
# (first run 2026-09-30 11:51 failed its baseline without them)
python - "$SB" <<'EOF'
import json, re, shutil, sys
from pathlib import Path
sb = Path(sys.argv[1])
man = json.loads(Path('layout/manifest.json').read_text())
for m in man['modules'].values():
    for p in re.findall(r'build/[\w./-]+', m.get('asm_evidence') or ''):
        p = p.rstrip('.,;')
        src, dst = Path(p), sb / p
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, dst)
EOF
md5sum tools/modules.py tools/promote.py tools/rtlink.py tools/validate.py > "$L/upstream_md5.txt"
cd "$SB"
echo "== baseline validate (unpatched tools)"; python tools/validate.py --no-tests > "$L/1_baseline_validate.log" 2>&1; echo "exit=$?"
cp docs/progress.json "$L/1_baseline_progress.json"
cp "$A/patch/tools_modules.py" tools/modules.py
cp "$A/patch/tools_promote.py" tools/promote.py
cp "$A/patch/tools_rtlink.py" tools/rtlink.py
cp "$A/patch/tests_test_codealign.py" tests/test_codealign.py
cp "$A/patch/T13_m19A9_odd_start.c" tests/negatives/T13_m19A9_odd_start.c
echo "== patched validate, unchanged state (expect: root:19A9 refused for CODEALIGN-1)"
python tools/validate.py --no-tests > "$L/2_patched_unchanged_validate.log" 2>&1; echo "exit=$?"
echo "== migration"; A="$A" bash "$A/migrate.sh" > "$L/3_migrate.log" 2>&1; echo "exit=$?"
echo "== validate after migration (with unit tests)"
python tools/validate.py > "$L/4_validate_after.log" 2>&1; echo "exit=$?"
cp docs/progress.json "$L/4_progress_after.json"
cd "$REPO"
python - "$L" <<'EOF'
import json, sys, pathlib
L = pathlib.Path(sys.argv[1])
a = json.loads((L / "1_baseline_progress.json").read_text())
c = json.loads((L / "4_progress_after.json").read_text())
print("baseline -> after migration:")
for k in sorted(set(a) | set(c)):
    if k != "generated" and a.get(k) != c.get(k):
        print(f"  {k}: {a.get(k)} -> {c.get(k)}")
EOF
echo "sandbox: $SB  logs: $L"
