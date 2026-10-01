"""Natural pointer-result expressions in the peer disturbed by the memory draft."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'tools')
import csrc,autosearch,modctx
out=Path('build/workers/siblings/peer-repair');out.mkdir(exist_ok=True)
text=Path('build/workers/siblings/f_171C_0CF4-filename.c').read_text()
name='f_171C_2086';ctx=modctx.resolve(func=name)
f=csrc.Source(text).function(name);body=text[f.body.s:f.body.e]
old='return (Handle)((long)(s_2F46 - h) + 0xF0EFFFFL);'
forms=[('cast-unsigned','return (Handle)((unsigned long)(s_2F46 - h) + 0xF0EFFFFUL);'),
       ('commute','return (Handle)(0xF0EFFFFL + (long)(s_2F46 - h));'),
       ('explicit-signed','return (Handle)((signed long)(s_2F46 - h) + 0xF0EFFFFL);')]
for ty in ['long','unsigned long','Handle']:
    for initialize in [False,True]:
        if ty=='Handle':
            expression='(Handle)((long)(s_2F46 - h) + 0xF0EFFFFL)'
            finish='return result;'
        else:
            expression='(long)(s_2F46 - h)'
            finish='return (Handle)(result + 0xF0EFFFFL);'
        if initialize:
            # Preserve evaluation after validation, Punt and the lock decrement.
            replacement='{\n        '+ty+' result = '+expression+';\n        '+finish+'\n    }'
            bb=body.replace(old,replacement)
        else:
            declaration=ty+' result;'
            replacement='result = '+expression+';\n    '+finish
            bb=body.replace('{\n','{\n    '+declaration+'\n',1).replace(old,replacement)
        forms.append((ty.replace(' ','-')+('-init' if initialize else '-assign'),bb))
texts=[]
for label,replacement in forms:
    bb=replacement if replacement.startswith('{') else body.replace(old,replacement)
    texts.append(text[:f.body.s]+bb+text[f.body.e:])
ev=autosearch.Evaluator(ctx,name,6,out/'cache')
canonical=ev.one(ctx.text);ev.set_base(canonical)
rows=[]
for (label,_),t,r in zip(forms,texts,ev.many(texts)):
    p=out/(label+'.c');p.write_text(t)
    rows.append({'draft':str(p),'source_sha256':hashlib.sha256(t.encode()).hexdigest(),
                 'peer_losses':ev.regressions(r),**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
print([(r['draft'],r.get('score'),r.get('all_exact'),r['peer_losses']) for r in rows],flush=True)
