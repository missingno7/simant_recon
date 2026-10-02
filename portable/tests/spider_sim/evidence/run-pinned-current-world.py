import hashlib, json, subprocess, sys
from pathlib import Path
root=Path('.')
report=Path('build/portable/spider-tick-current-world-10146.json')
paths=[
 'portable/game/simulation/spider_sim.c','portable/game/simulation/spider_sim.h',
 'portable/game/simulation/spider.c','portable/game/simulation/spider.h',
 'portable/game/simulation/rng.c','portable/game/simulation/rng.h',
 'portable/game/simulation/movement.c','portable/game/simulation/movement.h',
 'portable/game/state/world.h','portable/tests/spider_sim/native_bridge.c',
 'portable/tests/spider_sim/run_dos_diff.py','tools/behavior.py',
 'tools/functions.py','tools/exe.py','src/root/m0CDB.c','src/root/m0894.c',
 'assets/SHARED.NDX','assets/SHARED.DAT'
]
def digest(p): return hashlib.sha256((root/p).read_bytes()).hexdigest()
before={p:digest(p) for p in paths}
proc=subprocess.run([sys.executable,'portable/tests/spider_sim/run_dos_diff.py',
 '--random-count','10134','--report',str(report)],check=False)
after={p:digest(p) for p in paths}
receipt={
 'schema':'native-dos-movespider-run-receipt-v1',
 'status':'source-stable' if before==after else 'source-mutated-during-run',
 'source_hashes_before':before,'source_hashes_after':after,
 'report_sha256':digest(report) if report.exists() else None,
 'report':str(report),'runner_exit_code':proc.returncode
}
Path('build/portable/spider-tick-current-world-10146-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
if before!=after:
 raise SystemExit('source changed during run')
if proc.returncode:
 raise SystemExit(proc.returncode)
