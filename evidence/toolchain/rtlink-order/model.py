"""RTLink relocation descriptor hashing, transcribed from 4.14 file 0x6803a.

No observed permutation or fitted constants are stored here.  Descriptor flags,
frame and target IDs must be supplied by input processing.  Their origins and the
currently supported OMF subset are documented in RESULT.md.
"""
from dataclasses import dataclass
import struct

def ror16(x,n):
    n &= 15
    return ((x >> n) | (x << ((16-n)&15))) & 0xffff

def descriptor_hash(key: bytes, modulus=101):
    # AX starts with each zero-extended input byte; CL increases after each ROR.
    # BX is a 16-bit accumulator; DX is zero after the byte-count loop.
    return (sum(ror16(byte,j) for j,byte in enumerate(key)) & 0xffff) % modulus

@dataclass(frozen=True)
class Descriptor:
    tag: str
    flags: int
    secondary: int
    frame: int
    target: int
    def key(self):return struct.pack('<4H',self.flags,self.secondary,self.frame,self.target)

def relocation_groups(descriptors):
    """Prepend new keys to their bucket; traverse buckets upward.

    This operates on one final combined segment, not an entire link or object.
    The writer additionally filters converted/non-load descriptors. Callers here
    pass the surviving MZ base-relocation descriptors in first-FIXUPP order.
    """
    buckets=[[] for _ in range(101)];seen=set()
    for d in descriptors:
        key=d.key()
        if key not in seen:
            seen.add(key);buckets[descriptor_hash(key)].insert(0,d.tag)
    return [tag for bucket in buckets for tag in bucket]

def external_segment_groups(symbol_ids,first_fixups):
    # MASM 'mov ax,seg external' gives flags=048b, secondary=0000.
    return relocation_groups(Descriptor(name,0x048b,0,symbol_ids[name],symbol_ids[name]) for name in first_fixups)

if __name__=='__main__':
    import argparse,json
    ap=argparse.ArgumentParser();ap.add_argument('input',help='JSON containing symbol_ids and first_fixups');a=ap.parse_args()
    data=json.load(open(a.input));print(json.dumps(external_segment_groups(**data)))
