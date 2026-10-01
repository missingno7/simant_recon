from pathlib import Path
import sys,json,re,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='LessonDone';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/lesson-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
pieces=re.split(r'    case (\d+):\n',b);head=pieces[0];cases={int(pieces[i]):pieces[i+1] for i in range(1,len(pieces),2)};tail='    }\n    return 0;\n}';assert cases[56].endswith(tail);cases[56]=cases[56][:-len(tail)]
out=ROOT/'build/workers/takeover/lesson-negative-guards';out.mkdir(exist_ok=True);vs=[]
groupkeys=[5,7,12,19,8,10]
for mask,how in itertools.product(range(64),['break','return']):
 cs=dict(cases)
 for ix,key in enumerate(groupkeys):
  if mask&(1<<ix):
   cs[key]=re.sub(r'        if \(([^{}\n]*(?:\n[^{}\n]*)?)\)\n            return 1;\n        break;\n',lambda m:'        if (!('+m.group(1)+'))\n            '+('break;' if how=='break' else 'return 0;')+'\n        return 1;\n',cs[key])
 bb=head+''.join('    case '+str(i)+':\n'+cs[i] for i in sorted(cs))+tail
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],mask,how))
for how in ['break','return']:
 bb=re.sub(r'        if \(([^{}\n]*(?:\n[^{}\n]*)?)\)\n            return 1;\n        break;\n',lambda m:'        if (!('+m.group(1)+'))\n            '+('break;' if how=='break' else 'return 0;')+'\n        return 1;\n',b)
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],'all',how))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
