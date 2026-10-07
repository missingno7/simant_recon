"""Bounded S00 instruction controls; CPU hardware effects are explicit oracles."""
import ctypes
import struct
from types import SimpleNamespace


def copy_rect_checks(native, b, functions, rng):
    class Rect(ctypes.Structure):
        _fields_=[(n,ctypes.c_int16) for n in ('left','top','right','bottom')]
    call=native.sim_s00_raster_copy_rect
    call.argtypes=[ctypes.POINTER(Rect),ctypes.c_void_p,ctypes.c_size_t,
                   ctypes.POINTER(Rect),ctypes.c_void_p,ctypes.c_size_t]
    machine=b.Machine(SimpleNamespace(function=functions.get('o00_35A6_02FD'),vectors={}))
    cases=[]
    for r,c in [((0,0,48,20),(8,2,40,18)), ((-16,-5,32,15),(-7,-2,24,12)),
                ((0,0,47,20),(1,2,39,15)), ((0,0,16,10),(9,1,31,8)),
                ((0,0,16,10),(16,0,32,10)), ((0,0,64,12),(7,0,71,12))]:
        source=rng.randbytes(65536); buffer=rng.randbytes(65536)
        src=(ctypes.c_uint8*65536).from_buffer_copy(source)
        dst=(ctypes.c_uint8*65536).from_buffer_copy(buffer)
        status=call(ctypes.byref(Rect(*r)),src,65536,ctypes.byref(Rect(*c)),dst,65536)
        original=machine.run(b.Case('copy-rect',args=[0,0x5000,0,0x6000,0,0x5100,0,0x7000],
            writes=[(0x50000,struct.pack('<4h',*r)),(0x60000,source),
                    (0x51000,struct.pack('<4h',*c)),(0x70000,buffer)],
            observe=[b.Range('buffer',0x70000,65536)],return_kind='void'))
        equal=status==0 and bytes(dst)==bytes.fromhex(original['ranges']['buffer'])
        case={'entry':'o00_35A6_02FD','source_rect':r,'clip_rect':c,'matched':equal}
        cases.append(case)
        if not equal: raise AssertionError(case)
    return cases


