"""Named canonical DOS data addresses, including private CodeView data.

Public addresses come from SOURCE.MAP. Private segment placements are proved
by public anchors or linked group-relative relocations in the same canonical
object. No original layout offsets or nearest-symbol extent guesses are used.
"""
from pathlib import Path
import hashlib,json, re, sys

def canonical_layout(root, report_path):
    sys.path.insert(0,str(root/'tools'))
    from omf import OmfReader
    report=json.loads(report_path.read_text())
    exe=root/report['link']['candidate_executable']['path']
    if hashlib.sha256(exe.read_bytes()).hexdigest()!=report['link']['candidate_executable']['sha256']:
        raise ValueError('canonical DOS executable report identity changed')
    raw=exe.read_bytes();image=raw[int.from_bytes(raw[8:10],'little')*16:]
    map_path=exe.with_name('SOURCE.MAP')
    addresses={}
    for line in map_path.read_text(encoding='latin1').splitlines():
        m=re.match(r'\s*([0-9A-F]{4}):([0-9A-F]{4})\s+Res\s+_(\w+)',line)
        if m: addresses.setdefault(m[3],int(m[1],16)*16+int(m[2],16))
    # DGROUP frame is an exact MAP paragraph, not a historical DOS segment.
    line=next(s for s in map_path.read_text(encoding='latin1').splitlines()
              if re.match(r'\s*[0-9A-F]{4}:[0-9A-F]{4}\s+Res\s+_g_5A9C\s',s))
    dgroup=int(line.split(':',1)[0],16)*16
    result={}; errors=[]
    modules={m['basename']:m for m in report['translation_units'] if 'object' in m}
    order=re.findall(r'\bU\d{3}\b',exe.with_name('SOURCE.LNK').read_text())
    objects={}
    for name,m in modules.items():
        raw_object=(root/m['object']['path']).read_bytes()
        if hashlib.sha256(raw_object).hexdigest()!=m['object']['sha256']:
            raise ValueError('canonical object identity changed: '+name)
        if hashlib.sha256((root/m['source']).read_bytes()).hexdigest()!=m['source_identity']['sha256']:
            raise ValueError('canonical source identity changed: '+m['key'])
        objects[name]=OmfReader(communals=True).read(raw_object)
    # Reconstruct only named DATA/CONST/BSS contribution positions, in the
    # actual SOURCE.LNK order and at recorded SEGDEF alignment. Validate ALL
    # available MAP publics (257 DATA anchors in this oracle), not a majority.
    group_positions={}
    for segment in ('_DATA','_BSS','CONST'):
        lines=[re.match(r'\s*([0-9A-F]+)H\s+[0-9A-F]+H\s+([0-9A-F]+)H\s+'+re.escape(segment)+r'\s',s)
               for s in map_path.read_text().splitlines()]
        hit=next(x for x in lines if x)
        start,total=int(hit[1],16),int(hit[2],16);position=0
        for name in order:
            obj=objects[name]
            definition=next((s for s in obj.segment_defs if s['name']==segment),None)
            if not definition or not definition['length']: continue
            align={'byte':1,'word':2,'paragraph':16}.get(definition['alignment'])
            if align is None: raise ValueError('unsupported canonical segment alignment')
            position=(position+align-1)//align*align
            group_positions[name,segment]=start+position
            for p in obj.publics:
                public=p['name'].lstrip('_@')
                if p['segment']==segment and public in addresses and addresses[public]!=start+position+p['offset']:
                    raise ValueError('MAP contradicts canonical contribution order: '+public)
            position+=definition['length']
        if position>total: raise ValueError('canonical contribution exceeds MAP segment')
    sys.path.insert(0,str(root/'portable'))
    from canonical_native_abi import asm_data
    for object_name in order:
        module=modules[object_name];obj=objects[object_name]
        segment_bases={}
        for p in obj.publics:
            name=p['name'].lstrip('_@')
            if name in addresses:
                base=addresses[name]-p['offset']
                segment_bases.setdefault(p['segment'],set()).add(base)
        # Recover a merged DATA/BSS contribution through final linker-owned
        # offsets. Require every usable relocation to give the same base.
        for f in obj.linker_fixups:
            # Initialized DATA pointer cells may be completed by the loader.
            # Only final CODE operand offsets are address-placement anchors.
            if not any(s['name']==f['segment'] and s['class'].upper()=='CODE' for s in obj.segment_defs): continue
            if (f['target_kind']!='segment' or f['frame_kind']!='group' or
                f['frame']!='DGROUP' or f['loc']!='offset16' or f['self_relative']): continue
            source=segment_bases.get(f['segment'],set())
            if len(source)!=1: continue
            where=next(iter(source))+f['offset']
            if where+2>len(image): continue
            linked=int.from_bytes(image[where:where+2],'little')
            addend=int.from_bytes(bytes.fromhex(f['encoded_addend']),'little')
            base=dgroup+((linked-f['displacement']-addend)&0xffff)
            segment_bases.setdefault(f['target'],set()).add(base)
        for segment in ('_DATA','_BSS','CONST'):
            if (object_name,segment) in group_positions:
                expected=group_positions[object_name,segment]
                observed=segment_bases.get(segment,set())
                if observed and observed!={expected}:
                    raise ValueError('linked relocations contradict contribution position: '+module['key']+' '+segment+' '+str((expected,observed)))
                segment_bases[segment]={expected}
        for p in obj.publics:
            name=p['name'].lstrip('_@')
            definition=next(s for s in obj.segment_defs if s['name']==p['segment'])
            if definition['class'].upper()=='CODE' or p['segment'].startswith('$$'): continue
            if name in addresses:
                result.setdefault(name,dict(owner=name,dos_address=addresses[name],module=module['key'],
                                             address_evidence='SOURCE.MAP public',segment=p['segment']))
        for c in obj.communals:
            name=c['name'].lstrip('_@')
            if name in addresses:
                result.setdefault(name,dict(owner=name,dos_address=addresses[name],bytes=c['length'],
                                             module=module['key'],address_evidence='SOURCE.MAP communal; canonical COMDEF extent'))
        # MSC 6 CodeView records: one-byte record length (excluding itself),
        # one-byte kind; kind 05 is a named data object (off,seg,type,pstring).
        debug=bytes(obj.segments.get('$$SYMBOLS',b''));pos=0
        while pos<len(debug):
            length=debug[pos]; end=pos+length+1
            if end>len(debug) or length==0: break
            if length>=8 and debug[pos+1]==5:
                n=debug[pos+8];name=debug[pos+9:pos+9+n].decode('latin1')
                refs=[f for f in obj.linker_fixups if f['segment']=='$$SYMBOLS' and f['offset']==pos+2]
                if len(refs)==1 and refs[0]['target_kind']=='segment':
                    f=refs[0];bases=segment_bases.get(f['target'],set())
                    if len(bases)==1:
                        offset=int.from_bytes(debug[pos+2:pos+4],'little')+f['displacement']
                        public_names={p['name'].lstrip('_@') for p in obj.publics}
                        key=name if name in public_names else module['key']+'::'+name
                        result.setdefault(key,dict(owner=name,dos_address=next(iter(bases))+offset,
                                         module=module['key'],segment=f['target'],
                                         address_evidence='canonical CodeView data record + verified SOURCE.LNK contribution position'))
                    else: errors.append(dict(module=module['key'],name=name,segment=f['target'],bases=sorted(bases)))
            pos=end
        if module['lang']=='asm':
            if module['key']=='root:1B73':
                # The two canonical TickCount CS-relative loads name one
                # DWORD through exact OMF fixups, not a guessed CODE extent.
                tick=next(p for p in obj.publics if p['name']=='_TickCount')
                refs=[f for f in obj.linker_fixups if f['segment']==tick['segment'] and tick['offset']<=f['offset']<tick['offset']+11]
                refs.sort(key=lambda f:f['offset'])
                if len(refs)!=2 or refs[1]['displacement']!=refs[0]['displacement']+2:
                    raise ValueError('canonical TickCount DWORD relocation pair changed')
                if any(f['target']!=tick['segment'] or f['frame']!=tick['segment'] or f['loc']!='offset16' for f in refs):
                    raise ValueError('TickCount relocation is not own-CS offset16')
                base=addresses['TickCount']-tick['offset']
                result['root:1B73::tick_count']=dict(owner='tick_count',dos_address=base+refs[0]['displacement'],
                    bytes=4,segment='CLOCK',native_expr='app.game_clock.tick_count',normalize='u32',
                    address_evidence='canonical TickCount CS-relative DWORD relocation pair + SOURCE.MAP function anchor')
                disable=next(p for p in obj.publics if p['name']=='_f_1B73_0511')
                ref=next(f for f in obj.linker_fixups if f['segment']==disable['segment'] and f['offset']==disable['offset']+3)
                if ref['target']!=tick['segment'] or ref['frame']!=tick['segment'] or ref['loc']!='offset16':
                    raise ValueError('canonical tick enable address changed')
                result['root:1B73::tick_count_on']=dict(owner='tick_count_on',dos_address=base+ref['displacement'],
                    bytes=1,segment='CLOCK',native_expr='app.game_clock.tick_count_enabled',normalize='u8',
                    address_evidence='canonical disable-TickCount CS-relative byte relocation + SOURCE.MAP anchor')
            facts=asm_data.data_facts(root/module['source'])
            for segment,items in facts['segments'].items():
                definition=next((s for s in obj.segment_defs if s['name']==segment),None)
                if not definition or definition['class'].upper()=='CODE': continue
                bases=segment_bases.get(segment,set())
                if len(bases)!=1: continue
                for label,data in items['labels'].items():
                    owner=label.lstrip('_@')
                    key=owner if label.startswith('_') else module['key']+'::'+owner
                    result.setdefault(key,dict(owner=owner,dos_address=next(iter(bases))+data['offset'],
                                               module=module['key'],segment=segment,
                                               address_evidence='canonical symbolic ASM label + verified SOURCE.LNK contribution position'))
    return result,errors
