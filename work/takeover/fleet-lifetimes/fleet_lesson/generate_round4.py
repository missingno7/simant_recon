from pathlib import Path
base=Path(__file__).with_name('base.c').read_text(encoding='latin1')
name='int far LessonDone(int lesson)\n{'; pos=base.index(name); head,fn=base[:pos],base[pos:]
old7='''        if (MeLocY + MeLocX != fd_50F6_1074 && fd_50F6_0B1E == 0 && f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
'''
old9='''        if (fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074 || f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
'''
assert fn.count(old7)==2 and fn.count(old9)==1
nested7='''        if (MeLocY + MeLocX != fd_50F6_1074)
            if (fd_50F6_0B1E == 0)
                if (f_00F8_02BE() > fd_50F6_0204)
                    return 1;
        break;
'''
nested9='''        if (fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074)
            return 1;
        if (f_00F8_02BE() > fd_50F6_0204)
            return 1;
        break;
'''
fn1=fn.replace(old7,nested7).replace(old9,nested9)
Path(__file__).with_name('case7_9_nested_short_circuit.c').write_text(head+fn1,encoding='latin1',newline='')
# Lazy call-result local: declaration lifetime starts after the exact guards seen in the listing.
old7local='''        if (MeLocY + MeLocX != fd_50F6_1074 && fd_50F6_0B1E == 0) {
            long now = f_00F8_02BE();
            if (now > fd_50F6_0204)
                return 1;
        }
        break;
'''
old9local='''        if (fd_50F6_0508.y + fd_50F6_0508.x != fd_50F6_1074) {
            return 1;
        } else {
            long now = f_00F8_02BE();
            if (now > fd_50F6_0204)
                return 1;
        }
        break;
'''
fn2=fn.replace(old7,old7local).replace(old9,old9local)
assert fn2.count(old7local)==2 and fn2.count(old9local)==1
Path(__file__).with_name('case7_9_time_result_lifetime.c').write_text(head+fn2,encoding='latin1',newline='')
from shutil import copyfile
outdir=Path(__file__).with_name('round4-sources');outdir.mkdir(exist_ok=True)
for nm in ['base.c','case7_9_nested_short_circuit.c','case7_9_time_result_lifetime.c']:
 copyfile(Path(__file__).with_name(nm),outdir/nm)
