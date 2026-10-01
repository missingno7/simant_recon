from pathlib import Path
import sys,json,re
sys.path.insert(0,'tools')
import csrc,modctx,variants
name='CalcScore';ctx=modctx.resolve(func=name)
p=Path('build/workers/context_next/score-peer-repair/044_f_00F8_02F7-ticks.c')
text=p.read_text();f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
start=b.index('    {\n    int j;');end=b.index('    if (fd_50F6_0FC2')
part=b[start:end].rstrip();lines=part.splitlines()
# Indent the scoped statements; retain compiler line-entry boundaries.
part='\n'.join([lines[0]]+['    '+line if line.strip() else line for line in lines[1:-1]]+[lines[-1]])+'\n\n'
b=b[:start]+part+b[end:];text=text[:f.body.s]+b+text[f.body.e:]
# The exact spelling is not evidence: test a readable distinct name too.
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e];start=b.index('    {\n        int j;');end=b.index('    if (fd_50F6_0FC2')
renamed=text[:f.body.s]+b[:start]+re.sub(r'\bj\b','historyIndex',b[start:end])+b[end:]+text[f.body.e:]
out=Path('build/workers/context_next/score-reviewed');out.mkdir(exist_ok=True)
rows=variants.run(ctx,[('scoped-j',text,''),('history-index',renamed,'distinct natural name, same index lifetime')],extra_funcs=[name],claims_only=True,jobs=2,out_dir=out)
(out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
for x in rows:print(x['name'],x['result']['exact'],x['result']['claims'][name])
