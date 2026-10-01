from pathlib import Path
import sys, json, itertools, hashlib
sys.path.insert(0, 'tools')
import csrc, modctx, variants

name = 'win_DrawBitMap'
ctx = modctx.resolve(func=name)
base = Path('work/takeover/residue-controls/bitmap-original-order.c').read_text(encoding='utf-8')
f = csrc.Source(base).function(name)
body = base[f.body.s:f.body.e]
out = Path('build/workers/fleet_root/bitmap-actual-args')
out.mkdir(parents=True, exist_ok=True)
vs = [('base', base, '')]

def whole(b):
    return base[:f.body.s] + b + base[f.body.e:]

def flag_body(b, typ, place):
    b = b.replace('    unsigned int n;', '    unsigned int n;\n    ' + typ + ' flag;')
    if place == 'entry':
        b = b.replace('    h = db_LoadObject', '    flag = 0;\n    h = db_LoadObject', 1)
    elif place == 'loaded':
        b = b.replace('        pic = ', '        flag = 0;\n        pic = ', 1)
    elif place == 'type3':
        b = b.replace('        if (pic->type == 3) {', '        if (pic->type == 3) {\n            flag = 0;')
    elif place == 'branches':
        b = b.replace('                x1 = ', '                flag = 0;\n                x1 = ')
    b = b.replace(', x & 1, 0);', ', x & 1, flag);').replace(', x & 7, 0);', ', x & 7, flag);')
    return b

for typ, place in itertools.product(['int', 'unsigned', 'unsigned char'], ['entry', 'loaded', 'type3', 'branches']):
    vs.append((f'flag-{typ}-{place}', whole(flag_body(body, typ, place)), 'Existing zero overlay-call argument, initialized on every path before use'))

for typ in ['int', 'unsigned', 'unsigned char']:
    b = body.replace('    unsigned int n;', '    unsigned int n;\n    ' + typ + ' kind;')
    b = b.replace('    h = db_LoadObject(id, 2);', '    kind = 2;\n    h = db_LoadObject(id, kind);').replace('db_ReleaseObject(id, 2);', 'db_ReleaseObject(id, kind);')
    vs.append((f'kind-{typ}', whole(b), 'Existing object-kind argument, shared by load and release'))
    for place in ['entry', 'type3']:
        vs.append((f'kind-{typ}-flag-{place}', whole(flag_body(b, 'int', place)), 'Real object kind and overlay flag arguments'))

for typ, place in itertools.product(['int', 'unsigned'], ['entry', 'loaded']):
    b = body.replace('    unsigned int n;', '    unsigned int n;\n    ' + typ + ' success;')
    b = b.replace('return 1;', 'return success;')
    if place == 'entry':
        b = b.replace('    h = db_LoadObject', '    success = 1;\n    h = db_LoadObject', 1)
    else:
        b = b.replace('        pic = ', '        success = 1;\n        pic = ', 1)
    vs.append((f'success-{typ}-{place}', whole(b), 'Real later return value, initialized before all successful returns'))
    vs.append((f'success-{typ}-{place}-flag', whole(flag_body(b, 'int', 'entry')), 'Real return value and later overlay flag'))

rows = variants.run(ctx, vs, extra_funcs=[name], claims_only=True, jobs=2, out_dir=out)
for row, (_, source, _) in zip(rows, vs):
    row['source_sha256_lf'] = hashlib.sha256(source.encode()).hexdigest()
    r = row['result']
    t = r.get('claims', {}).get(name, {})
    losses = [c['name'] for c in ctx.claims if not r.get('claims', {}).get(c['name'], {}).get('exact')]
    print(row['name'], t, 'peer losses', losses, flush=True)
(out / 'results.json').write_text(json.dumps({'function':name, 'profile':ctx.profile, 'flags':ctx.flags, 'variants':rows}, indent=1)+'\n', encoding='utf-8')
