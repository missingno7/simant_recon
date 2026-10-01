from pathlib import Path
import sys,json,itertools,re
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
import modctx,autosearch,csrc
name='f_171C_0CF4';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.text,name);f=csrc.Source(base).function(name)
seed=(ROOT/'work/takeover/residue-controls/memcf4-result-lifetime-v6.c').read_text();sf=csrc.Source(seed).function(name);body=seed[sf.body.s:sf.body.e]
out=ROOT/'build/workers/blockers/memory-views';out.mkdir(parents=True,exist_ok=True);vs=[]
for flag,seg in itertools.product(['wide','int','alias','via_pointer'],['word','wide','wide_alias','wide_assign_alias']):
    bb=body
    if flag=='int':bb=bb.replace('unsigned long moved;', 'int moved;').replace('*(int near *)&moved', 'moved')
    elif flag=='alias':bb=bb.replace('moved = 0;', '*(int near *)&moved = 0;').replace('moved = 1;', '*(int near *)&moved = 1;')
    elif flag=='via_pointer':
        bb=bb.replace('unsigned long moved;', 'unsigned long moved;\n    int near *flag;').replace('moved = 0;', 'flag = (int near *)&moved;\n    *flag = 0;').replace('moved = 1;', '*flag = 1;').replace('*(int near *)&moved', '*flag')
    if seg!='word':
        bb=bb.replace('unsigned seg;', 'unsigned long seg;')
        if seg=='wide':bb=bb.replace('(seg = (unsigned)SEG(b))', '(unsigned)(seg = (unsigned)SEG(b))').replace('b->paras + seg', 'b->paras + (unsigned)seg')
        elif seg=='wide_alias':bb=bb.replace('(seg = (unsigned)SEG(b))', '(seg = (unsigned)SEG(b), *(unsigned near *)&seg)').replace('b->paras + seg', 'b->paras + *(unsigned near *)&seg')
        else:bb=bb.replace('(seg = (unsigned)SEG(b))', '(*(unsigned near *)&seg = (unsigned)SEG(b))').replace('b->paras + seg', 'b->paras + *(unsigned near *)&seg')
    vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:],flag,seg))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
    (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r})
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print([(r['name'],r['meta'],r.get('score'),r.get('all_exact')) for r in rows])
