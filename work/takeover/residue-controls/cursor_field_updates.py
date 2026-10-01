from pathlib import Path
import sys,json,itertools
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='DrawMapCursor';text=(ROOT/'work/takeover/full-search/DrawMapCursor/best.c').read_text()
f=csrc.Source(text).function(name);b=text[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/cursor-field-updates';out.mkdir(exist_ok=True);vs=[]
for pointer in ['none','all','horizontal']:
 for left in ['expression','add_offset','add_origin','three_stages']:
  for right in ['expression','two_stages']:
   bb=b
   if left=='add_offset':bb=bb.replace('fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left + fd_50F6_38C0;', 'fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left;\n    fd_50F6_38C2.left += fd_50F6_38C0;')
   elif left=='add_origin':bb=bb.replace('fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left + fd_50F6_38C0;', 'fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_38C0;\n    fd_50F6_38C2.left += fd_50F6_10D2.left;')
   elif left=='three_stages':bb=bb.replace('fd_50F6_3856 * fd_50F6_0508[0] + fd_50F6_10D2.left + fd_50F6_38C0;', 'fd_50F6_3856 * fd_50F6_0508[0];\n    fd_50F6_38C2.left += fd_50F6_10D2.left;\n    fd_50F6_38C2.left += fd_50F6_38C0;')
   if right=='two_stages':bb=bb.replace('fd_50F6_38C2.right = fd_50F6_38C2.left + fd_50F6_3856 * fd_50F6_10E0;', 'fd_50F6_38C2.right = fd_50F6_3856 * fd_50F6_10E0;\n    fd_50F6_38C2.right += fd_50F6_38C2.left;')
   if pointer!='none':
    pos=0 if pointer=='all' else bb.index('    fd_50F6_38C2.left')
    bb=bb[:pos]+bb[pos:].replace('fd_50F6_38C2.', 'rect->').replace('&fd_50F6_38C2,','rect,')
    bb=bb.replace('{\n','{\n    struct Rect far *rect;\n',1)
    marker='    fd_50F6_38C2.top' if pointer=='horizontal' else '    rect->top'
    if pointer=='horizontal':marker='    rect->left'
    bb=bb.replace(marker, '    rect = &fd_50F6_38C2;\n'+marker,1)
   vs.append(('v'+str(len(vs)),text[:f.body.s]+bb+text[f.body.e:]))
ev=autosearch.Evaluator(modctx.resolve(func=name),name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1))
