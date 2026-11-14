"""Preserve S13's adjacent signed-byte position tables as one native object.

Original DS:2A56..2AC9, established by DrawSimKid/DrawDog/DrawSimCat operands
and the whole exact yard_window module. Initializers are extracted from source.
See evidence/canonical/native-yard-offsets/README.md. No frame/motion rewrite.
"""
import re

TABLES = (('kidX', 12), ('kidY', 44), ('dogWalkX', 12),
          ('dogWalkY', 8), ('catOfs', 40))


def adapt(source):
    declarations = []
    initializers = []
    offset = 0
    offsets = {}
    for name, count in TABLES:
        pattern = (r'static signed char ' + name + r'\[' + str(count) +
                   r'\] = (\{[^{}]*\});')
        matches = list(re.finditer(pattern, source))
        if len(matches) != 1:
            raise ValueError('Yard position table declaration changed: ' + name)
        match = matches[0]
        declarations.append('    signed char ' + name + '[' + str(count) + '];')
        initializers.append('    .' + name + ' = ' + match[1] + ',')
        source = source[:match.start()] + source[match.end():]
        offsets[name] = offset
        offset += count
    header = ('/* One character view of the complete DOS position-table object. */\n'
              'struct YardPositionTables {\n' + '\n'.join(declarations) + '\n};\n'
              'static struct YardPositionTables yard_position_tables = {\n' +
              '\n'.join(initializers) + '\n};\n')
    # A pointer to a member array would still make crossing its end undefined.
    # Character access to the enclosing object has the complete 116-byte extent.
    for name, base in offsets.items():
        source, count = re.subn(r'\b' + name + r'\[([^\[\]]+)\]',
                               lambda m: ('((signed char *)&yard_position_tables)[' +
                                          str(base) + ' + (' + m[1] + ')]'), source)
        if not count:
            raise ValueError('Yard position table consumer missing: ' + name)
    return header + source
