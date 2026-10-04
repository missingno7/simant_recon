"""Append the separate frozen static tail review without rewriting other receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'work/source-only-dos/structural-audits-v32'

def pin(path):
    raw = path.read_bytes()
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(raw).hexdigest(), size=len(raw))

copies = []
sources = [(ROOT/'build/workers/dos_tail_bss_boundary_v32'/name, 'tail-bss-v32/'+name)
    for name in ('review-v32.md','probe_tail_bss_boundary_v32.py','tail-bss-boundary-v32.json')]
sources += [(Path(__file__).parent/'review_tail.py', 'root-review/review_tail.py'),
            (Path(__file__), 'root-review/preserve_tail.py'),
            (ROOT/'build/source-only-dos-tail-root-v32.log', 'root-review/tail.log'),
            (ROOT/'docs/exe-format.md', 'tail-bss-v32/exe-format-before-correction.md')]
for source, label in sources:
    target = OUT/label
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        assert target.read_bytes() == source.read_bytes()
    else:
        target.write_bytes(source.read_bytes())
    copies.append(dict(original=pin(source), archived=pin(target)))
decision = dict(schema='simant-v32-tail-root-review', root_reviewed=True,
    accepted_runtime_members_reverified_exact=90, input_pins_reopened=26,
    normal_startup_clear_interval='DGROUP:[8B9E,94F0)',
    tail_overlap_offsets=['8B9D','8B9E','8B9F'], written_offsets=['8B9E','8B9F'],
    excluded_offset='8B9D', source_physical_owner_or_fields_admitted=False,
    data_debt_discharged=0, game_executed=False,
    claim_limit='Normal CRT startup overwrites two bytes before initializers/main. '
                'No original-byte provider, independent placement, historical mastering mechanism, '
                'or first-byte harmlessness finding is made.',
    documentation_correction='Replace the overbroad all-three-inside-BSS statement with the exact clear interval.',
    worker_receipts_unchanged=True)
(OUT/'tail-root-review.json').write_bytes((json.dumps(decision, indent=2)+'\n').encode())
(OUT/'tail-preservation-index.json').write_bytes((json.dumps(dict(copies=copies,
    archive_only=[pin(OUT/'tail-root-review.json')]), indent=2)+'\n').encode())
print('Preserved seven unchanged tail artifacts; exact static write fact only, zero admission')
