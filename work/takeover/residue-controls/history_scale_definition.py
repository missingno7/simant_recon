from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='drawHistGraph';ctx=modctx.resolve(func=name);text=(ROOT/'build/workers/takeover/history-state-lifetimes/v13.c').read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/history-scale-definition';out.mkdir(exist_ok=True);vs=[];meta=[]
for init,split,read in itertools.product([False,True],[False,True],['none','before_false','after_false','max_false','after_true','max_true']):
 bb=b
 if init:bb=bb.replace('for (mul = 1; max * mul < height; mul++)', 'for (; max * mul < height; mul++)')
 if split:
  bb=bb.replace('    int n;', '    int n;\n    int sample;')
  at=bb.index('    div = 1;');start=bb.index('    for (n = 0;');bb=bb[:start]+re.sub(r'\bn\b','sample',bb[start:at])+bb[at:]
 if read!='none':
  check='    if ((unsigned)fd_50F6_04F4 '+('>= 0) {}' if read.endswith('true') else '< 0) return;')+'\n'
  if read.startswith('before'):bb=bb.replace('    j = (fd_50F6_04F4',check+'    j = (fd_50F6_04F4',1)
  elif read.startswith('after'):bb=bb.replace('    max = 0;',check+'    max = 0;',1)
  else:bb=bb.replace('    max = 0;','    max = 0;\n'+check,1)
 vs.append(text[:f.body.s]+bb+text[f.body.e:]);meta.append([init,split,read])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}','meta':meta[i],**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('meta'),r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:10]])
