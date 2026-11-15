"""Offline render-only comparison; no game sequencer or timing answers."""
import argparse,ctypes,hashlib,json,math,re,subprocess,wave
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
P=ctypes.c_void_p;U=ctypes.c_uint64;B=ctypes.c_uint8;H=ctypes.c_uint16
class Voice(ctypes.Structure):
    _fields_=[(n,H) for n in ('object','length','step','end','loop','position')]+[(n,B) for n in ('fraction','flags','volume')]+[('payload',ctypes.POINTER(B))]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--build',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--old-revision',required=True,help='Historical Git revision containing the retired ISA renderer')
    ap.add_argument('--reference',type=Path,default=ROOT/'build/reference/sound-on-identity-v1/quick-game/original/capture/observer.txt.content')
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    # Historical backend is a read-only comparison tool, never linked into the
    # game. No oracle content or historical game executable code is embedded.
    old_source=a.out/'old_isa_devices.cpp'
    for filename,destination in [('isa_devices.cpp',old_source),('isa_devices.h',a.out/'isa_devices.h')]:
        destination.write_bytes(subprocess.check_output(['git','show',a.old_revision+':portable/audio/'+filename],cwd=ROOT))
    common=[str(ROOT/'portable/audio/ymfm'/n) for n in ('ymfm_opl.cpp','ymfm_adpcm.cpp','ymfm_pcm.cpp')]
    for name,source in [('old',old_source),('new',ROOT/'portable/audio/native_renderer.cpp')]:
        subprocess.run(['C:/msys64/mingw64/bin/g++.exe','-O2','-std=c++17','-shared','-static','-Wl,--export-all-symbols','-I'+str(ROOT/'portable/audio'),str(source),*common,'-o',str(a.out/(name+'.dll'))],check=True)
    old=ctypes.CDLL(str((a.out/'old.dll').resolve()));new=ctypes.CDLL(str((a.out/'new.dll').resolve()))
    def sig(lib,n,args,ret=None):f=getattr(lib,n);f.argtypes=args;f.restype=ret;return f
    create_old=sig(old,'sim_isa_audio_create',[],P);destroy_old=sig(old,'sim_isa_audio_destroy',[P]);out=sig(old,'sim_isa_audio_out',[P,H,B,U]);render_old=sig(old,'sim_isa_audio_render',[P,ctypes.POINTER(ctypes.c_int16),U])
    create_new=sig(new,'sim_audio_create',[ctypes.POINTER(B)],P);destroy_new=sig(new,'sim_audio_destroy',[P]);opl=sig(new,'sim_audio_opl',[P,U,B,B]);start=sig(new,'sim_audio_voice_start',[P,U,ctypes.c_uint,ctypes.POINTER(Voice)]);stop=sig(new,'sim_audio_voice_stop',[P,U,ctypes.c_uint]);positions=sig(new,'sim_audio_positions',[P,U,ctypes.c_uint,ctypes.POINTER(H),ctypes.POINTER(B),ctypes.c_uint]);commit=sig(new,'sim_audio_commit',[P,U]);enable=sig(new,'sim_audio_enable',[P,U,ctypes.c_int]);render_new=sig(new,'sim_audio_render',[P,ctypes.POINTER(ctypes.c_int16),ctypes.c_size_t,U])
    table_source=(a.build/'canonical_audio_data.c').read_text();table_text=table_source.split('portable_canonical_volume_tables[2048] = {')[1].split('};')[0]
    table=bytes(int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',table_text));assert len(table)==2048
    tables=(B*2048).from_buffer_copy(table)
    reference=a.reference.resolve()
    rows=[s.split() for s in reference.read_text().splitlines()[1:]]
    first_sample=next(int(s[5]) for s in rows if s[0]=='S')
    cases=[('title',0,4_000_000_000,False),('effect',max(0,first_sample-100_000_000),4_000_000_000,True)]
    results=[]
    for name,begin,duration,only_samples in cases:
        left=create_old();right=create_new(tables);captured=[[],[]];idx=0;count=(begin+duration)*48000//10**9
        pos=(H*4)();vol=(B*4)();active=0;pair=None;keep=[];meta=[None]*2
        out(left,0x22c,0xd1,0);enable(right,0,1)
        for frame in range(count):
            ns=frame*10**9//48000
            while idx<len(rows) and int(rows[idx][5])<=ns:
                row=rows[idx];idx+=1;tag=row[0];t=int(row[5]);d=row[6:]
                if tag=='O' and not only_samples:
                    bank,reg,val=map(int,d);assert bank==0
                    out(left,0x388,reg,t);out(left,0x389,val,t);opl(right,t,reg,val)
                elif tag=='S':
                    ch,obj,rate,volume,end,loop,flags,size=map(int,d[:8]);payload=bytes.fromhex(d[8]);assert len(payload)==size
                    buf=(B*size).from_buffer_copy(payload);keep.append(buf);meta[ch]=(payload,volume)
                    v=Voice(obj,size,rate,end,loop,0,0,flags,volume,buf);start(right,t,ch,ctypes.byref(v));vol[ch]=volume
                elif tag=='X':
                    ch=int(d[0]);active&=~(1<<ch);stop(right,t,ch)
                elif tag=='P':
                    ch,obj,p,value=map(int,d);pos[ch]=p
                    if obj>=0:
                        active|=1<<ch;payload,volume=meta[ch];assert table[volume*256+payload[p]]==value
                    else:active&=~(1<<ch)
                    if ch==0:pair=value
                    else:
                        assert pair is not None
                        out(left,0x22c,0x10,t);out(left,0x22c,(pair+value)//2,t)
                        positions(right,t,2,pos,vol,active);commit(right,t);pair=None
            l=(ctypes.c_int16*2)();r=(ctypes.c_int16*2)();render_old(left,l,ns);render_new(right,r,1,frame)
            if ns>=begin:
                captured[0].append(tuple(l));captured[1].append(tuple(r))
        arrays=[np.asarray(x,dtype=np.int16) for x in captured]
        for label,pcm in zip(('old','new'),arrays):
            with wave.open(str(a.out/(name+'-'+label+'.wav')),'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);w.writeframes(pcm.astype('<i2').tobytes())
        x,y=[p[:,0].astype(np.float64) for p in arrays];spec=[np.abs(np.fft.rfft(z)) for z in (x,y)]
        results.append(dict(case=name,begin_ns=begin,duration_ns=duration,frames=len(x),equal=bool(np.array_equal(*arrays)),max_absolute_difference=int(np.max(np.abs(x-y))),rms_old=float(np.sqrt(np.mean(x*x))),rms_new=float(np.sqrt(np.mean(y*y))),rms_error=float(np.sqrt(np.mean((x-y)**2))),spectrum_relative_l2=float(np.linalg.norm(spec[1]-spec[0])/max(1,np.linalg.norm(spec[0]))),peak_hz=[float(np.argmax(s)*48000/len(x)) for s in spec]))
        destroy_old(left);destroy_new(right)
    receipt=dict(reference=str(reference),reference_sha256=sha(reference),tables_sha256=hashlib.sha256(table).hexdigest(),old_revision=a.old_revision,old_source_sha256=sha(old_source),new_source_sha256=sha(ROOT/'portable/audio/native_renderer.cpp'),cases=results,no_ear_test=True)
    (a.out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
    return int(any(not case['equal'] for case in results))
if __name__=='__main__':raise SystemExit(main())
