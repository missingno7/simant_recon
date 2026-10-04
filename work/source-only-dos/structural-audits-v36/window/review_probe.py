"""Bounded window ownership research. Writes only this worker directory.

Asset payloads are read for research and never written or used as C initializers.
Controls compile complete current effective modules and natural test-owned storage.
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, struct, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'tools'))
import compiler, exe
from omf import OmfReader

compiler.WORK = OUT / 'cc'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(p):
    p = p.resolve(); raw = p.read_bytes()
    return {'path': str(p).replace('\\','/'), 'size':len(raw), 'sha256':sha(raw)}

def lzss(src, expected):
    ring=bytearray([32]*4096); rp=0xfee; out=bytearray(); at=0
    while len(out)<expected:
        flags=src[at]; at+=1
        for bit in range(8):
            if len(out)>=expected: break
            if flags & (1<<bit):
                v=src[at]; at+=1; out.append(v); ring[rp]=v; rp=(rp+1)&4095
            else:
                lo,hi=src[at:at+2]; at+=2; pos=lo|((hi&240)<<4)
                for j in range((hi&15)+3):
                    if len(out)>=expected: break
                    v=ring[(pos+j)&4095]; out.append(v); ring[rp]=v; rp=(rp+1)&4095
    return bytes(out),at

def resource_census():
    result=[]
    for ixp in sorted((ROOT/'assets').glob('*.NDX')):
        dp=ixp.with_suffix('.DAT'); ix=ixp.read_bytes(); dat=dp.read_bytes()
        count=struct.unpack_from('<H',ix)[0]; selected=[]; windows=[]; layouts=[]
        for i in range(count):
            off,oid,kind,flags=struct.unpack_from('<IhBB',ix,20+i*8)
            if not (kind==0 and (oid in (0x80,0x81,0x83) or 0<=oid<128) or kind==9): continue
            packed_size=struct.unpack_from('<H',dat,off+20)[0]
            payload=dat[off+24:off+24+packed_size]
            if len(payload)!=packed_size: raise ValueError('truncated payload')
            consumed=None
            if flags&1:
                if flags&4: raise ValueError('delayed packed window research not supported')
                size=struct.unpack_from('<H',payload)[0]; payload,consumed=lzss(payload[2:],size)
            row={'id':oid,'kind':kind,'flags':flags,'record_offset':off,'packed_size':packed_size,
                 'expanded_size':len(payload),'expanded_sha256':sha(payload),'compressed_bytes_consumed':consumed}
            if kind==0 and oid==0x80:
                row['signed_count_words']=list(struct.unpack_from('<3h',payload))
            elif kind==0 and oid==0x81:
                row['six_byte_rows']=len(payload)//6; row['residual_bytes']=len(payload)%6
            elif kind==0 and oid==0x83:
                row['zero_positions']=[j for j,v in enumerate(payload) if v==0]
                row['nonzero_count']=sum(v!=0 for v in payload)
            elif kind==0:
                n=struct.unpack_from('<h',payload,12)[0]; pos=44+4*n; cs=[]; widths=[]; outliers=[]
                if n<0: raise ValueError('negative shipped count')
                for j in range(n):
                    if pos+40>len(payload): raise ValueError('short shipped object')
                    size=struct.unpack_from('<h',payload,pos+34)[0]
                    if size<40 or pos+size>len(payload): raise ValueError('bad shipped object stride')
                    colors=list(struct.unpack_from('<2b',payload,pos+38)); cs.extend(colors)
                    oflags=struct.unpack_from('<H',payload,pos+36)[0]
                    if any(c<0 or c>=16 for c in colors):
                        outliers.append({'object_number':j,'object_offset':pos,'type':payload[pos+33],
                          'record_stride':size,'group':payload[pos+32],'rect':list(struct.unpack_from('<4h',payload,pos)),
                          'object_flags':oflags,'initial_visible':bool(oflags&1),
                          'normal_color':colors[0],'alternate_color':colors[1],
                          'initial_selected_color':colors[1] if oflags&4 else colors[0]})
                    widths.append(size); pos+=size
                row['object_count']=n; row['object_color_signed_min']=min(cs) if cs else None
                row['object_color_signed_max']=max(cs) if cs else None; row['object_end']=pos
                row['trailing_bytes']=len(payload)-pos; row['color_fields_outside_shipped_palette']=outliers; windows.append(row)
            elif kind==9:
                row['rect_rows']=len(payload)//8; row['residual_bytes']=len(payload)%8
                row['loader_candidate']=oid==0; layouts.append(row)
            if kind==0 and oid in (0x80,0x81,0x83): selected.append(row)
        result.append({'index':pin(ixp),'database':pin(dp),'index_count':count,
          'headers_colors_purge':selected,'windows':windows,'layouts':layouts})
    return result

def compile_one(name,text,flags=None):
    sources=OUT/'sources'; sources.mkdir(exist_ok=True)
    p=sources/(name+'.c'); p.write_text(text,encoding='ascii')
    r=compiler.compile_c(text,'msc600ax',flags or ['/AL','/Os','/Gs'],basename='UNIT')
    (sources/(name+'.compiler.log')).write_text(r.log,encoding='utf-8')
    if not r.ok: raise RuntimeError(name+': '+r.log)
    (sources/(name+'.obj')).write_bytes(r.obj)
    o=OmfReader(communals=True).read(r.obj)
    return r.obj,o,{'source':pin(p),'object_sha256':sha(r.obj),'communals':o.communals,
      'segments':o.segment_lengths,'publics':o.publics,'external_scopes':o.external_scopes,
      'segment_sha256':{n:sha(bytes(v)) for n,v in o.segments.items()},'ordered_fixups':o.linker_fixups}

def nondebug(o):
    segs={r['name'] for r in o.segment_defs if r.get('class','').upper() not in {'DEBSYM','DEBTYP'}}
    return {'segments':{n:bytes(b) for n,b in o.segments.items() if n in segs},
      'lengths':{n:v for n,v in o.segment_lengths.items() if n in segs},
      'publics':[p for p in o.publics if p['segment'] in segs],
      'fixups':[f for f in o.linker_fixups if f['segment'] in segs],
      'communals':o.communals}

def full_module_controls():
    report=json.loads((ROOT/'build/source-only-dos-v35/build-report.json').read_text())
    row=next(r for r in report['translation_units'] if r['module']=='root:20E8')
    sp=Path(row['generated_source']['path']); sp=sp if sp.is_absolute() else ROOT/sp
    if sha(sp.read_bytes())!=row['generated_source']['sha256']: raise ValueError('effective source drift')
    src=sp.read_text(encoding='latin1'); flags=row['flags']; base=compile_one('m20E8_baseline',src,flags)
    controls=[]
    for length in (45,46):
        draft=src.replace('win_drawHooks[]','win_drawHooks[%d]'%length).replace('win_offsets[]','win_offsets[%d]'%length)
        _,o,fact=compile_one('m20E8_extern%d'%length,draft,flags)
        fact['nondebug_complete_object_equal_baseline']=nondebug(o)==nondebug(base[1]); controls.append(fact)
    # This counterexample changes zero-sized EXTDEF declarations into owning COMDEF declarations.
    # It is a research alternative, not an admitted game provider.
    candidates=[]
    for length in (45,46):
        text='struct Rect { int left,top,right,bottom; };\nvoid (far * far win_drawHooks[%d])(int phase);\nstruct Rect far win_offsets[%d];\n'%(length,length)
        raw,o,fact=compile_one('owner%d'%length,text)
        candidates.append((raw,o,fact))
    return {'effective_source':pin(sp),'whole_module_baseline':base[2],
       'extern_dimension_controls':controls,'test_owned_owner_controls':[x[2] for x in candidates]}, candidates

def original_initialization():
    x=exe.load(); region=x.read('S27',0x50f6*16,0x55b3*16-0x50f6*16)
    s27=x.sections[27]
    return {'exe':pin(ROOT/'assets/SIMANT.EXE'),'section27_load_linear':s27.load_linear,
      'far_common_interval':{'frame':0x50f6,'offset':0,'length':len(region)},
      'all_zero':not any(region),'region_sha256':sha(region),
      'near_bss_start':0x8b9e,'near_bss_end_exclusive':0x94f0,
      'far_reset_spans':{'hooks':{'offset':0x47de,'length':180},'offsets':{'offset':0x4892,'length':360}},
      'bytes_written_to_build':0,'claim':'original far common zero bytes are physically in preloaded section 27; near CRT BSS clear does not touch them'}

def registries():
    sy=json.loads((ROOT/'layout/symbols.json').read_text())
    return [{'name':n,**r} for n,r in sy['data'].items() if r.get('seg')==0x50f6 and 0x46a8<=r.get('off',0)<=0x4a06
          or r.get('seg')==0x55b3 and 0x8cf2<=r.get('off',0)<=0x94f0]

def main():
    result={'schema':'window-owner-review-v36','root_reviewed':False,'admitted':False,
      'inputs':[pin(ROOT/p) for p in ('layout/manifest.json','layout/symbols.json','layout/toolchain.json',
        'work/source-only-dos/static-completeness/index-v1.json')],
      'resource_census':resource_census(),'original_initial_state':original_initialization(),'registered_intervals':registries()}
    result['compiler'],_=full_module_controls()
    (OUT/'review-facts.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'resources':[{ 'database':Path(r['database']['path']).name,'headers':r['headers_colors_purge'],
      'window_count':len(r['windows']),'window_id_max':max([w['id'] for w in r['windows']],default=None),
      'color_max':max([w['object_color_signed_max'] for w in r['windows']],default=None),
      'color_outliers':[{ 'id':w['id'],'outliers':w['color_fields_outside_shipped_palette']} for w in r['windows'] if w['color_fields_outside_shipped_palette']],
      'layouts':[l for l in r['layouts'] if l['loader_candidate']]} for r in result['resource_census']],
      'module_controls':[{'source':r['source']['path'],'equal':r['nondebug_complete_object_equal_baseline']} for r in result['compiler']['extern_dimension_controls']],
      'owner_controls':[r['communals'] for r in result['compiler']['test_owned_owner_controls']],
      'original_far_zero':result['original_initial_state']['all_zero']},indent=2))

if __name__=='__main__': main()
