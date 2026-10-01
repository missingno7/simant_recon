from pathlib import Path
import sys,json
from dataclasses import replace
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o10_35F5_0384';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);out=ROOT/'build/workers/takeover/s10-compiler-profiles';out.mkdir(exist_ok=True);rows=[]
cases=[(p,ctx.flags) for p in ['msc600ax','msc600a','msc600a-c2l','msc600']]
cases += [(p,['/AL','/Os','/Gs','/Zi']+extra) for p in ['msc510','qc250','qc251'] for extra in [[],['/O'],['/Ox']]]
for profile,flags in cases:
 ev=autosearch.Evaluator(replace(ctx,profile=profile,flags=flags),name,1,out/('cache-'+str(len(rows))));r=ev.one(text);ev.save();n=profile+'-v'+str(len(rows));(out/(n+'.c')).write_text(text);rows.append({'name':n,'profile':profile,'flags':flags,**r})
(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length'),r.get('log'),r.get('claims')) for r in rows])
