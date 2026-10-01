from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_171C_0CF4';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);seed=(ROOT/'build/workers/takeover/memcf4-result-lifetime/v6.c').read_text();sf=csrc.Source(seed).function(name);b=seed[sf.body.s:sf.body.e];out=ROOT/'build/workers/takeover/memcf4-segment-types';out.mkdir(exist_ok=True);vs=[];meta=[]
for seg,end,qual in itertools.product(['unsigned','_segment','unsigned short'],['unsigned','_segment'],['plain','volatile_segment','volatile_flag']):
 bb=b.replace('    unsigned seg;', '    '+('volatile ' if qual=='volatile_segment' else '')+seg+' seg;').replace('    unsigned end;', '    '+end+' end;')
 if qual=='volatile_flag':bb=bb.replace('    unsigned long moved;', '    volatile unsigned long moved;').replace('*(int near *)&moved','*(volatile int near *)&moved')
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([seg,end,qual])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
