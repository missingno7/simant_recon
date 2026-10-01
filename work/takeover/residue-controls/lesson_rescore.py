from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,modctx
name='LessonDone';ctx=modctx.resolve(func=name);out=ROOT/'build/workers/takeover/lesson-body-aware-controls';out.mkdir(exist_ok=True)
# Diagnostic disassembly must skip this switch's 56-word jump table. The strict
# module gate still compares every byte, fixup and relocation, including the table.
plain=autosearch.insn_distance
autosearch.insn_distance=lambda a,b:plain(a[:0x1e],b[:0x1e])+plain(a[0x8e:],b[0x8e:])
vs=[]
for series in ['lesson-case-groups','lesson-boolean-returns','lesson-shared-labels','lesson-negative-guards']:
 d=ROOT/'build/workers/takeover'/series
 for r in json.loads((d/'results.json').read_text()):
  if r.get('compile_ok'):vs.append((series+'/'+r['name'],(d/(r['name']+'.c')).read_text(),r.get('meta')))
vs.append(('base',(ROOT/'build/workers/takeover/lesson-base.c').read_text(),[]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,meta),r in zip(vs,ev.many([t for _,t,_ in vs])):rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));best=min((r for r in rows if r.get('score')),key=lambda r:r['score']);(out/'best.c').write_text(next(t for n,t,_ in vs if n==best['name']))
print('Best',best['name'],best['score'],best.get('length'));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')]);print('Top',[(r['name'],r['score']) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:15]])
