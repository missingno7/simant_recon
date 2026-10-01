from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/findindex-bound-updates';out.mkdir(exist_ok=True);vs=[]
for upper,lower,layout in itertools.product(['top = --mid;','mid--; top = mid;','top = mid; top--;'],['fd_50F6_3956 = ++mid;','mid++; fd_50F6_3956 = mid;','fd_50F6_3956 = mid; fd_50F6_3956++;'],['if','goto']):
 if layout=='if':
  bb=b.replace('top = mid - 1;',upper).replace('fd_50F6_3956 = mid + 1;',lower)
  bb=bb.replace('            '+upper,'            { '+upper+' }').replace('            '+lower,'            { '+lower+' }')
 else:
  start=b.index('        if (fd_50F6_3952->kind > kind');end=b.index('\n    }',start)
  block='''        if (fd_50F6_3952->kind > kind) goto lower_top;
        if (fd_50F6_3952->kind != kind) goto raise_bottom;
        if (fd_50F6_3952->id < id) goto raise_bottom;
lower_top:
        '''+upper+'''
        continue;
raise_bottom:
        '''+lower
  bb=b[:start]+block+b[end:]
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
