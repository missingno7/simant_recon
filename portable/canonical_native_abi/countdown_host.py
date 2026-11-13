import hashlib
SOURCE = 'src/window/text_bitmap_helpers.c'
REPLACEMENTS = {'extern int16_t  fd_1B73_0006;': '', 'void  timer_wait_countdown(int16_t ticks)\n{\n    fd_1B73_0006 = ticks;\n    while (fd_1B73_0006 != 0)\n        ;\n}': 'void  timer_wait_countdown(int16_t ticks)\n{\n    portable_m1b73_source_countdown_wait(ticks);\n}', 'void  timer_start_countdown(int16_t ticks)\n{\n    fd_1B73_0006 = ticks;\n}': 'void  timer_start_countdown(int16_t ticks)\n{\n    portable_m1b73_source_countdown_write(ticks);\n}', 'int16_t  timer_countdown_done(void)\n{\n    return !fd_1B73_0006;\n}': 'int16_t  timer_countdown_done(void)\n{\n    return portable_m1b73_source_countdown_is_zero();\n}'}

def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def adapt(source, rel):
    if rel != SOURCE:
        return (source, None)
    original = source
    for (before, after) in REPLACEMENTS.items():
        if source.count(before) != 1:
            raise ValueError('countdown access changed: ' + before.splitlines()[0])
        source = source.replace(before, after, 1)
    if 'fd_1B73_0006' in source:
        raise ValueError('unadapted countdown access remains')
    source = '#include "portable/whole_program/platform/m1b73_countdown.h"\n' + source
    return (source, {'kind': 'HOSTED_INT08_COUNTDOWN_ACCESS', 'input_sha256': digest(original), 'output_sha256': digest(source), 'asm_basis': 'src/platform/input_timer.asm:tmr_countdown and interrupt08', 'functions': ['timer_wait_countdown', 'timer_start_countdown', 'timer_countdown_done'], 'contract': 'word store, spin-until-zero, zero test; unsigned decrement by 5 per always-on BIOS tick, floor zero', 'boundary': 'canonical ASM countdown word serviced by the native BIOS clock; waiting services native input and presentation'})
