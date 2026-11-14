"""Semantic controls for the owner-approved identity-pattern observation."""
from pathlib import Path
import subprocess,tempfile,unittest
from .animation_identity import original_scalars
HERE=Path(__file__).resolve().parent

class AnimationIdentity(unittest.TestCase):
    def test_original_local_bindings(self):
        self.assertEqual(len(original_scalars()),8)

    def test_c_and_cpp_identity_patterns(self):
        source=r'''
#include "animation_identity.h"
#include <stdio.h>
#include <string.h>
#define CHECK(c) do {if(!(c)){fprintf(stderr,"line %d\n",__LINE__);return 1;}}while(0)
static void put(uint8_t *p,unsigned i,uint16_t v){p[2*i]=v&255;p[2*i+1]=v>>8;}
int main(void){
 uint8_t a[34],b[34],copy[34];
 /* Every 5-slot partition over three live names plus the sentinel. Rename
  * bijectively, checking both aliases and the first-appearance order. */
 for(unsigned bits=0;bits<1024;++bits){
  unsigned x=bits,count=0;uint16_t seen[3];
  for(unsigned i=0;i<5;++i){unsigned v=x&3;x>>=2;
   put(a,i,v==3?65535:v);put(b,i,v==3?65535:(uint16_t)(32767-991*v));
   uint16_t expected=65535;
   if(v!=3){unsigned j=0;while(j<count && seen[j]!=v)++j;if(j==count)seen[count++]=(uint16_t)v;expected=(uint16_t)j;}
   CHECK(simant_anim_identity_word(a,i)==expected);
   CHECK(simant_anim_identity_word(b,i)==expected);
  }
  memcpy(copy,a,10);CHECK(simant_anim_identity_hash(a,5)==simant_anim_identity_hash(b,5));CHECK(!memcmp(copy,a,10));
 }
 put(a,0,10);put(a,1,20);put(a,2,10);put(a,3,65535);
 memcpy(b,a,8);put(b,2,30);CHECK(simant_anim_identity_hash(a,4)!=simant_anim_identity_hash(b,4)); /* broken alias */
 memcpy(b,a,8);put(b,3,10);CHECK(simant_anim_identity_hash(a,4)!=simant_anim_identity_hash(b,4)); /* missing sentinel */
 put(a,0,65534);put(b,0,65533);CHECK(simant_anim_identity_hash(a,1)!=simant_anim_identity_hash(b,1)); /* invalid words remain raw */
 for(unsigned i=0;i<17;++i){put(a,i,(uint16_t)(32767-i));CHECK(simant_anim_identity_word(a,i)==i);} /* max width */
 puts("PASS renaming, alias/sentinel negatives, invalid words, immutable input,17 slots");return 0;
}
'''
        with tempfile.TemporaryDirectory() as path:
            out=Path(path);file=out/'identity.c';file.write_text(source)
            for cc,standard in [('gcc','c11'),('g++','c++17')]:
                exe=out/(cc+'.exe')
                subprocess.run(['C:/msys64/mingw64/bin/'+cc+'.exe','-O2','-std='+standard,'-I'+str(HERE),str(file),'-o',str(exe)],check=True,capture_output=True,timeout=60)
                run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=20)
                self.assertEqual(run.returncode,0,run.stderr)

if __name__=='__main__':unittest.main()
