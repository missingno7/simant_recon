from pathlib import Path
import sys, json, hashlib
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import autosearch, csrc, modctx
name = 'win_UnlockWin'
ctx = modctx.resolve(func=name)
base = (ROOT / 'build/workers/ptr_unlock/base.c').read_text(encoding='latin1')
fn = csrc.Source(base).function(name)
body = base[fn.body.s:fn.body.e]
old = 'obj = w->objs[i];'
assert old in body
out = ROOT / 'build/workers/ptr_unlock'
variants = []
forms = [
    ('member_add', 'obj = *(w->objs + i);'),
    ('member_first_address_add', 'obj = *(&w->objs[0] + i);'),
    ('typed_byte_base_add', 'obj = *((struct Obj far * far *)((char far *)w + 0x2c) + i);'),
    ('byte_base_add', 'obj = *((struct Obj far * far *)((char far *)w + sizeof(struct Rect) + 0x24) + i);'),
    ('member_unsigned_add', 'obj = *(w->objs + (unsigned)i);'),
    ('member_add_parens', 'obj = *(i + w->objs);'),
]
for label, expr in forms:
    variants.append((label, base[:fn.body.s] + body.replace(old, expr) + base[fn.body.e:]))
for label, init in [
    ('local_member_add', 'objects = w->objs;'),
    ('local_typed_base_add', 'objects = (struct Obj far * far *)((char far *)w + 0x2c);'),
]:
    b = body.replace('    struct Win far *w;\n', '    struct Win far *w;\n    struct Obj far * far *objects;\n')
    b = b.replace('                w = *h;', '                w = *h;\n                ' + init)
    b = b.replace(old, 'obj = *(objects + i);')
    variants.append((label, base[:fn.body.s] + b + base[fn.body.e:]))
for label, init in [
    ('local_member_add_after_loop_vars', 'objects = w->objs;'),
    ('local_typed_base_add_after_loop_vars', 'objects = (struct Obj far * far *)((char far *)w + 0x2c);'),
]:
    b = body.replace('    struct Win far *w;\n', '    struct Win far *w;\n    struct Obj far * far *objects;\n')
    b = b.replace('                w = *h;', '                w = *h;\n                ' + init)
    b = b.replace(old, 'obj = *(i + objects);')
    variants.append((label, base[:fn.body.s] + b + base[fn.body.e:]))
for label, text in variants:
    (out / f'{label}.c').write_text(text, encoding='latin1', newline='\n')
    print(label, hashlib.sha256(text.encode('latin1')).hexdigest())
cache = out / 'cache'
ev = autosearch.Evaluator(ctx, name, 2, cache)
rows = []
for (label, text), r in zip(variants, ev.many([text for _, text in variants])):
    row = {'name': label, 'source_sha256': hashlib.sha256(text.encode('latin1')).hexdigest(), **r}
    rows.append(row)
    print(label, r.get('score'), 'all_exact=', r.get('all_exact'), 'length=', r.get('length'), 'reasons=', r.get('reasons'))
ev.save()
(out / 'expression-address-results.json').write_text(json.dumps(rows, indent=1) + '\n')
