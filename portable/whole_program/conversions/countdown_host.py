"""Replace source accesses to the INT08-owned countdown with its host owner."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/root/m208F.c'
SOURCE_SHA = '57fc64215f6ff681790e1afe2321f0348ee0cb8c3fbce066cef5f2dd5a18a72e'
REPLACEMENTS = {
    '''extern int16_t  fd_1B73_0006;''': '',
    '''void  f_208F_0530(int16_t ticks)
{
    fd_1B73_0006 = ticks;
    while (fd_1B73_0006 != 0)
        ;
}''': '''void  f_208F_0530(int16_t ticks)
{
    portable_m1b73_source_countdown_wait(ticks);
}''',
    '''void  f_208F_054B(int16_t ticks)
{
    fd_1B73_0006 = ticks;
}''': '''void  f_208F_054B(int16_t ticks)
{
    portable_m1b73_source_countdown_write(ticks);
}''',
    '''int16_t  f_208F_055B(void)
{
    return !fd_1B73_0006;
}''': '''int16_t  f_208F_055B(void)
{
    return portable_m1b73_source_countdown_is_zero();
}''',
}

def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def adapt(source, rel):
    if rel != SOURCE:
        return source, None
    if hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('countdown source identity changed')
    original = source
    for before, after in REPLACEMENTS.items():
        if source.count(before) != 1:
            raise ValueError('countdown access changed: ' + before.splitlines()[0])
        source = source.replace(before, after, 1)
    if 'fd_1B73_0006' in source:
        raise ValueError('unadapted countdown access remains')
    source = '#include "portable/whole_program/platform/m1b73_countdown.h"\n' + source
    return source, {'kind': 'HOSTED_INT08_COUNTDOWN_ACCESS',
        'input_sha256': digest(original), 'output_sha256': digest(source),
        'source_sha256': SOURCE_SHA,
        'asm_basis': 'src/root/m1B73.asm:tmr_countdown and interrupt08',
        'functions': ['f_208F_0530', 'f_208F_054B', 'f_208F_055B'],
        'contract': 'word store, spin-until-zero, zero test; unsigned decrement by 5 per always-on BIOS tick, floor zero',
        'boundary': 'interrupt-owned code-segment word replaced by one application timer owner; waiting services native input and presentation'}
