from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='FindIndex';text=autosearch.unscaffold((ROOT/'src/root/m1986.c').read_text(),name)
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/findindex-shared-blocks';out.mkdir(exist_ok=True);vs=[]
start=b.index('        if (fd_50F6_3952->kind > kind');end=b.index('\n    }',start)
blocks=[
'''        if (fd_50F6_3952->kind > kind) goto lower_top;
        if (fd_50F6_3952->kind != kind) goto raise_bottom;
        if (fd_50F6_3952->id < id) goto raise_bottom;
lower_top:
        top = mid - 1;
        goto next;
raise_bottom:
        fd_50F6_3956 = mid + 1;
next: ;''',
'''        if (fd_50F6_3952->kind > kind) goto lower_top;
        if (fd_50F6_3952->kind == kind) {
            if (fd_50F6_3952->id < id) goto raise_bottom;
lower_top:
            top = mid - 1;
        } else {
raise_bottom:
            fd_50F6_3956 = mid + 1;
        }''',
'''        if (fd_50F6_3952->kind <= kind) {
            if (fd_50F6_3952->kind != kind || fd_50F6_3952->id < id)
                goto raise_bottom;
        }
        top = mid - 1;
        goto next;
raise_bottom:
        fd_50F6_3956 = mid + 1;
next: ;''',
'''        if (fd_50F6_3952->kind > kind) goto lower_top;
        if (fd_50F6_3952->kind != kind || fd_50F6_3952->id < id) {
            fd_50F6_3956 = mid + 1;
            continue;
        }
lower_top:
        top = mid - 1;''']
for block in blocks:
 for endform in ['goto','continue']:
  bb=b[:start]+block.replace('goto next;', 'continue;' if endform=='continue' else 'goto next;')+b[end:]
  vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,4,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
