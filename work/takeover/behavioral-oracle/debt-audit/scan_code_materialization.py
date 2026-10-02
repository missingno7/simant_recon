"""Inspect known original instruction streams for materialized gap addresses."""
from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
try:
 import capstone
except ImportError:
 sys.path.insert(0,'C:/tools/capstone-5.0.3'); import capstone
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
import exe,functions,symbols

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
 x=exe.load(); md=Cs(CS_ARCH_X86,CS_MODE_16); md.detail=True
 specs=[
  dict(id='root_0ec11',unit='root',seg=0x0e2e,off=0x931),
  dict(id='root_1ccbe',unit='root',seg=0x1c62,off=0x69e),
  dict(id='root_1e578',unit='root',seg=0x1e57,off=0x008),
  dict(id='root_1f420',unit='root',seg=0x1e57,off=0xeb0),
  dict(id='root_23e5e',unit='root',seg=0x23ae,off=0x37e),
  dict(id='root_285d7',unit='root',seg=0x284a,off=0x137),
  dict(id='s04_368d0',unit='S04',seg=0x35f5,off=0x980),
 ]
 relocs={u:set(x.unit_relocs(u)) for u in x.units()}
 rows=functions.table()['functions']
 per_gap={}
 for s in specs:
  hits=[]; same_cs=[]; sequences=[]; transfer_hits=[]; cs_moves=[]
  for f in rows:
   if f['unit']!=s['unit']: continue
   base,data=x.unit_bytes(f['unit']); idx=f['seg']*16+f['off']-base
   raw=data[idx:idx+f['size']]
   ins=list(md.disasm(raw,f['off']))
   for n,i in enumerate(ins):
    immed=[(o.imm&0xffff) for o in i.operands if o.type==capstone.x86.X86_OP_IMM]
    if s['off'] not in immed: continue
    imoff=i.address+i.encoding.imm_offset if i.encoding.imm_size else None
    localrel=[]
    if imoff is not None:
     localrel=[{'site':hex(r[1]),'distance':r[1]-imoff,'word':data[r[1]+i.address*0-base:r[1]+2] if False else None} for r in []]
    rel_near=[]
    for rseg,roff in relocs[s['unit']]:
     if rseg==f['seg'] and abs(roff-i.address)<=16:
      bidx=rseg*16+roff-base
      word=int.from_bytes(data[bidx:bidx+2],'little') if 0<=bidx<=len(data)-2 else None
      rel_near.append({'offset':f'{roff:04X}','delta_from_insn':roff-i.address,'stored_word':None if word is None else f'{word:04X}'})
    role=('control_target' if i.group(capstone.CS_GRP_JUMP) or i.group(capstone.CS_GRP_CALL) else
          'mov_immediate' if i.mnemonic.startswith('mov') else
          'push_immediate' if i.mnemonic=='push' else 'other_immediate')
    rec={'function':functions.name_of(f['unit'],f['seg'],f['off']),'function_seg':f['seg'],
         'insn_offset':f'{i.address:04X}','bytes':i.bytes.hex(' '),'mnemonic':i.mnemonic,'operands':i.op_str,
         'role':role,'immediate_field_offset':None if imoff is None else f'{imoff:04X}',
         'memory_destination':bool(i.mnemonic.startswith('mov') and i.operands and i.operands[0].type==capstone.x86.X86_OP_MEM),
         'relocations_within_16_bytes':rel_near}
    hits.append(rec)
    if f['seg']==s['seg']:
     same_cs.append(rec)
    if imoff is not None and any(rs==f['seg'] and ro==imoff for rs,ro in relocs[s['unit']]):
     rec['immediate_field_has_loader_relocation']=True
    else: rec['immediate_field_has_loader_relocation']=False
    if i.mnemonic in ('call','jmp','lcall') or i.group(capstone.CS_GRP_JUMP):
     vals=[o.imm&0xffff for o in i.operands if o.type==capstone.x86.X86_OP_IMM]
     if i.mnemonic=='lcall':
      matches=(f['unit']==s['unit'] and vals==[s['seg'],s['off']])
     else:
      matches=(f['unit']==s['unit'] and f['seg']==s['seg'] and s['off'] in vals)
     if matches: transfer_hits.append(rec)
    # Require concrete segment association, not merely a nearby relocation or CS use.
    if role in ('mov_immediate','push_immediate'):
     lo=max(0,n-4); hi=min(n+5,len(ins)); win=ins[lo:hi]
     cs_reads=[q for q in win if q.mnemonic=='mov' and len(q.operands)==2 and q.operands[0].type==capstone.x86.X86_OP_REG and q.operands[1].type==capstone.x86.X86_OP_REG and q.reg_name(q.operands[1].reg)=='cs']
     if cs_reads:
      cs_moves.append({'at':f'{i.address:04X}','function':rec['function'],'cs_move_offsets':[f'{q.address:04X}' for q in cs_reads],
                       'instructions':[{'offset':f'{q.address:04X}','bytes':q.bytes.hex(' '),'mnemonic':q.mnemonic,'operands':q.op_str} for q in win]})
     exact_push_pair=(f['seg']==s['seg'] and any(q.mnemonic=='push' and q.op_str.lower()=='cs' for q in win)
                      and any(q.mnemonic=='push' and s['off'] in [o.imm&0xffff for o in q.operands if o.type==capstone.x86.X86_OP_IMM] for q in win))
     seg_loads=[]
     for q in win:
      if q.address==i.address or not q.encoding.imm_size: continue
      qoff=q.address+q.encoding.imm_offset
      immvals=[o.imm&0xffff for o in q.operands if o.type==capstone.x86.X86_OP_IMM]
      if s['seg'] in immvals and any(rs==f['seg'] and ro==qoff for rs,ro in relocs[s['unit']]):
       seg_loads.append({'offset':f'{q.address:04X}','instruction':q.bytes.hex(' '),'role':'relocated target segment'})
     if exact_push_pair or seg_loads:
      seq=[{'offset':f'{q.address:04X}','bytes':q.bytes.hex(' '),'mnemonic':q.mnemonic,'operands':q.op_str} for q in win]
      sequences.append({'at':f'{i.address:04X}','function':rec['function'],'same_cs_push_pair':exact_push_pair,'segment_loads':seg_loads,'instructions':seq})
  per_gap[s['id']]={'target':s,'matching_offset_immediates':hits,'same_code_segment_immediates':same_cs,
                    'unit_and_segment_qualified_control_transfers':transfer_hits,
                    'candidate_materialization_sequences':sequences,'nearby_mov_cs_contexts':cs_moves,
                    'immediate_fields_with_loader_reloc':sum(bool(h['immediate_field_has_loader_relocation']) for h in hits),
                    'memory_destination_immediates':[h for h in hits if h['memory_destination']]}
 # Source literal/address-taken grep across accepted source tree. Exact numeric hit is only a lead.
 source_hits={}
 patterns={s['id']:re.compile(r'(?i)(?<!\w)(?:0x'+format(s['off'],'04x')+r'|'+format(s['off'],'04x')+r'h)(?!\w)') for s in specs}
 for p in (ROOT/'src').rglob('*'):
  if not p.is_file() or p.suffix.lower() not in ('.c','.h','.asm'): continue
  try: lines=p.read_text(encoding='utf-8',errors='replace').splitlines()
  except OSError: continue
  for sid,pat in patterns.items():
   found=[{'line':i+1,'text':line.strip()} for i,line in enumerate(lines) if pat.search(line)]
   if found: source_hits.setdefault(sid,[]).append({'path':p.relative_to(ROOT).as_posix(),'hits':found})
 out={'schema':'gap-address-materialization-scan-v1','oracle_sha256':x.sha256,
      'manifest_sha256':sha((ROOT/'layout/manifest.json').read_bytes()),
      'functions_sha256':sha((ROOT/'layout/functions.json').read_bytes()),
      'symbols_sha256':sha((ROOT/'layout/symbols.json').read_bytes()),
      'relevant_source_sha256':{p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for p in [ROOT/'src/root/m1C62.c',ROOT/'src/root/m1E57.c',ROOT/'src/root/m23AE.c',ROOT/'src/root/m284A.c',ROOT/'src/S04/m35F5.c']},
      'source_tree_scope':'all src/**/*.c,h,asm; exact standalone 0xNNNN/NNNNh literals and gap-shaped source symbol names, diagnostic only',
      'known_function_extent_count':len(rows),'gaps':per_gap,'source_literal_hits':source_hits,
      'scope':'Instruction immediates are interpreted in the instruction segment. Branch destinations only name a gap if unit and CS frame both match. A target-offset immediate is not a pointer unless paired with segment/CS evidence and a pointer-producing use. Relocations were correlated within +/-16 instruction bytes; this is a bounded pattern scan, not a whole-program proof of runtime indirect flow.'}
 out['source_symbol_hits']={s['id']:[] for s in specs}
 for s in specs:
  sympat=re.compile(r'(?i)(?<![\w])(?:f|o\d\d)_'+format(s['seg'],'04X')+'_'+format(s['off'],'04X')+r'(?![\w])')
  for p in (ROOT/'src').rglob('*'):
   if p.is_file() and p.suffix.lower() in ('.c','.h','.asm'):
    content=p.read_text(encoding='utf-8',errors='replace')
    for m in sympat.finditer(content):
     line=content.count('\n',0,m.start())+1
     out['source_symbol_hits'][s['id']].append({'path':p.relative_to(ROOT).as_posix(),'line':line,'symbol':m.group(0)})
 syms=symbols.load()['code']
 out['symbol_registry_matches']={s['id']:[name for name,rec in syms.items() if rec.get('unit')==s['unit'] and rec.get('seg')==s['seg'] and rec.get('off')==s['off']] for s in specs}
 (ROOT/'build/workers/behavior_data_audit/code-pointer-materialization.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print('wrote code-pointer-materialization.json')
 for sid,g in per_gap.items():
  print(sid,'all',len(g['matching_offset_immediates']),'same-CS',len(g['same_code_segment_immediates']),'exact-control',len(g['unit_and_segment_qualified_control_transfers']),'materialization-seq',len(g['candidate_materialization_sequences']))
if __name__=='__main__': main()
