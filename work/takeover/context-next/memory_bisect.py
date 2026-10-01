"""Bisect natural memory-manager edits with every original module claim checked."""
from pathlib import Path
import sys,json,hashlib,itertools,concurrent.futures
sys.path.insert(0,'tools')
import modctx,csrc,autosearch,modules,variants
name='f_171C_0CF4';ctx=modctx.resolve(func=name)
base=autosearch.unscaffold(ctx.text,name)
fn=csrc.Source(base).function(name);body=base[fn.body.s:fn.body.e]
out=Path('build/workers/context_next/memory-bisect');out.mkdir(parents=True,exist_ok=True)

def segment(b):
    b=b.replace('    int moved;', '    unsigned seg;\n    int moved;')
    return b.replace('for (; SEG(b) < end; b = BLK(SEG(b) + b->paras))',
                     'for (; (seg = (unsigned)SEG(b)) < end; b = BLK(seg + b->paras))').replace('n = BLK(SEG(b) + b->paras);','n = BLK(seg + b->paras);')
def type_cache(b):
    b=b.replace('    int moved;', '    int t;\n    int moved;')
    b=b.replace('SEG(n) < end && !n->lock && (n->type == 1 || n->type == 3)',
                'SEG(n) < end && (t = n->type, !n->lock) && (t == 1 || t == 3)')
    b=b.replace('if (!n->lock && (n->type == 1 || n->type == 3) && b->paras >= n->paras)',
                'if ((t = n->type, !n->lock) && (t == 1 || t == 3) && b->paras >= n->paras)')
    return b.replace('f_171C_068C(b, paras, n->type);','f_171C_068C(b, paras, t);')
def remove_alias(b):
    b=b.replace('    Block far *nb;\n','').replace('        nb = b;\n','')
    import re
    return re.sub(r'\bnb\b','b',b)
def address_width(b):
    b=b.replace('n = BLK(SEG(n) + n->paras)', 'n = BLK((unsigned)SEG(n) + (unsigned long)n->paras)')
    b=b.replace('(char far *)nb + 0x20000L','(char far *)((long)nb + 0x20000L)')
    b=b.replace('(char far *)n + 0x20000L','(char far *)((long)n + 0x20000L)')
    return b
def wide_result(b):
    return b.replace('    int moved;', '    unsigned long moved;').replace('return moved;', 'return *(int near *)&moved;')
changes=[segment,type_cache,remove_alias,address_width,wide_result]
drafts=[]
for bits in itertools.product([False,True],repeat=len(changes)):
    b=body
    for bit,change in zip(bits,changes):
        if bit:b=change(b)
    label=''.join('1' if x else '0' for x in bits)
    drafts.append((label,base[:fn.body.s]+b+base[fn.body.e:],bits))
saved=Path('work/takeover/siblings/memory-near.c').read_text()
drafts.append(('near',saved,None))
claims=variants.check_set(ctx,[name],claims_only=True,text=base)
def check(item):
    label,text,bits=item;p=out/(label+'.c');p.write_text(text)
    col={};r=modules.verify_module(text,ctx.module_dict(),claims,collect=col)
    row={'name':label,'changes':bits,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
         'compile_ok':r.get('compile_ok'),'module_exact':r.get('exact'),
         'claims':r.get('claims'),'data':r.get('data'),'log':r.get('log','')[-500:]}
    if r.get('compile_ok'):
        obj=modctx.read_obj(col['object']);row['targets']={}
        for n in [name,'f_171C_2086']:
            bound,_=modctx.bind_function(ctx,obj,ctx.function(n))
            row['targets'][n]={'candidate_bytes':len(bound.candidate),'code_sha256':hashlib.sha256(bound.candidate).hexdigest(),
                              'byte_differences':sum(a!=b for a,b in zip(bound.original,bound.candidate))+abs(len(bound.original)-len(bound.candidate))}
        row['peer_losses']=[c['name'] for c in ctx.claims if not r['claims'][c['name']]['exact']]
    print(label,row.get('peer_losses'),row.get('targets'),flush=True)
    return row
with concurrent.futures.ThreadPoolExecutor(6) as pool:rows=list(pool.map(check,drafts))
(out/'results.json').write_text(json.dumps({'profile':ctx.profile,'flags':ctx.flags,
    'change_order':[f.__name__ for f in changes],'variants':rows},indent=1))
