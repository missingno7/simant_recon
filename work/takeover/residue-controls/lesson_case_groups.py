from pathlib import Path
import sys,json,re,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='LessonDone';ctx=modctx.resolve(func=name);base=(ROOT/'build/workers/takeover/lesson-base.c').read_text();f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
pieces=re.split(r'    case (\d+):\n',b);head=pieces[0];cases={int(pieces[i]):pieces[i+1] for i in range(1,len(pieces),2)}
tail='    }\n    return 0;\n}'
assert cases[56].endswith(tail);cases[56]=cases[56][:-len(tail)]
out=ROOT/'build/workers/takeover/lesson-case-groups';out.mkdir(exist_ok=True);vs=[]
groups=[[3,4],[5,20],[7,26],[10,32,42],[12,49],[19,22]]
for anchor,fallthrough,last in itertools.product(['first','last','observed'],[False,True],['plain','break','else','else_break']):
 cs=dict(cases);labels={i:[i] for i in cs}
 true=[i for i,v in cs.items() if v.strip()=='return 1;']
 for i in true[1:]:del cs[i];del labels[i]
 labels[1]=true
 for g in groups:
  a=g[-1] if anchor=='last' else g[0]
  if anchor=='observed':a={3:3,5:20,7:26,10:10,12:49,19:22}[g[0]]
  for i in g:
   if i!=a:del cs[i];del labels[i]
  labels[a]=[a]+[i for i in g if i!=a]
 g=[8,43,46,50]
 for i in g:del cs[i];del labels[i]
 if fallthrough:
  cs[30]=cs[30].replace('        if (fd_50F6_1074 != 0)', ''.join('    case '+str(i)+':\n' for i in g)+'        if (fd_50F6_1074 != 0)')
 else:
  a=g[-1] if anchor=='last' else g[0];cs[a]=cases[a];labels[a]=g
 if last in ['break','else_break']:cs[54]=cs[54].replace('        return 0;', '        break;')
 if last in ['else','else_break']:cs[54]=cs[54].replace('        if (MePlane == 2)', '        else if (MePlane == 2)')
 bb=head+''.join(''.join('    case '+str(j)+':\n' for j in labels[i])+cs[i] for i in sorted(cs))+tail
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],anchor,fallthrough,last))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
