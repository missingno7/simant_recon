from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_PrintStyleTextInRect';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
old="        while (text[end] == ' ')\n            end++;"
assert old in b
out=ROOT/'build/workers/takeover/printstyle-loop-cache';out.mkdir(exist_ok=True);vs=[]
for typ in ['char','unsigned char','int','unsigned']:
 for place in ['first','last']:
  for mode in ['cond_keep','cond_use','body_keep','body_use','fold_word','fold_long','fold_byte']:
   for order in ['plain','pos_first']:
    bb=b
    if order=='pos_first':bb=bb.replace('    int len;\n    int pos;', '    int pos;\n    int len;')
    if mode.startswith('fold'):
     cast={'fold_word':'unsigned','fold_long':'unsigned long','fold_byte':'unsigned char'}[mode]
     bb=bb.replace(old,f"        while (({cast})text[end] >= 0 && text[end] == ' ')\n            end++;")
    else:
     decl='    '+typ+' character;\n'
     bb=bb.replace('    char buf[120];',decl+'    char buf[120];') if place=='first' else bb.replace('    struct StyleRun far *styles;', '    struct StyleRun far *styles;\n'+decl.rstrip())
     if mode.startswith('cond'):bb=bb.replace(old,"        while ((character = text[end]) == ' ')\n            end++;")
     else:bb=bb.replace(old,"        character = text[end];\n        while (character == ' ') {\n            end++;\n            character = text[end];\n        }")
     if mode.endswith('use'):bb=bb.replace("if (text[end] == '\\n' || text[end] == '\\r')", "if (character == '\\n' || character == '\\r')")
    n='v'+str(len(vs));vs.append((n,base[:f.body.s]+bb+base[f.body.e:],typ,place,mode,order))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t,*meta),r in zip(vs,ev.many([t for _,t,*_ in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,'meta':meta,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
