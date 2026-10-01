from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='f_1E57_038E';text=autosearch.unscaffold((ROOT/'src/root/m1E57.c').read_text(),name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/clip-pointer-differences';out.mkdir(exist_ok=True);vs=[]
for repeat,wide,fold in itertools.product([True,False],['plain','long','ulong'],range(4)):
 bb=b
 if repeat:
  bb=bb.replace('    int count;\n','').replace('        count = end - tmp;\n','').replace('        n = count = end - tmp;', '        n = end - tmp;')
  bb=bb.replace('if (count >= 256)', 'if (end - tmp >= 256)').replace('", count);','", end - tmp);').replace('(count + 1)', '(end - tmp + 1)')
 if wide!='plain':
  bb=bb.replace('    int n;','    '+('long' if wide=='long' else 'unsigned long')+' n;')
  bb=bb.replace('if (n >= 256)', 'if ((int)n >= 256)').replace('"C099: Clip overflow %d", n);','"C099: Clip overflow %d", (int)n);')
 if fold&1:bb=bb.replace('        end = f_1D8E_02BD(&r, list, 0L, tmp);','        end = f_1D8E_02BD(&r, list, 0L, tmp);\n        if ((unsigned)((unsigned long)end >> 16) < 0) return;')
 if fold&2:bb=bb.replace('        end = f_1D8E_02BD(&r, list, tmp, 0L);','        end = f_1D8E_02BD(&r, list, tmp, 0L);\n        if ((unsigned)((unsigned long)end >> 16) < 0) return;')
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:8]])
