from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='win_DrawBitMap';text=(ROOT/'build/workers/takeover/bitmap-original-order.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/bitmap-picture-views';out.mkdir(exist_ok=True);vs=[]
for view,xread,yread in itertools.product(['wide','void','char','union'],[False,True],[False,True]):
 bb=b
 if view=='wide':
  bb=bb.replace('struct Pic far *pic;', 'unsigned long pic;').replace('pic = *(struct Pic far * far *)h;', 'pic = *(unsigned long far *)h;');bb=bb.replace('pic->','((struct Pic far *)pic)->')
 elif view in ['void','char']:
  bb=bb.replace('struct Pic far *pic;',view+' far *pic;').replace('pic = *(struct Pic far * far *)h;', 'pic = *('+view+' far * far *)h;');bb=bb.replace('pic->','((struct Pic far *)pic)->')
 else:
  bb=bb.replace('struct Pic far *pic;', 'union { struct Pic far *pointer; unsigned long bits; } pic;').replace('pic = *(struct Pic far * far *)h;', 'pic.bits = *(unsigned long far *)h;');bb=bb.replace('pic->', 'pic.pointer->').replace('(char far *)pic', '(char far *)pic.bits')
 reads=''
 if xread:reads+='    if ((unsigned)x < 0) return 0;\n'
 if yread:reads+='    if ((unsigned)y < 0) return 0;\n'
 bb=bb.replace('    h = db_LoadObject',reads+'    h = db_LoadObject',1)
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
