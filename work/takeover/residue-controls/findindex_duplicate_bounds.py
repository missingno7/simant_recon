from pathlib import Path
import sys,json,itertools
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));import csrc,autosearch,modctx
name='FindIndex';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name);f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];out=ROOT/'build/workers/takeover/findindex-duplicate-bounds';out.mkdir(exist_ok=True);vs=[]
start=b.index('        if (fd_50F6_3952->kind > kind');end=b.index('\n    }',start)
k='fd_50F6_3952->kind';ident='fd_50F6_3952->id';low='fd_50F6_3956'
blocks=[f'''        if ({k} > kind) {{
            top = mid - 1;
            continue;
        }}
        if ({k} == kind && {ident} >= id) {{
            top = mid - 1;
            continue;
        }}
        {low} = mid + 1;''',f'''        if ({k} > kind)
            top = mid - 1;
        else if ({k} == kind && {ident} >= id)
            top = mid - 1;
        else
            {low} = mid + 1;''',f'''        if ({k} > kind) {{
            top = mid - 1;
            continue;
        }}
        if ({k} == kind) {{
            if ({ident} >= id) {{
                top = mid - 1;
                continue;
            }}
        }}
        {low} = mid + 1;''']
for block,loop in itertools.product(blocks,['while','for','guarded_do']):
 bb=b[:start]+block+b[end:]
 if loop=='for':bb=bb.replace('while (fd_50F6_3956 <= top)', 'for (; fd_50F6_3956 <= top;)')
 elif loop=='guarded_do':
  bb=bb.replace('while (fd_50F6_3956 <= top) {','if (fd_50F6_3956 <= top) do {').replace('    }\n    fd_50F6_3952 =', '    } while (fd_50F6_3956 <= top);\n    fd_50F6_3952 =',1)
 vs.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,4,out/'cache');rows=[]
for i,(t,r) in enumerate(zip(vs,ev.many(vs))):
 (out/f'v{i}.c').write_text(t);rows.append({'name':f'v{i}',**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('variants',len(rows),'exact',sum(bool(r.get('all_exact')) for r in rows));print([(r['name'],r.get('score'),r.get('length')) for r in rows])
