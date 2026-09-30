"""survey.py: for each module with scaffold, unscaffold the canonical source and report each
scaffold function's residue (via tools/variants.py)."""
import json
import os
import re
import subprocess
import sys
import glob

ROOT = os.getcwd()
m = json.load(open('layout/manifest.json'))['modules']
out = open('work/resI/survey.txt', 'w')
keys = sys.argv[1:] or [k for k, r in m.items() if r.get('scaffold')]
for k in keys:
    r = m[k]
    src = open(r['source']).read()
    u = re.sub(r'/\* SCAFFOLD BEGIN:.*?\*/\n', '', src, flags=re.S).replace('/* SCAFFOLD END */\n', '')
    fn = 'build/workers/resI/surv_%s.c' % k.replace(':', '_').replace('@', '_')
    open(fn, 'w').write(u)
    env = dict(os.environ, MSYS_NO_PATHCONV='1', MSYS2_ARG_CONV_EXCL='*')
    cmd = [sys.executable, 'tools/variants.py', fn, '--module', k, '--funcs'] + r['scaffold'] + ['--quiet', '--claims-only']
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    d = sorted(glob.glob('build/helpers/variants/*'))[-1]
    try:
        res = json.load(open(os.path.join(d, 'results.json')))
        cl = res['variants'][-1]['result'].get('claims', {})
    except Exception as e:
        cl = {}
    for f in r['scaffold']:
        x = cl.get(f, {})
        line = '%-12s %-28s %s %s' % (k, f, 'E' if x.get('exact') else '.', '; '.join(x.get('reasons', []))[:150])
        print(line)
        out.write(line + '\n')
    out.flush()
