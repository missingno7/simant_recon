from pathlib import Path
import sys,json,itertools
from dataclasses import replace
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='o10_35F5_0384';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);out=ROOT/'build/workers/takeover/s10-optimizer-controls';out.mkdir(exist_ok=True);rows=[]
for globaloff,localoff in itertools.product([False,True],[False,True]):
 flags=[x for x in ctx.flags if not(globaloff and x.lower()=='/og') and not(localoff and x.lower()=='/oe')]
 for filelevel in [False,True]:
  cctx=replace(ctx,flags=flags) if filelevel else ctx
  tt=text
  if not filelevel:
   opts=('g' if globaloff else '')+('e' if localoff else '')
   if opts:
    tt=text[:f.head_s]+'#pragma optimize("'+opts+'", off)\n'+text[f.head_s:]
    end=csrc.Source(tt).function(name).e;tt=tt[:end]+'\n#pragma optimize("'+opts+'", on)\n'+tt[end:]
  ev=autosearch.Evaluator(cctx,name,1,out/('cache-'+str(len(rows))));r=ev.one(tt);ev.save();n='v'+str(len(rows));(out/(n+'.c')).write_text(tt);rows.append({'name':n,'flags':cctx.flags,'meta':[globaloff,localoff,filelevel],**r})
(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length'),r.get('claims')) for r in rows])
