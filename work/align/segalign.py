"""Which SEGDEF alignment does each pinned compiler/option set give the code segment?"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
from omf import OmfReader
SRC = "int g;\nint f(int a){ return a+g; }\nvoid h(void){}\n"
CASES = [(p, fl) for p, fl in [
    ('msc600ax', ['/AL', '/Os']), ('msc600ax', ['/AL', '/Os', '/Oeg', '/Gs', '/Zi']),
    ('msc600ax', ['/AL', '/Os', '/NT', 'DB_TEXT']), ('msc600ax', ['/AL', '/Ox']), ('msc600ax', ['/AL', '/Od', '/Zi']),
    ('msc600ax', ['/AL', '/Os', '/Gw']), ('msc600ax', ['/AL', '/Os', '/G2']), ('msc600ax', ['/AL', '/Os', '/Gc']),
    ('msc600ax', ['/AL', '/Os', '/Za']), ('msc600ax', ['/AL', '/Os', '/Zp1']), ('msc600ax', ['/AL', '/f-']),
    ('msc600', ['/AL', '/Os']), ('msc600a', ['/AL', '/Os']), ('msc510', ['/AL']), ('msc510', ['/AL', '/Os']),
    ('qc250', ['/AL']), ('qc251', ['/AL']), ('qc251', ['/AL', '/Ox'])]]
out = []
for p, fl in CASES:
    try:
        r = compiler.compile_c(SRC, p, fl)
    except Exception as e:
        out.append((p, fl, 'ERR ' + str(e))); continue
    if not r.ok:
        out.append((p, fl, 'FAIL ' + r.log[-200:])); continue
    o = OmfReader(communals=True).read(r.obj)
    out.append((p, fl, [(s['name'], s.get('class'), s['alignment']) for s in o.segment_defs]))
for row in out:
    print(row)
Path(__file__).with_name('segalign.json').write_text(json.dumps(out, indent=1))
