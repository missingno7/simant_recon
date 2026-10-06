from __future__ import annotations
import re
HEADER = '#include "portable/whole_program/conversions/pointer_globals.h"\n'
DATABASE_UNIT = 'src/root/m1A53.c'
FONT_UNITS = {'src/root/m24AB.c', 'src/root/m1629.c'}

def adapt(unit: str, source: str) -> tuple[str, dict | None]:
    if unit not in FONT_UNITS | {DATABASE_UNIT}:
        return (source, None)
    changes: list[str] = []
    text = source
    if unit == DATABASE_UNIT:
        declaration = 'extern\\s+int\\s+far\\s+db_handles\\s*\\[\\s*\\]\\s*;'
        (text, count) = re.subn(declaration, '', text)
        if count != 1:
            raise ValueError('m1A53: expected one unsized db_handles declaration')
        changes.append('db_handles declaration -> one four-entry native int16 table')
    elif unit == 'src/root/m24AB.c':
        definition = 'void\\s+far\\s*\\*\\s*fd_55B3_65A4\\s*=\\s*0\\s*;'
        (text, count) = re.subn(definition, 'struct Font *fd_55B3_65A4 = 0;', text)
        if count != 1:
            raise ValueError('m24AB: expected sole current-font pointer definition')
        declaration = 'extern\\s+void\\s+far\\s*\\*\\s*fd_50F6_4A1A\\s*\\[\\s*\\]\\s*;'
        (text, count) = re.subn(declaration, '', text)
        if count != 1:
            raise ValueError('m24AB: expected font table declaration')
        changes.extend(['fd_55B3_65A4 source definition retained as typed struct Font* owner', 'fd_50F6_4A1A declaration -> four-slot source-used native Font* table'])
    elif unit == 'src/root/m1629.c':
        declaration = 'extern\\s+void\\s+far\\s*\\*\\s*far\\s+fd_55B3_65A4\\s*;'
        (text, count) = re.subn(declaration, '', text)
        if count != 1:
            raise ValueError('m1629: expected current-font pointer alias declaration')
        changes.append('current-font pointer use shares the root:m24AB typed owner')
    if HEADER not in text:
        text = HEADER + text
    return (text, {'kind': 'SHARED_POINTER_REPRESENTATION_CONVERSION', 'source': unit, 'changes': changes, 'provenance': {'db_handles': 'layout/symbols.json 50F6:3B50; next symbol 3B58; src/root/m1A28.c GetFreeHandle scans exactly four slots; four int16 values occupy source bytes 3B50..3B57', 'fd_50F6_4A1A': 'layout/symbols.json 50F6:4A1A..4A41; src/root/m24AB.c writes slots 0..3 and f_24AB_02AD clamps reads to font-2..font-5 (indices 0..3); only these slots become native pointers', 'fd_55B3_65A4': 'src/root/m24AB.c defines one initialized-null selector; root:m1629 has only an extern use; layout/symbols.json 55B3:65A4 grounds its font-pointer role', 'db_cacheTable': 'left defined by source root:m1A53 db_cacheTable = 0L; no duplicate native definition introduced', 'database_records': 'src/state/database-record-state.c and src/state/database-index-state.c supply the sole canonical record and cursor owners; native conversion widens their pointer fields using the shared wire/runtime views'}, 'limits': ['Native pointer addresses intentionally differ from DOS far segment:offset values.', 'The six unused source font-table pointer slots and any adjacent/unowned source bytes are not expanded into host pointer storage.', 'This is ownership/layout conversion evidence only; DB open/read/decompression runtime behavior remains a separate integration contract.']})
