from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,modctx
name='f_0250_129E';base=(ROOT/'build/workers/takeover/mapdraw-coordinate-copies/v9.c').read_text();out=ROOT/'build/workers/takeover/mapdraw-profile-controls';out.mkdir(exist_ok=True);rows=[]
for profile in ['msc600ax','msc600a','msc600a-c2l','msc600','msc600-c2l']:
 try:
  ctx=modctx.resolve(func=name,profile=profile);ev=autosearch.Evaluator(ctx,name,1,out/'cache');r=ev.one(base);ev.save()
 except Exception as e:r={'error':str(e)}
 rows.append({'name':profile,**r});print(profile,r.get('score'),r.get('all_exact'),r.get('error'),flush=True)
(out/'base.c').write_text(base);(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
