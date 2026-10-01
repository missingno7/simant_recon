from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='win_DrawBitMap';text=autosearch.unscaffold((ROOT/'src/root/m259D.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/bitmap-buffer-lifetimes';out.mkdir(exist_ok=True);vs=[]
for word,head,buffer,cache in itertools.product(['unsigned int','int'],['char','void'],[False,True],[False,True]):
 bb=b.replace('    unsigned int n;', '    '+word+' n;').replace('    char far *h;', '    '+head+' far *h;')
 if head=='void':bb=bb.replace('h[n]', '((char far *)h)[n]')
 if buffer:
  bb=bb.replace('    int x1;', '    char far *buffer;\n    int x1;')
  pos=bb.index('        if (pic->type == 3)');tail=bb[pos:]
  # The handle is dead from the first allocation onward; only buffer uses are replaced.
  tail=tail.replace('h = malloc', 'buffer = malloc').replace('h[n]', 'buffer[n]').replace('((char far *)h)', 'buffer').replace('h);', 'buffer);').replace(', h,', ', buffer,').replace('*)h', '*)buffer')
  bb=bb[:pos]+tail
 if cache:bb=bb.replace('h = malloc((*g_9140)(x & ~1, y, x1, y1));', 'n = (*g_9140)(x & ~1, y, x1, y1);\n                h = malloc(n);').replace('buffer = malloc((*g_9140)(x & ~1, y, x1, y1));','n = (*g_9140)(x & ~1, y, x1, y1);\n                buffer = malloc(n);')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
