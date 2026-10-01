from pathlib import Path
import sys,json,itertools,re
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='ch_LookUpId';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/cache-lookup-lifetimes';out.mkdir(exist_ok=True);vs=[]
for hook,count,loop in itertools.product(['plain','separate','condition','ulong'],['local','repeated','copy','staged'],['plain','second_pointer','while']):
 bb=b
 if hook=='separate':
  bb=bb.replace('char far *handle;', 'char far *handle;\n    char far *cached;').replace('handle = (*g_3B7E)(object, type);\n        if (handle)\n            return handle;', 'cached = (*g_3B7E)(object, type);\n        if (cached)\n            return cached;')
 if hook=='condition':bb=bb.replace('handle = (*g_3B7E)(object, type);\n        if (handle)', 'if ((handle = (*g_3B7E)(object, type)) != 0L)')
 if hook=='ulong':bb=bb.replace('char far *handle;', 'char far *handle;\n    unsigned long cached;').replace('handle = (*g_3B7E)(object, type);\n        if (handle)\n            return handle;', 'cached = (unsigned long)(*g_3B7E)(object, type);\n        if (cached)\n            return (char far *)cached;')
 if count=='repeated':
  bb=bb.replace('    int count;\n','').replace('    count = (*table)->count;\n','');bb=re.sub(r'\bcount\b', '(*table)->count', bb)
 if count=='copy':bb=bb.replace('    int count;', '    int count;\n    int divisor;').replace('    base = (*table)->e;', '    base = (*table)->e;\n    divisor = count;').replace('% count;', '% divisor;')
 if count=='staged':bb=bb.replace('    count = (*table)->count;\n    base = (*table)->e;', '    base = (*table)->e;\n    count = (*table)->count;')
 if loop=='second_pointer':
  bb=bb.replace('CacheEntry far *p;', 'CacheEntry far *p;\n    CacheEntry far *last;')
  start=bb.index('    for (i = ');end=bb.index('    goto missing;',start)
  bb=bb[:start]+re.sub(r'\bp\b','last',bb[start:end])+bb[end:]
 if loop=='while':
  count_expr='(*table)->count' if count=='repeated' else 'count'
  bb=bb.replace('for (i = '+count_expr+' - 1, p = &base[i]; i >= start; i--, p--) {', 'i = '+count_expr+' - 1; p = &base[i];\n    while (i >= start) {').replace('        probes++;\n    }\n    goto missing;', '        probes++;\n        i--; p--;\n    }\n    goto missing;')
 n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],hook,count,loop))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,meta,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
