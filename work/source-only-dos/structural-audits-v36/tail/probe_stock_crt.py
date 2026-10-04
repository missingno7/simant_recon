"""Source-built stock CRT controls; no original executable read/build material."""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'build/behavior/deps'))
import compiler
import source_only_dos as dos
from omf import OmfReader
import unicorn as uc
from unicorn import x86_const as xr
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

def sha(b): return hashlib.sha256(b).hexdigest()
def pin(p):
    b = p.read_bytes()
    return dict(path=str(p), size=len(b), sha256=sha(b))

def build():
    compiler.WORK = OUT / 'tool-scratch'
    sources = {
      'bss_two': 'unsigned char near probe[2];\nint main(void) { return probe[0] + probe[1]; }\n',
      'bss_shift': 'unsigned char near label[] = "ordinary boundary shift";\nunsigned char near probe[2];\nint main(void) { return label[0] + probe[0] + probe[1]; }\n',
      'file_seed': 'unsigned char near probe[2] = {0x31,0x57};\nint main(void) { return probe[0] + probe[1]; }\n',
    }
    tc = compiler.toolchain()
    runner = tc['runners']['dosbox-x']
    libs = json.loads((ROOT / 'layout/manifest.json').read_bytes())['runtime']['libraries']
    cases = []
    for name, source in sources.items():
        (OUT / (name + '.c')).write_text(source, encoding='ascii')
        result = compiler.compile_c(source, 'msc600ax', ['/AL', '/Os', '/Zi', '/Gs'], basename='MAIN', keep=True)
        assert result.ok, result.log
        obj = OmfReader(communals=True).read(result.obj)
        for profile in ('rtlink400', 'rtlink610'):
            tool = tc['linkers'][profile]
            directory = OUT / profile / name
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'MAIN.OBJ').write_bytes(result.obj)
            for lib in libs.values():
                assert sha(Path(lib['path']).read_bytes()) == lib['sha256']
                shutil.copyfile(lib['path'], directory / Path(lib['path']).name.upper())
            (directory / 'PROBE.LNK').write_bytes(b'OUTPUT PROBE\r\nMAP = PROBE S,N,A,L\r\nNODEFLIB\r\nLIBRARY LLIBCR, LIBH\r\nFILE MAIN\r\n')
            (directory / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
            (directory / 'RUN.BAT').write_bytes((f'@echo off\r\nD:\\{tool["executable"]} @PROBE.LNK < NUL > LINK.LOG\r\n').encode('ascii'))
            config = []
            for section, settings in runner['conf'].items():
                config += ['[' + section + ']'] + [f'{k}={v}' for k, v in settings.items()]
            config += ['[autoexec]', f'mount c "{directory}"', f'mount d "{compiler.pinned_tree(tool)}" -ro', 'c:', 'call RUN.BAT', 'exit']
            conf = directory / 'dosbox.conf'
            conf.write_text('\n'.join(config) + '\n', encoding='ascii')
            env = os.environ.copy()
            env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
            subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'], cwd=directory, env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True)
            assert (directory / 'PROBE.EXE').is_file(), (directory / 'LINK.LOG').read_text()
            cases.append(dict(name=name, linker=profile, directory=str(directory),
                              source_object_sha256=sha(result.obj), source_object_segments=obj.segment_lengths))
            print(profile, name, 'linked', flush=True)
    return cases

def publics(path):
    found = {}
    for line in path.read_text(encoding='latin1').splitlines():
        m = re.match(r'\s*([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\s+(\S+)', line)
        if m: found[m[3]] = (int(m[1],16), int(m[2],16))
    return found

def execute(case, poison, dos_version=5, injected_observer=False):
    directory = Path(case['directory'])
    p = publics(directory / 'PROBE.MAP')
    raw = (directory / 'PROBE.EXE').read_bytes()
    fields = struct.unpack_from('<13H', raw, 2)
    last, pages, nr, hp, mina, maxa, ss, sp, checksum, ip, cs, ro, ov = fields
    size = (pages-1)*512+last if last else pages*512
    image = bytearray(raw[hp*16:size])
    base, psp = 0x1000, 0xff0
    # Conventional relocation at load time, no mutation of the file/object.
    for i in range(nr):
        off, seg = struct.unpack_from('<HH',raw,ro+i*4)
        site = seg*16+off
        struct.pack_into('<H',image,site,(struct.unpack_from('<H',image,site)[0]+base)&65535)
    cpu = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_16)
    cpu.mem_map(0, 0x110000)
    cpu.mem_write(base*16, bytes(image))
    regs = {n:getattr(xr,'UC_X86_REG_'+n.upper()) for n in ('ax','bx','cx','dx','si','di','bp','sp','ip','cs','ds','es','ss','eflags')}
    def reg(n): return cpu.reg_read(regs[n])
    def put(n,v): cpu.reg_write(regs[n],v)
    dg, ed = p['_edata']; dg2, en = p['_end']; assert dg == dg2
    dgroup = base + dg
    a = dgroup*16+ed
    probe_seg, probe_off = p['_probe']; probe_a = (base+probe_seg)*16+probe_off
    if case['name']=='file_seed': assert probe_a+2<=a-1, 'boundary poison overlaps file-backed seed'
    cpu.mem_write(a-1,bytes([poison,poison,poison]))
    if case['name'].startswith('bss'): cpu.mem_write(probe_a,bytes([poison,poison]))
    cpu.mem_write(psp*16, b'\xcd\x20')
    cpu.mem_write(psp*16+2,struct.pack('<H',dgroup+0x1000))
    cpu.mem_write(psp*16+0x2c,struct.pack('<H',0x3000))
    cpu.mem_write(psp*16+0x80,b'\x00\r')
    cpu.mem_write(0x30000,b'A=B\0\0\x01\0PROBE.EXE\0')
    for n,v in dict(cs=base+cs,ip=ip,ss=base+ss,sp=sp,ds=psp,es=psp,eflags=0x202).items():put(n,v)
    main_a=(base+p['_main'][0])*16+p['_main'][1]
    crt_a=(base+p['__astart'][0])*16+p['__astart'][1]
    text = bytes(cpu.mem_read(crt_a,255))
    rd=OmfReader(communals=True)
    name, member=next((n,b) for n,b in rd.split_library(Path('C:/tools/msc-6.00/LIB/llibcr.lib').read_bytes()) if n.lower()=='dos\\crt0.asm')
    assert sha(member)=='2e9a254b9bd00ea59884089e78e951f0e40343e11d24976f32d9582f4ded259d'
    ob=rd.read(member,name); mask=set()
    for f in ob.linker_fixups:
        if f['segment']=='_TEXT': mask.update(range(f['offset'],f['offset']+f['width']))
    stock=bytes(ob.segments['_TEXT']); assert len(text)==len(stock)==255
    assert all(i in mask or text[i]==stock[i] for i in range(255)), 'whole stock CRT mismatch'
    assert struct.unpack_from('<H',text,0x84)[0]==ed
    assert struct.unpack_from('<H',text,0x87)[0]==en
    assert struct.unpack_from('<H',text,0x24)[0]==((en-2)&65535)
    events=[]; pre_reads=[]; written=set(); interrupted=False; terminated=False; observed=[]
    def code_hook(c,address,size,user):
        nonlocal terminated
        if dos_version<2 and address==crt_a+0x0c:
            assert bytes(c.mem_read(reg('ss')*16+reg('sp'),4))==struct.pack('<HH',0,psp)
            events.append('dos1-transfer-to-psp-zero');terminated=True;c.emu_stop()
        if address==main_a and reg('cs')==base+p['_main'][0]:
            events.append('main-entry');c.emu_stop()
        if address==crt_a+0x8f:events.append('clear-complete')
        if address==crt_a+0x91:events.append('qczrinit-after-clear')
        if address==crt_a+0x99:
            events.append('first-environment-call-after-clear')
            c.emu_stop()
        if address==crt_a+0x9e:events.append('setargv-after-clear')
        if address==crt_a+0xa5:events.append('cinit-after-clear')
    def read_hook(c,access,address,size,value,user):
        if address<a+2 and address+size>a and 'clear-complete' not in events:
            pre_reads.append(dict(address=address,size=size,cs=reg('cs'),ip=reg('ip')))
    def write_hook(c,access,address,size,value,user):
        if a<=address<a+2:written.add(address-a)
    def intr_hook(c,intno,user):
        nonlocal terminated
        ax=reg('ax');ah=ax>>8
        put('eflags',reg('eflags')&~1)
        if intno==0x20:terminated=True;events.append('dos1-terminal');c.emu_stop();return
        if intno!=0x21: raise RuntimeError(f'unsupported interrupt {intno:x}')
        if ah==0x30:
            if injected_observer: observed.append(bytes(c.mem_read(a,2)).hex())
            put('ax',dos_version)
        elif ah in (0x4a,0x49,0x25): pass
        elif ah==0x35:put('bx',0);put('es',0)
        elif ah==0x44:put('dx',0x80)
        elif ah==0x48:put('ax',0x4000)
        elif ah==0x40:put('ax',reg('cx'))
        elif ah==0x4c:terminated=True;events.append('dos-terminal');c.emu_stop()
        else:raise RuntimeError(f'unsupported DOS {ax:04x}')
    cpu.hook_add(uc.UC_HOOK_CODE,code_hook)
    cpu.hook_add(uc.UC_HOOK_MEM_READ,read_hook)
    cpu.hook_add(uc.UC_HOOK_MEM_WRITE,write_hook)
    cpu.hook_add(uc.UC_HOOK_INTR,intr_hook)
    cpu.emu_start((base+cs)*16+ip,0,count=100000)
    return dict(name=case['name'],linker=case['linker'],poison=poison,dos_version=dos_version,
        injected_external_observer=injected_observer,observer_output=observed,
        edata=ed,end=en,boundary_final=bytes(cpu.mem_read(a-1,3)).hex(),
        probe_final=bytes(cpu.mem_read(probe_a,2)).hex(),events=events,
        pre_clear_target_reads=pre_reads,clear_written_relative_offsets=sorted(written),terminated=terminated,
        genuine_whole_stock_crt_member=True,stop_registers={n:reg(n) for n in ('cs','ip','ds','es','si','di','cx','ss','sp')},
        executable_pin=pin(directory/'PROBE.EXE'))

