from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import autosearch,csrc,modctx
name='win_PrintStyleTextInRect';ctx=modctx.resolve(func=name);base=autosearch.unscaffold(ctx.source.read_text(),name)
f=csrc.Source(base).function(name);b=base[f.body.s:f.body.e]
out=ROOT/'build/workers/takeover/printstyle-final-byte';out.mkdir(exist_ok=True);vs=[]
cond="text[end] == '\\n' || text[end] == '\\r'"
for mode in ['plain','char','unsigned_char','int','char_loop','unsigned_char_loop','fold_before','fold_after','fold_byte_before','fold_byte_after']:
 for declorder in ['plain','pos_first']:
  for linehtype in ['int','volatile int']:
   bb=b
   if declorder=='pos_first':bb=bb.replace('    int len;\n    int pos;', '    int pos;\n    int len;')
   if linehtype!='int':bb=bb.replace('    int lineH;', '    '+linehtype+' lineH;')
   if mode in ['char','unsigned_char','int','char_loop','unsigned_char_loop']:
    typ='unsigned char' if mode.startswith('unsigned_char') else 'char' if mode.startswith('char') else 'int'
    bb=bb.replace('    int end;', '    '+typ+' character;\n    int end;')
    if mode.endswith('_loop'):
     bb=bb.replace("while (text[end] == ' ')","while ((character = text[end]) == ' ')")
    else:bb=bb.replace('        if ('+cond+')','        character = text[end];\n        if ('+cond+')')
    bb=bb.replace('if ('+cond+')', "if (character == '\\n' || character == '\\r')")
   elif mode.startswith('fold'):
    fold='((unsigned char)text[end] >= 0)' if 'byte' in mode else '((unsigned)text[end] >= 0)'
    bb=bb.replace('if ('+cond+')', 'if ('+(fold+' && ('+cond+')' if mode.endswith('before') else '('+cond+') && '+fold)+')')
   vs.append(('v'+str(len(vs)),base[:f.body.s]+bb+base[f.body.e:]))
ev=autosearch.Evaluator(ctx,name,6,out/'cache');rows=[]
for (n,t),r in zip(vs,ev.many([t for _,t in vs])):
 (out/(n+'.c')).write_text(t);rows.append({'name':n,**r});print(n,r.get('score'),r.get('all_exact'),flush=True)
ev.save();(out/'results.json').write_text(json.dumps(rows,indent=1));print('EXACT GATES',[r['name'] for r in rows if r.get('all_exact')],flush=True)
