from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE_PATH = ROOT / 'portable/tools/recover_source.py'
BASE_SHA256 = 'c1fd7616c392d39ebe4574e6ccde85b4e7f79205d21afcfbcb7ead249d5ffc50'
NEXT3_PATH = ROOT / 'portable/tools/recover_source_next3.py'
NEXT3_SHA256 = '2a819b1c9d23213ecfd8fdebbb3bae580b8ef0914e535357b3e91aa0d2606edd'
SOURCE_PATH = ROOT / 'src/root/m0798.c'
SOURCE_SHA256 = 'ecf807dc3159f583f6ee3ea8a9f5422650a64bb557d4551e9c97b5dcc7b6a1b8'
OUT_SOURCE = ROOT / 'build/workers/behavior_controls_next4/m0798_controls.c'
EXTENSION_ID = 'selected-control-init-source-next4-v1'
FUNCTIONS = ['InitTriVars','SetTriLatPoint','cvtLevels2IdealCaste','win_ModeControlClosed',
             'win_CasteControlClosed','win_ModeControlChanged','win_CasteControlChanged','initControls']
HOST_EDGES = ['win_GetObjRect(0x120D/0x130D, Rect*)',
              'f_208F_0419(&knobSize,0x578)',
              'hanim_RemoveAnimSet(handle) only when prior animation handle is non-null']


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'cannot import {path}')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def extract_named(source: str, name: str) -> tuple[str,int,int]:
    match = re.search(r'(?m)^\s*void\s+far\s+' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', source)
    if match is None:
        raise RuntimeError(f'missing source definition {name}')
    start = source.find('{', match.start())
    depth = 0; in_string = False; quote = ''; escaped = False; i = start
    while i < len(source):
        c = source[i]
        if in_string:
            if escaped: escaped = False
            elif c == '\\': escaped = True
            elif c == quote: in_string = False
        else:
            if c in ('"', "'"):
                in_string = True; quote = c
            elif c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    body = source[match.start():i+1]
                    return body, source.count('\n',0,match.start())+1, source.count('\n',0,i+1)+1
        i += 1
    raise RuntimeError(f'unbalanced definition {name}')


def transform_word_views(text: str) -> tuple[str,list[dict[str,object]]]:
    rewrites = [
      (r'\bunsigned\s+(half|w)\s*;', r'unsigned int \1;'),
      (r'void\s+far\s+SetTriLatPoint\s*\(struct TriLevel far \*level,', 'void far SetTriLatPoint(unsigned int far *level,'),
      (r'level->frac', 'level[0]'),
      (r'level->weight', 'level[2]'),
      (r'SetTriLatPoint\(&casteLevels,', 'SetTriLatPoint(casteLevels,'),
      (r'SetTriLatPoint\(&modeLevels,', 'SetTriLatPoint(modeLevels,'),
      (r'\(&casteLevels\.frac\)\[([012])\]', r'casteLevels[\1]'),
      (r'\(&casteLevels\.frac\)\[i\]', 'casteLevels[i]'),
      (r'\(&modeLevels\.frac\)\[i\]', 'modeLevels[i]'),
      (r'\(&fd_3D57_0810\[0\]\.frac\)\[i\]', 'fd_3D57_0810[i]'),
      (r'\(&fd_3D57_07F2\[0\]\.frac\)\[i\]', 'fd_3D57_07F2[i]'),
    ]
    rows=[]
    for pattern,replacement in rewrites:
        text,n=re.subn(pattern,replacement,text)
        if n == 0:
            raise RuntimeError(f'word-view adaptation did not match: {pattern}')
        rows.append({'pattern':pattern,'replacement':replacement,'count':n,
                     'reason':'use source byte offsets over canonical 16-bit array storage; avoids incompatible struct lvalue/aliasing'})
    return text,rows


def build_source() -> tuple[bytes,dict[str,object]]:
    raw = SOURCE_PATH.read_bytes(); source=raw.decode('utf-8')
    if sha(raw)!=SOURCE_SHA256: raise RuntimeError('pinned m0798 source changed')
    extracted={}; anchors={}
    for name in FUNCTIONS:
        extracted[name], start, end = extract_named(source,name)
        anchors[name]={'source_path':'src/root/m0798.c','source_sha256':sha(raw),
                       'line_start':start,'line_end':end,
                       'body_sha256':sha(extracted[name].encode())}
    header='''struct Rect { int left; int top; int right; int bottom; };\nstruct Pt { int x; int y; };\nstruct TriPoints { int apexX; int apexY; int leftX; int leftY; int rightX; int rightY; };\nstruct TriLevel { unsigned int frac; unsigned int mid; unsigned int weight; };\ntypedef void * Handle;\n'''
    decls='''extern void _fastcall win_GetObjRect(int obj, struct Rect far *rect);\nextern void f_208F_0419(struct Pt *size, int id);\nextern void hanim_RemoveAnimSet(Handle handle);\nextern unsigned int far triWidth;\nextern unsigned int far triWidthR;\nextern unsigned int far triWidthL;\nextern unsigned int far triHeight;\nextern long far fd_50F6_382E;\nextern struct TriPoints far fd_50F6_3816;\nextern struct TriPoints far fd_50F6_3822;\nextern struct Pt far fd_50F6_0358;\nextern struct Pt far fd_50F6_022E;\nextern struct Pt far knobSize;\nextern int far CasteAuto;\nextern int far fd_50F6_0468;\nextern int far fd_3D57_07EA;\nextern int far fd_50F6_0370;\nextern int far fd_50F6_024E;\nextern unsigned int far casteLevels[3];\nextern unsigned int far fd_3D57_080A[3];\nextern unsigned int far fd_3D57_07EC[3];\nextern unsigned int far fd_3D57_0810[12];\nextern unsigned int far fd_3D57_07F2[12];\nextern void * far fd_50F6_37F6;\nextern void * far fd_50F6_37F2;\nextern void far InitTriVars(int obj, struct TriPoints far *tri);\nextern void far SetTriLatPoint(struct TriLevel far *level, struct TriPoints far *tri, struct Pt far *out);\nextern void far cvtLevels2IdealCaste(int far *ideal);\nextern void far win_ModeControlChanged(void);\nextern void far win_CasteControlChanged(void);\nextern void far win_ModeControlClosed(void);\nextern void far win_CasteControlClosed(void);\n'''
    text=header+decls+'\n\n'.join(extracted[n] for n in FUNCTIONS)+'\n'
    text,rewrites=transform_word_views(text)
    OUT_SOURCE.parent.mkdir(parents=True,exist_ok=True)
    OUT_SOURCE.write_text(text,encoding='utf-8',newline='')
    return OUT_SOURCE.read_bytes(),{'original_source_sha256':sha(raw),'function_anchors':anchors,
                                   'generated_slice_sha256':sha(OUT_SOURCE.read_bytes()),
                                   'word_view_rewrites':rewrites}


def main() -> int:
    base_bytes=BASE_PATH.read_bytes()
    if sha(base_bytes)!=BASE_SHA256: raise RuntimeError('pinned base generator changed')
    if sha(NEXT3_PATH.read_bytes())!=NEXT3_SHA256: raise RuntimeError('pinned next3 wrapper changed')
    next3=load(NEXT3_PATH,'next3')
    base=next3._load_base()
    balloon_extension=next3.balloon_state_extension(base)
    selected_bytes, anchors=build_source()
    base.MODULES['root_m0798_controls']='build/workers/behavior_controls_next4/m0798_controls.c'
    argv=sys.argv[1:]
    if '--out' not in argv: argv += ['--out','build/workers/recovered_source_next4/generated']
    if '--compile' not in argv: argv += ['--compile']
    sys.argv=[str(Path(__file__)),*argv]
    result=base.main()
    if result: return result
    out=Path(argv[argv.index('--out')+1]); out=out if out.is_absolute() else ROOT/out
    pp=out.resolve()/'provenance.json'; provenance=json.loads(pp.read_text(encoding='utf-8'))
    compiled_module=out.resolve()/'root_m0798_controls.c'
    broken=out.resolve()/'root_m0798_controls_negative.c'
    compiled_text=compiled_module.read_text(encoding='utf-8')
    negative_text=compiled_text.replace('casteLevels[i] = fd_3D57_07EC[i];',
                                        '(&casteLevels.frac)[i] = fd_3D57_07EC[i];')
    if negative_text==compiled_text:
        raise RuntimeError('negative-control source perturbation did not apply')
    broken.write_text(negative_text,encoding='utf-8',newline='')
    negative_obj=out.resolve()/'root_m0798_controls_negative.o'
    negative_proc=subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I',str(out.resolve()),'-c',str(broken),'-o',str(negative_obj)],
                                 cwd=ROOT,capture_output=True,text=True)
    if negative_proc.returncode==0:
        raise RuntimeError('invalid structure-member access unexpectedly compiled')
    ext={'schema':'simant-recovered-source-profile-extension-v1','id':EXTENSION_ID,
         'status':'DIAGNOSTIC_ONLY_NOT_PRODUCTION','base_generator_path':'portable/tools/recover_source.py',
         'base_generator_sha256':BASE_SHA256,'parent_extension_id':balloon_extension['id'],
         'parent_extension_wrapper_sha256':balloon_extension['wrapper_sha256'],
         'wrapper_path':Path(__file__).resolve().relative_to(ROOT).as_posix(),
         'wrapper_sha256':sha(Path(__file__).read_bytes()),'selected_source':anchors,
         'selected_functions':FUNCTIONS,'explicit_host_edges':HOST_EDGES,
         'negative_compile_control':{'mutation':'replace explicit word-index access to casteLevels with original .frac member form against uint16_t[3] canonical view',
            'compile_returncode':negative_proc.returncode,'expected_failure':True,
            'diagnostics':(negative_proc.stdout+negative_proc.stderr)[-4000:]},
         'source_global_views':{
           'modeLevels':'existing canonical uint16_t[3] at 50F6:049E; frac/mid/weight word accesses explicitly lowered by index',
           'casteLevels':'uint16_t[3] at 50F6:0482, alias fd_50F6_0482',
           'fd_3D57_0810':'uint16_t[12] from 24-byte DATA extent; first three consecutive words are the first preset struct fields',
           'fd_3D57_07F2':'uint16_t[12] from 24-byte DATA extent; first three consecutive words are the first preset struct fields',
           'fd_50F6_3816/3822':'struct TriPoints, each six source int16 fields (12 bytes)',
           'fd_50F6_0358/022E/knobSize':'struct Pt, each two source int16 fields (4 bytes)',
           'fd_50F6_37F6/37F2':'host opaque void* animation handles; no DOS pointer identity'} ,
         'limits':['selected source functions only; unrelated input/event/drawing UI bodies excluded',
                   'strict compile proves C/TU integration only, not behavior or full state initialization',
                   'the three UI services are required host calls and must not be stubbed']}
    provenance['versioned_profile_extension']=ext
    provenance['parent_profile_extension']=balloon_extension
    pp.write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8',newline='')
    return 0

if __name__=='__main__': raise SystemExit(main())


