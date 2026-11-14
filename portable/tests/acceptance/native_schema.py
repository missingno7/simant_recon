"""Read native object extents/locations from PE DWARF, without a debugger.

Only fixed DW_OP_addr storage and fully sized types are accepted. Pointers in
any member exclude the entire view, as in the former observer. No nearest-name
or next-symbol size guesses are used.
"""
import io
import re
import subprocess
from functools import lru_cache
from pathlib import Path
import pefile
from elftools.dwarf.dwarfinfo import DWARFInfo, DwarfConfig, DebugSectionDescriptor


class NativeSymbols:
    def __init__(self, path):
        pe = pefile.PE(str(path))
        sections = {}
        strings = pe.FILE_HEADER.PointerToSymbolTable + pe.FILE_HEADER.NumberOfSymbols * 18
        for section in pe.sections:
            name = section.Name.rstrip(b'\0').decode()
            if name.startswith('/'):
                start = strings + int(name[1:])
                name = pe.__data__[start:].split(b'\0', 1)[0].decode()
            sections[name] = DebugSectionDescriptor(io.BytesIO(section.get_data()[:section.Misc_VirtualSize]), name,
                                                   0, section.Misc_VirtualSize, 0)
        fields = ('info', 'aranges', 'abbrev', 'frame', 'eh_frame', 'str', 'loc',
                  'ranges', 'line', 'pubtypes', 'pubnames', 'addr', 'str_offsets',
                  'line_str', 'loclists', 'rnglists', 'sup', 'cu_index', 'tu_index', 'types')
        args = {('eh_frame_sec' if f == 'eh_frame' else 'debug_' + f + '_sec'):
                sections.get('.eh_frame' if f == 'eh_frame' else '.debug_' + f) for f in fields}
        # elftools versions differ in the optional DWARF5 section arguments.
        import inspect
        args = {k: args.get(k) for k in inspect.signature(DWARFInfo).parameters if k != 'config'}
        self.dwarf = DWARFInfo(config=DwarfConfig(True, 'x64', 8), **args)
        self.variables = {}
        nm = subprocess.check_output(['C:/msys64/mingw64/bin/nm.exe', str(path)], text=True)
        self.addresses = {name: int(at, 16) for at, name in
                          re.findall(r'^([0-9a-fA-F]+) [A-Z] (\S+)$', nm, re.M)}
        for cu in self.dwarf.iter_CUs():
            top = cu.get_top_DIE()
            filename = Path(top.attributes['DW_AT_name'].value.decode().replace('\\', '/')).name
            for die in cu.iter_DIEs():
                if die.tag != 'DW_TAG_variable':
                    continue
                if die.get_parent().tag != 'DW_TAG_compile_unit':
                    continue
                attr = die.attributes.get('DW_AT_name')
                if attr is None:
                    continue
                name = attr.value.decode()
                location = die.attributes.get('DW_AT_location')
                if location and isinstance(location.value, list) and len(location.value) == 9 and location.value[0] == 3:
                    address = int.from_bytes(bytes(location.value[1:]), 'little')
                elif die.attributes.get('DW_AT_external') and name in self.addresses:
                    address = self.addresses[name]
                else:
                    continue
                self.variables.setdefault(name, []).append((filename, address, die))

    def shape(self, die, seen=None):
        seen = set() if seen is None else seen
        if die.offset in seen:
            raise ValueError('Recursive non-pointer type')
        seen = seen | {die.offset}
        if die.tag == 'DW_TAG_pointer_type':
            return die.attributes.get('DW_AT_byte_size').value if 'DW_AT_byte_size' in die.attributes else 8, True
        if die.tag in ('DW_TAG_typedef', 'DW_TAG_const_type', 'DW_TAG_volatile_type', 'DW_TAG_variable'):
            return self.shape(die.get_DIE_from_attribute('DW_AT_type'), seen)
        if die.tag == 'DW_TAG_array_type':
            size, pointer = self.shape(die.get_DIE_from_attribute('DW_AT_type'), seen)
            for child in die.iter_children():
                if child.tag != 'DW_TAG_subrange_type':
                    continue
                count = child.attributes.get('DW_AT_count')
                upper = child.attributes.get('DW_AT_upper_bound')
                size *= count.value if count else upper.value + 1 if upper else 0
            return size, pointer
        size = die.attributes['DW_AT_byte_size'].value
        pointer = any(self.shape(c.get_DIE_from_attribute('DW_AT_type'), seen)[1]
                      for c in die.iter_children() if c.tag == 'DW_TAG_member')
        return size, pointer

    def variable(self, name, filename=None):
        rows = self.variables.get(name, [])
        if filename:
            rows = [r for r in rows if r[0] == filename]
        definitions = [r for r in rows if 'DW_AT_location' in r[2].attributes]
        rows = definitions or rows
        shapes = {(r[1], *self.shape(r[2])) for r in rows}
        if len(shapes) != 1:
            raise ValueError('Missing/ambiguous fixed native storage: ' + str((name, filename, len(rows))))
        _, address, die = rows[0]
        size, pointer = self.shape(die)
        return address, size, pointer, die

    def expression(self, expression):
        names = expression.split('.')
        address, size, pointer, die = self.variable(names[0])
        for name in names[1:]:
            die = die.get_DIE_from_attribute('DW_AT_type')
            while die.tag in ('DW_TAG_typedef', 'DW_TAG_const_type', 'DW_TAG_volatile_type'):
                die = die.get_DIE_from_attribute('DW_AT_type')
            member = next(c for c in die.iter_children() if c.attributes.get('DW_AT_name') and
                          c.attributes['DW_AT_name'].value.decode() == name)
            address += member.attributes['DW_AT_data_member_location'].value
            die = member
            size, pointer = self.shape(die.get_DIE_from_attribute('DW_AT_type'))
        return address, size, pointer


@lru_cache(maxsize=2)
def read_symbols(path, modified):
    return NativeSymbols(Path(path))


def symbols_for(executable):
    return read_symbols(str(executable), executable.stat().st_mtime_ns)


def native_views(executable, specs, span_path):
    symbols = symbols_for(executable)
    import json
    spans = json.loads(span_path.read_text())['bindings'] if span_path.is_file() else {}
    result = {}
    for name, spec in specs.items():
        try:
            if spec.get('native_expr'):
                address, size, pointer = symbols.expression(spec['native_expr'])
                size = spec['bytes']  # explicitly normalized source word width
            else:
                owner = spec.get('owner', name)
                owner = 'seed' if name == 'g_8BA2' else owner
                if name in spans:
                    # The generated packed group is real DWARF storage; follow
                    # its member expression rather than assuming host adjacency.
                    address, size, pointer = symbols.expression(spans[name]['expression'])
                else:
                    address, size, pointer, _ = symbols.variable(owner, spec.get('native_file'))
            if spec.get('owner', name) in ('db_handles', 'startup_executable_fd'):
                result[name] = dict(status='EXCLUDED_HANDLE', reason='Platform file descriptor identity')
                continue
            if pointer:
                result[name] = dict(status='EXCLUDED_POINTER', reason='Address/handle/callback representation')
                continue
            offset = spec.get('offset', 0)
            length = spec.get('bytes', 0) if offset or not size else size
            if length <= 0 or size and offset + length > size:
                raise ValueError('Unsupported native extent')
            result[name] = dict(status='OK', address=address + offset, bytes=length)
        except (ValueError, KeyError, StopIteration, TypeError) as exc:
            result[name] = dict(status='UNAVAILABLE', reason=str(exc))
    return result

