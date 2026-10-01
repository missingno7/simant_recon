from pathlib import Path
import json, sys, hashlib
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / 'tools'))
import csrc, modctx, variants
out = ROOT / 'build' / 'workers' / 'fleet_index'
base_path = out / 'findindex-base.c'
base = base_path.read_text(encoding='latin1')
ctx = modctx.resolve(func='FindIndex', source=base_path)
f = csrc.Source(base).function('FindIndex')
body0 = base[f.body.s:f.body.e]
k = 'fd_50F6_3952->kind'
i = 'fd_50F6_3952->id'
arr = 'fd_50F6_3958[db].index'
lo = 'fd_50F6_3956'
cond = f'!({k} < kind || ({k} == kind && {i} < id))'
items = []
def change(label, text, rationale):
    items.append((label, text, rationale))
def edit_body(label, replacement, rationale):
    source = base[:f.body.s] + replacement + base[f.body.e:]
    change(label, source, rationale)
# Bounds placement controls: bottom remains zeroed before all empty-index returns.
for label, pre in [
 ('count-check-before-bound', '    fd_50F6_3956 = 0;\n    if (fd_50F6_3958[db].indexHeader.count == 0)\n        return 0L;\n    top = fd_50F6_3958[db].indexHeader.count - 1;'),
 ('cached-count-check-before-bound', '    int count;\n    fd_50F6_3956 = 0;\n    count = fd_50F6_3958[db].indexHeader.count;\n    if (count == 0)\n        return 0L;\n    top = count - 1;'),
 ('bound-zero-check-before-decrement', '    fd_50F6_3956 = 0;\n    top = fd_50F6_3958[db].indexHeader.count;\n    if (top == 0)\n        return 0L;\n    --top;'),
 ('cached-bound-zero-check-before-decrement', '    int count;\n    fd_50F6_3956 = 0;\n    count = fd_50F6_3958[db].indexHeader.count;\n    top = count;\n    if (top == 0)\n        return 0L;\n    --top;'),
]:
    b = body0.replace('    fd_50F6_3956 = 0;\n    top = fd_50F6_3958[db].indexHeader.count - 1;\n    if (top == -1)', pre + '\n    if (top == -1)')
    edit_body(label, b, 'Same inclusive interval and empty-table result; changes where the zero-count test occurs.')
# Current-entry acquisition/lifetime controls.
def rep_body(old, new):
    assert old in body0, old
    return body0.replace(old, new)
old_assign = '        fd_50F6_3952 = &fd_50F6_3958[db].index[mid];\n'
for label, header, acquire, pred, reason in [
 ('local-current-pointer', '    IndexEntry far *entry;\n', '        entry = &fd_50F6_3958[db].index[mid];\n        fd_50F6_3952 = entry;\n', cond.replace('fd_50F6_3952->', 'entry->'), 'Acquires the current record in a real local, retaining the global pointer assignment and final global result.'),
 ('local-pointer-addition', '    IndexEntry far *entry;\n', '        entry = fd_50F6_3958[db].index + mid;\n        fd_50F6_3952 = entry;\n', cond.replace('fd_50F6_3952->', 'entry->'), 'Uses equivalent far-array pointer addition and a live current-record local.'),
 ('cached-kind-local', '    IndexEntry far *entry;\n    unsigned char currentKind;\n', '        entry = &fd_50F6_3958[db].index[mid];\n        fd_50F6_3952 = entry;\n        currentKind = entry->kind;\n', cond.replace(k, 'currentKind').replace(i, 'entry->id'), 'Keeps the record pointer and a byte-sized kind value live across the decision; record fields are unchanged.'),
 ('cached-fields-locals', '    IndexEntry far *entry;\n    unsigned char currentKind;\n    int currentId;\n', '        entry = &fd_50F6_3958[db].index[mid];\n        fd_50F6_3952 = entry;\n        currentKind = entry->kind;\n        currentId = entry->id;\n', cond.replace(k, 'currentKind').replace(i, 'currentId'), 'Caches the two compared fields from the just-acquired record before the decision.'),
]:
    b = rep_body(old_assign, acquire)
    b = b.replace(cond, pred)
    # Add new locals immediately before top, after the existing mid local.
    b = b.replace('    int top;\n', header + '    int top;\n')
    edit_body(label, b, reason)
