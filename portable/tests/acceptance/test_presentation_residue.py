"""Output-relevance controls for opaque animation IDs and clip-list residue."""
import subprocess
import re
import tempfile
import unittest
from pathlib import Path
from portable.canonical_native_abi.scalar import convert
from .step_state import fingerprint

ROOT=Path(__file__).resolve().parents[3]


class PresentationResidue(unittest.TestCase):
    def test_actual_animation_ids_are_opaque(self):
        source=(ROOT/'src/graphics/anim.c').read_text().replace('#include "rect.h"',
            'struct Rect { int left,top,right,bottom; };')
        prefix=source[:source.index('void far hanim_PrintSet')]
        functions=[]
        for name in ('_hanim_FindObject','hanim_AddAnimObject','hanim_RemoveAnimObject',
                     'hanim_ActuallyRemoveAnimObjects','hanim_HideObject','hanim_ShowObject',
                     'hanim_SetObjectPos','hanim_MakeAnimSet'):
            match=re.search(r'(?m)^[^\n;]*\b'+name+r'\([^\n]*\)\n\{',source)
            functions.append(source[match.start():source.index('\n}',match.end())+2])
        source=prefix+'\nstatic int s_688A=0;\n'+'\n'.join(functions)
        header='#include <stdint.h>\n#include <stdlib.h>\n#include <stdio.h>\n#include <string.h>\n'
        providers=r'''
static unsigned char fill;
char gfx_display_mode;
struct AnimObj *anim_last_added_object;
char *mem_Lock(Handle h){return *h;}
Handle mem_Unlock(Handle h){return h;}
Handle mem_Alloc(int32_t n,int16_t flags,char *name){
  Handle h=malloc(sizeof(*h));*h=malloc(n);memset(*h,fill,n);return h;
}
Handle mem_Realloc(Handle h,int32_t n,int16_t flags){*h=realloc(*h,n);return h;}
void mem_Free(Handle h){free(*h);free(h);}
void *_fmemmove(void *d,void *s,uint16_t n){return memmove(d,s,n);}
void gr_BitMapSize(struct Size *p,int16_t pic){p->w=11;p->h=13;}
void Punt(char *msg,...){exit(77);}
int main(int argc,char **argv){
  fill=(unsigned char)atoi(argv[1]);
  Handle h=hanim_MakeAnimSet();
  int16_t a=hanim_AddAnimObject(h,5,7,100,10);
  int16_t b=hanim_AddAnimObject(h,20,30,200,20);
  if(a==b)return 10;
  if(argc>2) {hanim_ShowObject(h,(int16_t)(b+123));return 99;}
  hanim_SetObjectPos(50,60,101,h,a,30); /* reinsertion swaps opaque IDs */
  hanim_HideObject(h,b);hanim_ShowObject(h,b);
  hanim_ActuallyRemoveAnimObjects(h);
  struct AnimSet *set=(void *)mem_Lock(h);
  struct AnimObj *p=(void *)mem_Lock(set->objs);
  if(set->count!=2)return 11;
  for(int i=0;i<set->count;i++,p++)
    printf("%d %d %d %d %d %d %d %d\n",p->x,p->y,p->pic,p->pri,p->show,p->remove,p->w,p->h);
  if(_hanim_FindObject((void *)*set->objs,&set->count,a,&a)->pic!=101)return 12;
  return 0;
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'anim.c';exe=path.with_suffix('.exe')
            path.write_text(header+convert(source)+providers)
            run=subprocess.run(['C:/msys64/mingw64/bin/gcc.exe','-std=c11','-O2',
                '-ffunction-sections','-fdata-sections',str(path),'-Wl,--gc-sections','-o',str(exe)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            outputs=[]
            for fill in (0,85,255):
                run=subprocess.run([str(exe),str(fill)],capture_output=True,timeout=10)
                self.assertEqual(run.returncode,0,run.stderr)
                outputs.append(run.stdout)
            self.assertEqual(outputs,[outputs[0]]*3)
            self.assertEqual(subprocess.run([str(exe),'85','bad-id'],capture_output=True,timeout=10).returncode,77)

    def test_clip_sentinel_and_raw_negative(self):
        a=b'\x00\x01\x00\x80'+bytes(60)
        b=a[:4]+bytes([0x55])*60
        self.assertEqual(fingerprint(a,True),fingerprint(b,True))
        self.assertNotEqual(fingerprint(a),fingerprint(b))
        self.assertNotEqual(fingerprint(a,True),fingerprint(b'\x01'+a[1:],True))


if __name__=='__main__':unittest.main()
