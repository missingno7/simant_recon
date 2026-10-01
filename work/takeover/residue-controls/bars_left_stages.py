from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import autosearch,modctx,csrc
name='DrawColonyBars';base=(ROOT/'src/S13/m384C.c').read_text(); old=(ROOT/'work/takeover/full-search/DrawColonyBars/best.c').read_text();of=csrc.Source(old).function(name);body=old[of.body.s:of.body.e];f=csrc.Source(base).function(name);base=autosearch.unscaffold(base,name);f=csrc.Source(base).function(name)
out=ROOT/'build/workers/takeover/bars-left-stages';out.mkdir(exist_ok=True)
line='                    l = (x + 6) * 28 + fd_50F6_10D2.left - y * 10;'
forms=[line, '                    l = (x + 6) * 28 + fd_50F6_10D2.left;\n                    l -= y * 10;', '                    tmp2 = (x + 6) * 28 + fd_50F6_10D2.left;\n                    l = tmp2 - y * 10;', '                    tmp2 = (x + 6) * 28;\n                    l = tmp2 + fd_50F6_10D2.left - y * 10;', '                    l = (x + 6) * 28;\n                    l += fd_50F6_10D2.left;\n                    l -= y * 10;', '                    t = (x + 6) * 28 + fd_50F6_10D2.left;\n                    l = t - y * 10;', '                    l = (x + 6) * 28 + (fd_50F6_10D2.left - y * 10);', '                    l = fd_50F6_10D2.left + (x + 6) * 28 - y * 10;']
fields=['                    r.left = l;\n','                    r.bottom = y * 10 + fd_50F6_10D2.top + 0x47;\n','                    r.right = l + 9;\n','                    r.top = r.bottom - h;\n'];vs=[]
for form in forms:
 for order in itertools.permutations(fields):
  if order.index(fields[1])>order.index(fields[3]):continue
  b=body.replace(line,form,1).replace(''.join(fields),''.join(order),1)
  vs.append(base[:f.body.s]+b+base[f.body.e:])
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows));print(json.dumps(sorted(rows,key=lambda r:r.get('score',[9]))[:3],indent=1)[:3000])
