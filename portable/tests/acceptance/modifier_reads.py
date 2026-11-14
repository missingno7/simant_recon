"""Bind actual foreground BDA modifier-byte reads omitted by the first recorder.

The native converter maps BIOS_KEYBOARD_FLAGS_FARPTR reads to
dos_keyboard_modifiers(). These six exact C modules also contain other byte
reads: the emulator qualifies their *effective physical address*, never their
observed value. IRQ/internal reads remain excluded by the clock transaction.
"""
import json,sys,re,hashlib
from pathlib import Path
from capstone import Cs,CS_ARCH_X86,CS_MODE_16,CS_AC_READ,CS_AC_WRITE
from capstone.x86 import *
ROOT=Path(__file__).resolve().parents[3]

def bind(original,executable,base):
    sys.path.insert(0,str(ROOT/'tools'))
    import exe as oracle
    from omf import OmfReader
    modules=json.loads((ROOT/'layout/manifest.json').read_text())['modules']
    addresses={};compiled={}
    if not original:
        # Include actual overlay bodies, not the resident RTLink call vectors.
        for line in executable.with_name('SOURCE.MAP').read_text().splitlines():
            match=re.match(r'\s*([0-9A-F]{4}):([0-9A-F]{4})\s+(?:Res|Ovl)\s+[_@](\w+)(?:\s|$)',line)
            if match:addresses[match[3]]=16*int(match[1],16)+int(match[2],16)
        report=json.loads((ROOT/'build/current/dos/build-report.json').read_text())
        compiled={row['key']:row for row in report['translation_units']}
    decoder=Cs(CS_ARCH_X86,CS_MODE_16);decoder.detail=True
    registers={0:0,X86_REG_BX:1,X86_REG_BP:2,X86_REG_SI:3,X86_REG_DI:4,
               X86_REG_AX:5,X86_REG_CX:6,X86_REG_DX:7,X86_REG_SP:8}
    segments={X86_REG_ES:1,X86_REG_CS:2,X86_REG_SS:3,X86_REG_DS:4}
    rows=[]
    for key,module in modules.items():
        source=module.get('source')
        if not source or 'BIOS_KEYBOARD_FLAGS_FARPTR' not in (ROOT/source).read_text():continue
        claims=[c for c in module['claims'] if c['kind']=='C']
        if any(not c['provenance'].startswith('EXACT') for c in claims):raise ValueError('Modifier census requires exact module: '+key)
        if original:code_base=module['seg']*16
        else:
            row=compiled[key];object_path=ROOT/row['object']['path']
            if hashlib.sha256(object_path.read_bytes()).hexdigest()!=row['object']['sha256']:raise ValueError('Changed canonical object')
            obj=OmfReader(communals=True).read(object_path.read_bytes())
            text=next(segment['name'] for segment in obj.segment_defs if segment['class']=='CODE')
            object_code=bytes(obj.segments[text])
            publics={p['name'].lstrip('_@'):p['offset'] for p in obj.publics+obj.local_publics if p['segment']==text}
            starts={addresses[name]-offset for name,offset in publics.items() if name in addresses}
            if len(starts)!=1:raise ValueError('Canonical module frame is not independently anchored: '+key)
            code_base=starts.pop()
        for claim in claims:
            if original:
                start=code_base+claim['off']
                code=oracle.load().read(claim['unit'],claim['seg']*16+claim['off'],claim['size'])
            else:
                if claim['name'] not in publics:raise ValueError('Missing canonical code public: '+claim['name'])
                offset=publics[claim['name']];end=min([len(object_code)]+[p for p in publics.values() if p>offset])
                start=code_base+offset;code=object_code[offset:end]
            for ins in decoder.disasm(code,start):
                operands=[op for op in ins.operands if op.type==X86_OP_MEM and op.size==1 and op.access&CS_AC_READ and not op.access&CS_AC_WRITE]
                if not operands:continue
                if len(operands)!=1:continue # string operations are not scalar BDA queries
                memory=operands[0].mem
                # Linear extents can include embedded switch-table bytes. The
                # pinned 8086 C modules use 16-bit addressing for this far
                # constant; 32-bit decodings cannot be a modifier-byte site.
                if memory.base not in registers or memory.index not in registers:continue
                segment=memory.segment or (X86_REG_SS if memory.base==X86_REG_BP else X86_REG_DS)
                if segment not in segments:continue
                rows.append(dict(pc=base+ins.address,segment=segments[segment],base=registers[memory.base],index=registers[memory.index],
                    displacement=memory.disp&65535,signature=bytes(ins.bytes).hex(),function=claim['name'],module=key,
                    instruction=ins.mnemonic+' '+ins.op_str))
    if not rows:raise ValueError('No BDA modifier read candidates')
    return rows
