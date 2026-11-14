import re

def adapt(unit: str, source: str) -> tuple[str, dict | None]:
    if unit not in {'src/graphics/font_resources.c', 'src/graphics/font_output.c', 'src/ui/yard_window.c'}:
        return (source, None)
    changes = []
    if unit in {'src/graphics/font_resources.c', 'src/graphics/font_output.c'}:
        (source, count) = re.subn('struct Bitmap\\s*\\{[^{}]*\\};', '', source)
        if count != 1:
            raise ValueError('Bitmap source family changed')
        changes.append('common native Bitmap definition')
    if unit == 'src/graphics/font_resources.c':
        (source, count) = re.subn('struct Font\\s*\\{[^{}]*\\};', '', source)
        if count != 1:
            raise ValueError('Font source definition changed')
        old = 'mem_malloc(0x2a, "FontHeader")'
        if source.count(old) != 1:
            raise ValueError('Font runtime allocation changed')
        source = source.replace(old, 'mem_malloc(sizeof(struct Font), "FontHeader")')
        changes.extend(['common Font definition; 26-byte wire-read prefix retained', 'runtime FontHeader allocation 0x2a -> sizeof(struct Font), native pointers'])
    if unit == 'src/ui/yard_window.c':
        from .yard_offsets import adapt as yard_position_views
        source = yard_position_views(source)
        changes.append('DOS-adjacent signed-byte Yard position tables, complete-object character view')
        old = 'extern int far out_buffer;'
        if source.count(old) != 1:
            raise ValueError('S13 Bitmap width view changed')
        source = source.replace(old, '')
        (source, count) = re.subn('\\bout_buffer\\b', 'out_buffer.width', source)
        if count != 1:
            raise ValueError('S13 Bitmap width use count changed')
        changes.append('same-address S13 scalar width view -> Bitmap.width')
    source = '#include "portable/whole_program/types/fonts.h"\n' + source
    return (source, {'kind': 'NATIVE_FONT_RUNTIME_LAYOUT', 'source': unit, 'changes': changes, 'limits': 'source algorithms retained; glyph raster/platform buffers require separate providers'})
