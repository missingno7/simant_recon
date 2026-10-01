from pathlib import Path
import json, sys
sys.path.insert(0,'tools')
import modctx

root=Path('build/workers/fleet_root')
out=root/'lookup-controls'
ctx=modctx.resolve(func='ch_LookUpId')
files={'both_add':'007_chain1-first1-wrap1.c',
       'first_add_only':'006_chain1-first1-wrap0.c',
       'wrap_add_only':'005_chain1-first0-wrap1.c',
       'reversed_stores':'003_chain0-first1-wrap1.c'}
sources={k:(out/v).read_text(encoding='utf-8') for k,v in files.items()}
spec={'id':'PTR-1',
      'question':'In the preserved cache-table module, do explicit base-plus-index initializers in both probing phases reproduce the original register and frame allocation?',
      'notes':['Context-specific: &base[i] and base+i preserve C pointer semantics, but MSC 6.00AX does not emit the same code in this whole-module context.',
               'Both-add with i=start assignment is exact across eleven functions and a 1772-byte complete TU; a single-phase pointer spelling correction remains 359 vs 354 bytes.',
               'Reversing the chained hash-index stores keeps both-add length and allocation, but swaps two store displacement bytes. Chained assignment order is independently observable.',
               'All controls preserve ten accepted peers, DATA112 and BSS2. No folded dummy expression, unused padding or assembly is introduced. Sources and full binding evidence: work/takeover/fleet-lifetimes/.'],
      'variants':sources,'profiles':[{'profile':ctx.profile,'flags':ctx.flags}],
      'expect':{'both_add@0':'idiv si; mov word ptr [bp - 0x14], dx; mov word ptr [bp - 0xa], dx',
                'reversed_stores@0':'idiv si; mov word ptr [bp - 0xa], dx; mov word ptr [bp - 0x14], dx'},
      'expect_segments':{k+'@0':{'UNIT_TEXT':{'length':1772 if k in ('both_add','reversed_stores') else 1777},
                                '_DATA':{'length':112},'_BSS':{'length':2}} for k in sources}}
Path('evidence/codegen/PTR-1-cache-probe-pointer-add.json').write_text(json.dumps(spec,indent=1)+'\n',encoding='utf-8',newline='\n')
print('Pinned PTR-1 four whole-module controls')
