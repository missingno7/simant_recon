from pathlib import Path
base=Path(__file__).with_name('base.c').read_text(encoding='latin1'); start=base.index('int far LessonDone(int lesson)\n{'); head,fn=base[:start],base[start:]
old7='''        if (MeLocY + MeLocX != fd_50F6_1074 && fd_50F6_0B1E == 0 && f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
'''
old9='''        if (fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074 || f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
'''
nested7='''        if (MeLocY + MeLocX != fd_50F6_1074)
            if (fd_50F6_0B1E == 0)
                if (f_00F8_02BE() > fd_50F6_0204)
                    return 1;
        break;
'''
split9='''        if (fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074)
            return 1;
        if (f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
'''
assert fn.count(old7)==2 and fn.count(old9)==1
Path(__file__).with_name('case7_nested_only.c').write_text(head+fn.replace(old7,nested7),encoding='latin1',newline='')
Path(__file__).with_name('case9_split_only.c').write_text(head+fn.replace(old9,split9),encoding='latin1',newline='')
from shutil import copyfile
outdir=Path(__file__).with_name('round5-sources');outdir.mkdir(exist_ok=True)
for nm in ['base.c','case7_nested_only.c','case9_split_only.c','case7_9_nested_short_circuit.c']:
 copyfile(Path(__file__).with_name(nm),outdir/nm)
