import json
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
import compilerstate

worker = Path(__file__).resolve().parent
spec = {'function': 'FindIndex', 'base_source': str(worker / 'base.c'),
        'dimension': 'REFERENCED_CONTINUATION_GATE_RECHECK',
        'hypothesis': 'Preserve complete strict peer/data proof for four previously compiled worker controls. This is a gate recheck, not a new source-search dimension.',
        'diagnostic_only': False,
        'variants': [{'parameters': {'form': p.stem, 'purpose': 'missing-persistent-full-gate-proof'}, 'source': str(p)}
                     for p in sorted(worker.glob('v*.c'))]}
out = Path('build/workers/hardtail_root/index-gate-recheck')
out.mkdir(parents=True, exist_ok=True)
(out / 'spec.json').write_text(json.dumps(spec, indent=1))
compilerstate.run(spec, out, Path('build/workers/hardtail_root/experiments-index-gates.jsonl'),
                  [Path('work/takeover/hardtail/experiments.jsonl')])