def main():
    denied=dos.install_input_guard()
    cases=build() if '--vm-only' not in sys.argv else [dict(name=name,linker=profile,directory=str(OUT/profile/name))
        for name in ('bss_two','bss_shift','file_seed') for profile in ('rtlink400','rtlink610')]
    runs=[execute(case,poison) for case in cases for poison in (0xa5,0x5a)]
    for profile in ('rtlink400','rtlink610'):
        case=next(c for c in cases if c['name']=='bss_two' and c['linker']==profile)
        runs.append(execute(case,0xc7,dos_version=1))
        runs += [execute(case,poison,injected_observer=True) for poison in (0xa5,0x5a)]
    (OUT/'vm-diagnostic-runs.json').write_text(json.dumps(runs,indent=2)+'\n')
    for r in runs:
        if r['dos_version']==1:
            assert r['terminated'] and r['events']==['dos1-transfer-to-psp-zero']
            assert r['boundary_final']=='c7c7c7'
        else:
            assert r['events']==['clear-complete','qczrinit-after-clear','first-environment-call-after-clear'],r
            expected_triplet=(f'{r["poison"]:02x}'*3 if r['name']=='file_seed' else f'{r["poison"]:02x}0000')
            assert r['boundary_final']==expected_triplet,r
            assert r['clear_written_relative_offsets']==([] if r['name']=='file_seed' else [0,1]) and not r['pre_clear_target_reads'],r
            assert r['probe_final']==('3157' if r['name']=='file_seed' else '0000'),r
    assert not denied
    artifact_pins=[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.suffix.lower() in ('.c','.obj','.exe','.map','.lnk','.bat','.conf')
        and 'tool-scratch' not in p.parts]
    report=dict(schema='dos-tail-stock-crt-source-fixtures-v36',root_reviewed=False,admitted=False,
        original_executable_build_bytes=0,denied_original_reads=denied,cases=cases,runs=runs,
        artifact_pins=artifact_pins,controls_pass=True,scope='Test-owned source-built DOS programs, executed through the first post-clear environment call. Later startup ordering is static proof, not VM main execution. Boundary triplet is VM prior memory, not extra linked storage. External observer contrast is explicitly outside ordinary DOS ABI and prevents unconditional discharge.')
    (OUT/'stock-crt-controls.json').write_text(json.dumps(report,indent=2)+'\n')
    print('ALL CONTROLS PASS',len(runs),flush=True)

if __name__=='__main__':main()
