from pathlib import Path
import sys,json,itertools,re
sys.path.insert(0,'tools')
import csrc,modctx,autosearch,variants
root=Path('build/workers/context_next');root.mkdir(parents=True,exist_ok=True)
def run(name,text,candidates,folder):
    ctx=modctx.resolve(func=name);out=root/folder;out.mkdir(exist_ok=True)
    rows=variants.run(ctx,[(label,t,'') for label,t in [('base',text)]+candidates],extra_funcs=[name],claims_only=True,jobs=6,out_dir=out)
    (out/'results.json').write_text(json.dumps({'function':name,'profile':ctx.profile,'flags':ctx.flags,'variants':rows},indent=1))
    for row in rows:
        r=row['result'];v=r.get('claims',{}).get(name,{})
        losses=[c['name'] for c in ctx.claims if not r.get('claims',{}).get(c['name'],{}).get('exact')]
        print(folder,row['name'],v.get('exact'),v.get('reasons'),losses,flush=True)

name='o15_384C_0239';ctx=modctx.resolve(func=name);text=autosearch.unscaffold(ctx.text,name)
fn=csrc.Source(text).function(name);body=text[fn.body.s:fn.body.e];candidates=[]
for ty,form,site in itertools.product(['int','long','unsigned long','signed char','unsigned char'],['ternary','branches'],['outer','scoped']):
    decl=ty+' font;'
    calc='font = g_3DB2 == 0x140 ? 2 : 4;' if form=='ternary' else 'if (g_3DB2 == 0x140) font = 2; else font = 4;'
    code=calc+'\n    f_24AB_02AD((int)font);'
    bb=body.replace('f_24AB_02AD(g_3DB2 == 0x140 ? 2 : 4);',code if site=='outer' else '{\n    '+decl+'\n    '+code+'\n    }')
    if site=='outer':bb=bb.replace('    int result;','    int result;\n    '+decl)
    candidates.append((ty.replace(' ','-')+'-'+form+'-'+site,text[:fn.body.s]+bb+text[fn.body.e:]))
for pointer in ['char huge *','void far *','const unsigned char far *']:
    bb=body.replace('char far *text;',pointer+'text;').replace('text = f_171C_1B84(h);','text = ('+pointer+')f_171C_1B84(h);').replace('win_PrintTextInRect(0, text, &r);','win_PrintTextInRect(0, (char far *)text, &r);')
    candidates.append((pointer.replace(' ','-').replace('*','ptr'),text[:fn.body.s]+bb+text[fn.body.e:]))
# Result exists only during the event phase; text and rectangle only during setup.
for setup_scope,result_scope in itertools.product([False,True],repeat=2):
    bb=body
    if setup_scope:
        bb=bb.replace('    char far *text;\n','').replace('    struct Rect r;\n','')
        bb=bb.replace('    text = f_171C_1B84(h);','    {\n    char far *text;\n    struct Rect r;\n    text = f_171C_1B84(h);').replace('    f_24AB_02AD(0);\n    for (;;)', '    f_24AB_02AD(0);\n    }\n    for (;;)')
    if result_scope:
        bb=bb.replace('    int result;\n','').replace('    for (;;) {','    {\n    int result;\n    for (;;) {',1)
        bb=bb.replace('    return result;\n}', '    return result;\n    }\n}')
    candidates.append((f'phases-{setup_scope}-{result_scope}',text[:fn.body.s]+bb+text[fn.body.e:]))
run(name,text,candidates,'s15-lifetimes')

name='f_171C_0CF4';text=Path('work/takeover/siblings/memory-near.c').read_text()
fn=csrc.Source(text).function(name);body=text[fn.body.s:fn.body.e];candidates=[]
for alias_point,alias_kind in itertools.product(['found','before_size','after_copy'],['all','fields','copy']):
    bb=body.replace('    unsigned long moved;', '    unsigned long moved;\n    Block far *nb;')
    if alias_point=='found':bb=bb.replace('found:\n','found:\n        nb = b;\n')
    elif alias_point=='before_size':bb=bb.replace('        b->size = size;', '        nb = b;\n        b->size = size;')
    else:bb=bb.replace('        b->handle = n->handle;', '        nb = b;\n        b->handle = n->handle;')
    at=bb.index('        nb = b;')+len('        nb = b;')
    part=bb[at:]
    if alias_kind=='all':part=re.sub(r'\bb\b','nb',part[:part.index('        moved = 1;')])+part[part.index('        moved = 1;'):]
    elif alias_kind=='fields':part=part.replace('b->','nb->')
    elif alias_kind=='copy':
        if alias_point=='after_copy':continue
        part=part.replace('(long)b + 0x20000L','(long)nb + 0x20000L')
    bb=bb[:at]+part
    candidates.append((alias_point+'-'+alias_kind,text[:fn.body.s]+bb+text[fn.body.e:]))
run(name,text,candidates,'memory-alias')