def tile_checks(native, b, functions, rng):
    # Independent, minimal mode-1 VGA CPU aperture hook. Other write modes
    # are exercised by the C hardware controls, not this instruction model.
    class VgaMachine(b.Machine):
        def __init__(self, entry='o00_31AD_0647'):
            self.planes=[]; self.latches=[0]*4
            self.gc=0; self.seq=0; self.read_map=0; self.mode=0; self.map_mask=15
            super().__init__(SimpleNamespace(function=functions.get(entry),vectors={}))
            self.cpu.hook_add(b.uc.UC_HOOK_MEM_READ,self.read_aperture,None,0xa0000,0xaffff)
        def _on_out(self,cpu,port,size,value,user):
            super()._on_out(cpu,port,size,value,user)
            if port==0x3ce:self.gc=value
            elif port==0x3c4:self.seq=value
            elif port==0x3cf:
                if self.gc==4:self.read_map=value&3
                elif self.gc==5:self.mode=value
            elif port==0x3c5 and self.seq==2:self.map_mask=value&15
        def read_aperture(self,cpu,access,address,size,value,user):
            values=[]
            for at in range(address,address+size):
                off=(at-0xa0000)&65535
                self.latches=[p[off] for p in self.planes]
                values.append(self.latches[self.read_map])
            cpu.mem_write(address,bytes(values))
        def _on_write(self,cpu,access,address,size,value,user):
            super()._on_write(cpu,access,address,size,value,user)
            if 0xa0000<=address<0xb0000:
                assert self.mode&3 in (0,1)
                for byte in range(size):
                    for p in range(4):
                        if self.map_mask&(1<<p):
                            data=self.latches[p] if self.mode&3==1 else (value>>(byte*8))&255
                            self.planes[p][(address-0xa0000+byte)&65535]=data

    native.tile_test_reset.argtypes=[ctypes.c_int,ctypes.c_void_p]
    native.tile_test_call.argtypes=[ctypes.c_int16,ctypes.c_int16,ctypes.c_uint16]
    native.tile_test_planes.restype=ctypes.c_void_p
    native.tile_test_fallback.restype=ctypes.c_void_p
    native.tile_test_pattern.restype=ctypes.c_void_p
    native.tile_test_state.argtypes=[ctypes.c_uint]
    cases=[]
    for clip,x,y,offset in [(1,0,0,0xa000),(1,624,464,0xc020),(1,632,472,42),
                            (1,640,393,0xc000),(1,-16,100,0xc000),(1,0,480,0xc000),
                            (1,1,20,0xa010),(1,639,479,0xffe0),(0,8,450,0xffe0)]:
        planes=rng.randbytes(4*65536)
        native.tile_test_reset(clip,(ctypes.c_uint8*len(planes)).from_buffer_copy(planes))
        status=native.tile_test_call(x,y,offset)
        machine=VgaMachine()
        machine.planes=[bytearray(planes[p*65536:(p+1)*65536]) for p in range(4)]
        fallbacks=[]
        def bitmap(m,args):
            fallbacks.append(m.read(args[3]*16+args[2],128))
            assert args[0]==x&65535 and args[1]==y&65535 and args[4:]==[16,16]
            return 0
        writes=[(b.symbol_address('g_3DB0'),b.words(0xa000)),
                (b.symbol_address('g_3DB6'),b.words(80)),
                (b.symbol_address('g_3DD4'),b.words(0x8800)),
                (b.symbol_address('g_4333'),b'\x01'),
                (b.symbol_address('g_5AAC'),b.words(0,0x7300 if clip else 0)),
                (0x73000,struct.pack('<8h',0,0,640,480,0,-32768,0,0)),
                (b.symbol_address('g_3DFC'),b.words(*(row*80 for row in range(480))))]
        result=machine.run(b.Case('tile',args=[x,y,offset],writes=writes,
            callbacks={'o00_31AD_0CF9':b.Callback(6,handler=bitmap)},
            observe=[b.Range('busy',b.symbol_address('g_3DD4'),2)],return_kind='void',
            observe_at_calls=False))
        expected=b''.join(machine.planes)
        state=[0x8800,machine.map_mask,machine.read_map,machine.mode,machine.gc,machine.seq]
        equal=(status==0 and ctypes.string_at(native.tile_test_planes(),4*65536)==expected
            and native.tile_test_calls()==len(fallbacks)
            and (not fallbacks or ctypes.string_at(native.tile_test_fallback(),128)==fallbacks[0])
            and [native.tile_test_state(i) for i in range(6)]==state
            and result['ranges']['busy']=='0088')
        case={'entry':'o00_31AD_0647','clip':clip,'x':x,'y':y,'offset':offset,
              'fallback_calls':len(fallbacks),'matched':equal}
        cases.append(case)
        if not equal:raise AssertionError(case)
    native.tile_test_capture.argtypes=[ctypes.c_int16]*4+[ctypes.c_void_p]
    for rect in [(0,0,32,4),(-16,20,24,24),(632,470,656,474),
                 (0,480,32,484),(0,818,32,822),(0,-2,16,2)]:
        planes=rng.randbytes(4*65536); buffer=rng.randbytes(65536)
        native.tile_test_reset(0,(ctypes.c_uint8*len(planes)).from_buffer_copy(planes))
        dst=(ctypes.c_uint8*65536).from_buffer_copy(buffer)
        status=native.tile_test_capture(*rect,dst)
        machine=VgaMachine('o00_31AD_0550')
        machine.planes=[bytearray(planes[p*65536:(p+1)*65536]) for p in range(4)]
        result=machine.run(b.Case('capture',args=[*rect,0,0x7000],
            writes=[(b.symbol_address('g_3DB0'),b.words(0xa000)),
                    (b.symbol_address('g_3DB6'),b.words(80)),
                    (b.symbol_address('g_4333'),b'\x01'),
                    (b.symbol_address('g_3DD4'),b.words(0x8800)),(0x70000,buffer)],
            observe=[b.Range('buffer',0x70000,65536),b.Range('busy',b.symbol_address('g_3DD4'),2)],
            return_kind='void',observe_at_calls=False))
        state=[0x8800,machine.map_mask,machine.read_map,machine.mode,machine.gc,machine.seq]
        equal=(status==0 and bytes(dst)==bytes.fromhex(result['ranges']['buffer'])
               and [native.tile_test_state(i) for i in range(6)]==state
               and result['ranges']['busy']=='0088')
        case={'entry':'o00_31AD_0550','rect':rect,'matched':equal}
        cases.append(case)
        if not equal:raise AssertionError(case)
    for entry,offset,plane,count in [
        ('o00_31AD_186A',1,0,2),('o00_31AD_186A',0,2,1),
        ('o00_31AD_186A',3,3,5),('o00_31AD_186A',0xfffa,1,16),
        ('o00_31AD_186A',42,9,12),('o00_31AD_18BA',42,0,3),
        ('o00_31AD_18BA',0xffe0,0,2)]:
        planes=rng.randbytes(4*65536); source=rng.randbytes(65536)
        native.tile_test_reset(0,(ctypes.c_uint8*len(planes)).from_buffer_copy(planes))
        src=(ctypes.c_uint8*65536).from_buffer_copy(source)
        call=getattr(native,entry)
        call.argtypes=([ctypes.c_void_p,ctypes.c_uint16,ctypes.c_int16,ctypes.c_uint16]
                       if entry.endswith('186A') else [ctypes.c_void_p,ctypes.c_uint16,ctypes.c_int16])
        call(*([src,offset,plane,count] if entry.endswith('186A') else [src,offset,count]))
        machine=VgaMachine(entry)
        machine.planes=[bytearray(planes[p*65536:(p+1)*65536]) for p in range(4)]
        args=[0,0x7000,offset,plane,count] if entry.endswith('186A') else [0,0x7000,offset,count]
        result=machine.run(b.Case('upload',args=args,
            writes=[(b.symbol_address('g_3DB0'),b.words(0xa000)),
                    (b.symbol_address('g_3DD4'),b.words(0x8800)),(0x70000,source)],
            observe=[b.Range('busy',b.symbol_address('g_3DD4'),2)],return_kind='void'))
        state=[0x8800,machine.map_mask,machine.read_map,machine.mode,machine.gc,machine.seq]
        equal=(ctypes.string_at(native.tile_test_planes(),4*65536)==b''.join(machine.planes)
               and [native.tile_test_state(i) for i in range(6)]==state
               and result['ranges']['busy']=='0088')
        case={'entry':entry,'offset':offset,'plane':plane,'count':count,'matched':equal}
        cases.append(case)
        if not equal:raise AssertionError(case)
    for plane,offset in [(0,0xa000),(3,42),(9,0xffe0)]:
        planes=rng.randbytes(4*65536)
        native.tile_test_reset(0,(ctypes.c_uint8*len(planes)).from_buffer_copy(planes))
        native.o00_31AD_1A8F.argtypes=[ctypes.c_int16,ctypes.c_int16]
        native.o00_31AD_1A8F(plane,offset)
        machine=VgaMachine('o00_31AD_1A8F')
        machine.planes=[bytearray(planes[p*65536:(p+1)*65536]) for p in range(4)]
        result=machine.run(b.Case('readback',args=[plane,offset],
            writes=[(b.symbol_address('g_3DB0'),b.words(0xa000)),
                    (b.symbol_address('g_3DD4'),b.words(0x8800))],
            observe=[b.Range('pattern',b.symbol_address('g_3D20'),128),
                     b.Range('busy',b.symbol_address('g_3DD4'),2)],return_kind='void'))
        state=[0x8800,machine.map_mask,machine.read_map,machine.mode,machine.gc,machine.seq]
        equal=(ctypes.string_at(native.tile_test_pattern(),128)==bytes.fromhex(result['ranges']['pattern'])
               and [native.tile_test_state(i) for i in range(6)]==state
               and result['ranges']['busy']=='0088')
        case={'entry':'o00_31AD_1A8F','plane':plane,'offset':offset,'matched':equal}
        cases.append(case)
        if not equal:raise AssertionError(case)
    return cases
