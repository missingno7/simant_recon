from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='win_DrawBitMap';text=(ROOT/'build/workers/takeover/bitmap-original-order.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/bitmap-aligned-coordinate';out.mkdir(exist_ok=True);vs=[]
for typ,nword,branchcache in itertools.product(['int','unsigned int'],['int','unsigned int'],[False,True]):
 bb=b.replace('    int x1;', '    '+typ+' alignedX;\n    int x1;').replace('    unsigned int n;', '    '+nword+' n;')
 bb=bb.replace('x & ~1', 'alignedX').replace('x & ~7', 'alignedX')
 bb=bb.replace('            if (g_5A97 == 2) {','            if (g_5A97 == 2) {\n                alignedX = x & ~1;').replace('                x1 = ((alignedX) + pic->width + 15)', '                alignedX = x & ~7;\n                x1 = ((alignedX) + pic->width + 15)')
 if branchcache:bb=bb.replace('h = malloc((*g_9140)(alignedX, y, x1, y1));','n = (*g_9140)(alignedX, y, x1, y1);\n                h = malloc(n);')
 assert 'alignedX = x & ~7;' in bb
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))])