# Keep one local record pointer through the post-loop exact-key check as well.
entry_src = 'IndexEntry far * far FindIndex(int db, int id, int kind)\n{\n    int mid;\n    int top;'
entry_dst = 'IndexEntry far * far FindIndex(int db, int id, int kind)\n{\n    int mid;\n    int top;\n    IndexEntry far *entry;'
b = body0.replace(old_assign, '        entry = &fd_50F6_3958[db].index[mid];\n        fd_50F6_3952 = entry;\n')
b = b.replace('    int top;\n', '    int top;\n    IndexEntry far *entry;\n')
b = b.replace(cond, cond.replace('fd_50F6_3952->', 'entry->'))
b = b.replace('    fd_50F6_3952 = &fd_50F6_3958[db].index[fd_50F6_3956];\n    if (fd_50F6_3952->id == id && fd_50F6_3952->kind == kind)\n        return fd_50F6_3952;', '    entry = &fd_50F6_3958[db].index[fd_50F6_3956];\n    fd_50F6_3952 = entry;\n    if (entry->id == id && entry->kind == kind)\n        return entry;')
edit_body('local-pointer-through-final-check', b, 'Uses the acquired record local in-loop and for the final exact-key check; preserves the final global pointer value.')
# Two equivalent half-open lower-bound algorithms, with explicit out-of-range protection.
header = '    int count;\n    int bottom;\n    IndexEntry far *entry;'
for label, mid_expr in [('exclusive-upper-sum-midpoint', '(bottom + top) / 2'), ('exclusive-upper-difference-midpoint', 'bottom + (top - bottom) / 2')]:
    fn = '''IndexEntry far * far FindIndex(int db, int id, int kind)\n{\n    int top;\n    int count;\n    int bottom;\n    IndexEntry far *entry;\n\n    count = fd_50F6_3958[db].indexHeader.count;\n    fd_50F6_3956 = 0;\n    bottom = 0;\n    top = count;\n    while (bottom < top) {\n        int mid;\n        mid = ''' + mid_expr + f''';\n        entry = &fd_50F6_3958[db].index[mid];\n        fd_50F6_3952 = entry;\n        if (entry->kind < kind || (entry->kind == kind && entry->id < id))\n            bottom = mid + 1;\n        else\n            top = mid;\n    }}\n    if (bottom >= count)\n        return 0L;\n    entry = &fd_50F6_3958[db].index[bottom];\n    fd_50F6_3952 = entry;\n    if (entry->id == id && entry->kind == kind)\n        return entry;\n    return 0L;\n}}'''
    full = base[:f.head_s] + fn + base[f.body.e:]
    change(label, full, 'Equivalent lower-bound search over [0,count); adds an explicit count guard before the final record read.')
# Run whole module verification (manifest claims/data plus FindIndex) with the manifest context.
(out/'initial').mkdir(parents=True, exist_ok=True)
rows = variants.run(ctx, [('base', base, '')] + [(a, t, '') for a, t, _ in items], extra_funcs=['FindIndex'], claims_only=True, jobs=2, out_dir=out/'initial')
result_rows = []
for row, item in zip(rows[1:], items):
    label, text, rationale = item
    r = row['result']
    target = r.get('claims', {}).get('FindIndex', {})
    result_rows.append({'name': label, 'rationale': rationale, 'source_sha256': hashlib.sha256(text.encode('latin1')).hexdigest(), 'whole_module_exact': r.get('exact'), 'findindex': target, 'compile_ok': r.get('compile_ok'), 'warnings': r.get('warnings', [])})
(out/'initial-results.json').write_text(json.dumps({'module':ctx.key,'profile':ctx.profile,'flags':ctx.flags,'placements':ctx.placements,'existing_claims':[c['name'] for c in ctx.claims],'data_results':rows[0]['result'].get('data',{}),'variants':result_rows}, indent=2, default=str))
print('module',ctx.key,'profile',ctx.profile,'flags',ctx.flags,'placements',ctx.placements,'claims',[c['name'] for c in ctx.claims])
print('variants',len(items),'exact',sum(bool((x.get('findindex') or {}).get('exact')) for x in result_rows))
for x in result_rows:
    print(x['name'], 'compile',x['compile_ok'],'FindIndex',((x.get('findindex') or {}).get('exact'),(x.get('findindex') or {}).get('size'),(x.get('findindex') or {}).get('reason')),'module_exact',x['whole_module_exact'],x['source_sha256'])
