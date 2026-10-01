from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name,filename,series=sys.argv[1:4];ctx=modctx.resolve(func=name);base=Path(filename).read_text();f=csrc.Source(base).function(name)
out=ROOT/'build/workers/takeover'/series;out.mkdir(exist_ok=True);vs=[]
for opt,setting in [('c','off'),('e','off'),('g','off'),('eg','off'),('s','off'),('t','on'),('a','on'),('i','on'),('l','on')]:
 restore='on' if setting=='off' else 'off'
 tt=base[:f.head_s]+'#pragma optimize("'+opt+'", '+setting+')\n'+base[f.head_s:f.e]+'\n#pragma optimize("'+opt+'", '+restore+')\n'+base[f.e:]
 n='v'+str(len(vs));vs.append((n,tt,opt,setting))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
