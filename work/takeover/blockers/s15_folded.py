from pathlib import Path
import sys, json, itertools
ROOT=Path.cwd(); sys.path.insert(0,str(ROOT/'tools'))
import autosearch, modctx, csrc
name='o15_384C_0239'; ctx=modctx.resolve(func=name); base=autosearch.unscaffold(ctx.text,name)
f=csrc.Source(base).function(name); body=base[f.body.s:f.body.e]
out=ROOT/'build/workers/blockers/s15-folded'; out.mkdir(parents=True,exist_ok=True)
# Read only values already initialized at these statement boundaries. These
# folded reads are diagnostic STEERED controls, never recovered source evidence.
groups=[('    text = f_171C_1B84(h);', ['(unsigned long)h', '(unsigned)which']),
        ('    f_24AB_02AD(0);', ['(unsigned long)h','(unsigned long)text','(unsigned)which','(unsigned)r.left']),
        ('done:', ['(unsigned long)h','(unsigned long)text','(unsigned)which','(unsigned)result'])]
vs=[('v0',base)]
for marker, expressions in groups:
    for n in range(1,min(3,len(expressions))+1):
        for subset in itertools.combinations(expressions,n):
            for form in ('void','range'):
                use='\n'.join('    (void)('+e+');' if form=='void' else
                    '    if ('+e+' > '+('0xffffffffUL' if 'long' in e else '0xffffu')+') return 0;'
                    for e in subset)
                b=body.replace(marker,marker+'\n'+use,1)
                vs.append(('v'+str(len(vs)),base[:f.body.s]+b+base[f.body.e:]))
guards=[('if (g_5A97 & 1)', ['(unsigned long)h','(unsigned long)text','(unsigned)which']),
        ('if (f_1F58_0038())', ['(unsigned long)h','(unsigned long)text','(unsigned)which','(unsigned)r.left']),
        ('if (win_GetEvent(&ev))', ['(unsigned long)h','(unsigned long)text','(unsigned)which','(unsigned)r.left'])]
for marker, expressions in guards:
    condition=marker[4:-1]
    for n in range(1,min(3,len(expressions))+1):
        for subset in itertools.combinations(expressions,n):
            for positive in (True,False):
                op=' && ' if positive else ' || '
                reads=op.join('('+e+(' >= 0)' if positive else ' < 0)') for e in subset)
                b=body.replace(marker,'if (('+condition+')'+op+reads+')',1)
                vs.append(('v'+str(len(vs)),base[:f.body.s]+b+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache'); rows=[]
for start in range(0,len(vs),24):
    batch=vs[start:start+24]
    for (n,t),r in zip(batch,ev.many([t for _,t in batch])):
        (out/(n+'.c')).write_text(t); rows.append({'name':n,**r})
    ev.save(); (out/'results.json').write_text(json.dumps(rows,indent=1))
    print('done',len(rows),'all exact',[(r['name']) for r in rows if r.get('all_exact')],flush=True)
print('best',[(r['name'],r.get('score')) for r in sorted(rows,key=lambda r:r.get('score',[9]))[:5]],flush=True)
