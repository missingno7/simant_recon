"""Review existing stock outputs without relinking or copying original bytes."""
import hashlib,json,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import exe
def sha(b): return hashlib.sha256(b).hexdigest()
result=json.loads((OUT/'runtime-facts.json').read_text())
result['raw_receipt_sha256']=sha((OUT/'runtime-facts.json').read_bytes())
result['review_correction']='Overlay MAP publics may have Res qualifier. Encoded MZ zero bytes do not imply loaded zero when relocations touch the span.'
for c in result['cases']:
 d=OUT/'runtime'/c['profile']/c['case']; mp=(d/'PROBE.MAP').read_text(encoding='latin1')
 locations={}
 for n in ('_win_drawHooks','_win_offsets'):
  pairs=re.findall(r'(?im)^\s*([0-9a-f]{4}):([0-9a-f]{4})\s+(?:Res\s+)?'+re.escape(n)+r'\b',mp)
  locations[n]=sorted(set((int(s,16),int(o,16)) for s,o in pairs))
 c['map_owner_locations']=locations
 c.pop('pre_startup_mz_far_bytes',None)
 if c['owner_in_overlay']: continue
 b=(d/'PROBE.EXE').read_bytes(); hdr=struct.unpack_from('<H',b,8)[0]*16
 nr,rt=struct.unpack_from('<H',b,6)[0],struct.unpack_from('<H',b,24)[0]
 reloc=[sg*16+of for of,sg in (struct.unpack_from('<HH',b,rt+4*j) for j in range(nr))]
 spans=[]
 for n,length in (('_win_drawHooks',180),('_win_offsets',360)):
  if len(locations[n])!=1: raise ValueError('missing/ambiguous public')
  seg,off=locations[n][0]; lo=seg*16+off; at=hdr+lo; span=b[at:at+length]
  rel=[x-lo for x in reloc if lo-1<=x<lo+length]
  spans.append({'name':n,'file_offset':at,'length':length,'present':len(span)==length,
   'unrelocated_all_zero':len(span)==length and not any(span),'relocated_word_offsets':rel,
   'zero_before_crt':len(span)==length and not any(span) and not rel,'sha256':sha(span)})
 c['unrelocated_mz_far_bytes_and_relocations']=spans
x=exe.load(); lo=0x50f6*16; hi=0x55b3*16; sites=sorted(x.reloc_sites('S27'))
result['original_far_bss_relocation_check']={'exe_sha256':x.sha256,'section':27,
 'linear_start':lo,'linear_end_exclusive':hi,'relocated_word_offsets':[p-lo for p in sites if lo-1<=p<hi],
 'section_relocation_count':len(sites),'claim':'Only a zero span with no loader relocation establishes zero initial bytes.'}
(OUT/'runtime-normalized.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'cases':[{'profile':c['profile'],'case':c['case'],'result':c['run_log'].strip(),
 'locations':c['map_owner_locations'],'disk':c.get('unrelocated_mz_far_bytes_and_relocations',[])} for c in result['cases']],
 'original_relocations':result['original_far_bss_relocation_check']},indent=2))
