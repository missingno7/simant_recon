"""Bind sampled-sound timer boundaries in each DOS executable independently.

The caller supplies original root symbols or that candidate's SOURCE.MAP, plus
its relocated memory. Selector operands and the actual INT8 installation code
bind each entry; no original offsets are applied to the canonical executable.
Completion PCs require entry tracking: install_slow_timer_regs also reaches an
IRET after an ordinary PUSHF/CALL, and the interrupt handlers can nest.
"""

ENTRIES = (('t', 'snd_timer_mix_two_channels'),
           ('t', 'snd_timer_mix_four_channels'),
           ('u', 'snd_slow_timer_interrupt'))


def timer_binding(memory, base, addresses):
    """Return entry/completion PCs and inspectable instruction/IVT receipts."""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16
    from capstone.x86 import (X86_OP_IMM, X86_OP_MEM, X86_OP_REG,
                             X86_REG_AX, X86_REG_DX, X86_REG_ES, X86_REG_CS)
    decoder = Cs(CS_ARCH_X86, CS_MODE_16)
    decoder.detail = True
    names = ('snd_timer_reentrant_exit', 'snd_timer_mix_two_channels',
             'snd_timer_mix_four_channels', 'snd_slow_timer_interrupt',
             'snd_start_sample_timer', 'snd_slow_sample_timer',
             'snd_install_slow_timer_regs', 'snd_select_four_channel_timer',
             'snd_select_two_channel_timer', 'snd_restore_bios_timer')
    locations = {name: base + addresses[name] for name in names}
    ordered = [locations[name] for name in names]
    if ordered != sorted(set(ordered)) or ordered[-1] - ordered[0] > 4096:
        raise ValueError('Sound timer module anchors are not ordered and bounded')

    # The module's last public function ends at its own RETF. Decode the full
    # code contribution, including shared exits and device output routines;
    # stopping at the next public would miss both the shared fast IRET and the
    # IRET reached when a fast interrupt installs the slow timer.
    tail = []
    for ins in decoder.disasm(memory[ordered[-1]:ordered[-1] + 256], ordered[-1]):
        tail.append(ins)
        if ins.mnemonic == 'retf':
            break
    if not tail or tail[-1].mnemonic != 'retf':
        raise ValueError('Missing sound timer module final RETF')
    end = tail[-1].address + tail[-1].size
    instructions = list(decoder.disasm(memory[ordered[0]:end], ordered[0]))
    by_pc = {ins.address: ins for ins in instructions}
    if not instructions or instructions[-1].address + instructions[-1].size != end:
        raise ValueError('Incomplete sound timer instruction coverage')
    if not all(pc in by_pc for pc in ordered):
        raise ValueError('Sound timer public is not an instruction boundary')
    bodies = {name: [ins for ins in instructions
                     if locations[name] <= ins.address <
                     (ordered[index + 1] if index + 1 < len(ordered) else end)]
              for index, name in enumerate(names)}

    def direct_mem(op, segment=None, size=None):
        return (op.type == X86_OP_MEM and not op.mem.base and not op.mem.index
                and (segment is None or op.mem.segment == segment)
                and (size is None or op.size == size))

    def immediate_stores(name):
        return [ins for ins in bodies[name] if ins.mnemonic == 'mov'
                and len(ins.operands) == 2 and direct_mem(ins.operands[0], size=2)
                and ins.operands[1].type == X86_OP_IMM]

    selector_pairs = []
    for selector, entry in (('snd_select_two_channel_timer', ENTRIES[0][1]),
                            ('snd_select_four_channel_timer', ENTRIES[1][1])):
        stores = immediate_stores(selector)
        if len(stores) != 2 or stores[0].operands[0].mem.disp != stores[1].operands[0].mem.disp + 2:
            raise ValueError('Ambiguous sound timer selection pointer: ' + selector)
        segment, offset = (ins.operands[1].imm for ins in stores)
        if segment * 16 + offset != locations[entry]:
            raise ValueError('Sound timer selector does not target named entry: ' + entry)
        selector_pairs.append((segment, stores[1].operands[0].mem.disp))
    if selector_pairs[0] != selector_pairs[1]:
        raise ValueError('Sound timer selectors disagree on code frame or pointer')
    segment, selected_pointer = selector_pairs[0]
    code_frame = segment * 16

    # Bind the slow offset/segment from actual register loads immediately
    # before ES:[20h]/[22h] writes, with ES explicitly zeroed for the IVT.
    slow = bodies['snd_install_slow_timer_regs']
    vector = {}
    for index, ins in enumerate(slow):
        if (ins.mnemonic != 'mov' or len(ins.operands) != 2
                or not direct_mem(ins.operands[0], X86_REG_ES, 2)
                or ins.operands[0].mem.disp not in (0x20, 0x22)):
            continue
        load = slow[index - 1]
        register = X86_REG_DX if ins.operands[0].mem.disp == 0x20 else X86_REG_AX
        if not (ins.operands[1].type == X86_OP_REG and ins.operands[1].reg == register
                and load.mnemonic == 'mov' and len(load.operands) == 2
                and load.operands[0].type == X86_OP_REG and load.operands[0].reg == register
                and load.operands[1].type == X86_OP_IMM):
            raise ValueError('Sound slow timer IVT operand is not independently bound')
        vector[ins.operands[0].mem.disp] = load.operands[1].imm
    if set(vector) != {0x20, 0x22} or vector[0x22] * 16 + vector[0x20] != locations[ENTRIES[2][1]]:
        raise ValueError('Sound slow timer IVT writes do not name the slow entry')
    if vector[0x22] != segment or not any(
            a.mnemonic == 'xor' and a.op_str == 'ax, ax'
            and b.mnemonic == 'mov' and b.op_str == 'es, ax'
            for a, b in zip(slow, slow[1:])):
        raise ValueError('Sound slow timer IVT segment setup differs')

    # The fast installer copies the same selected pointer into INT8. Verify
    # both source operands, rather than assuming the selectors are installed.
    fast = bodies['snd_start_sample_timer']
    writes = []
    for index, ins in enumerate(fast):
        if (ins.mnemonic == 'mov' and len(ins.operands) == 2
                and direct_mem(ins.operands[0], X86_REG_ES, 2)
                and ins.operands[0].mem.disp in (0x20, 0x22)):
            load = fast[index - 1]
            if not (load.mnemonic == 'mov' and len(load.operands) == 2
                    and direct_mem(load.operands[1], size=2)
                    and load.operands[1].mem.disp == selected_pointer + ins.operands[0].mem.disp - 0x20
                    and load.operands[0].type == X86_OP_REG
                    and ins.operands[1].type == X86_OP_REG
                    and load.operands[0].reg == ins.operands[1].reg):
                raise ValueError('Sound fast timer IVT source pointer differs')
            writes.append(ins.operands[0].mem.disp)
    if sorted(writes) != [0x20, 0x22]:
        raise ValueError('Missing sound fast timer IVT pointer installation')

    prefixes = {'snd_timer_mix_two_channels': [('push', 'ax'), ('mov', 'al, 0x20'), ('out', '0x20, al')],
                'snd_timer_mix_four_channels': [('push', reg) for reg in ('ax', 'bx', 'dx', 'si', 'ds', 'es')],
                'snd_slow_timer_interrupt': [('inc', None), ('push', 'ax'), ('push', 'ds')]}
    for name, expected in prefixes.items():
        actual = bodies[name][:len(expected)]
        if len(actual) != len(expected) or any(ins.mnemonic != mnemonic or operand is not None and ins.op_str != operand
                                               for ins, (mnemonic, operand) in zip(actual, expected)):
            raise ValueError('Sound timer entry instruction signature differs: ' + name)
    busy = bodies['snd_slow_timer_interrupt'][0].operands[0]
    if not direct_mem(busy, X86_REG_CS, 1):
        raise ValueError('Slow sound timer nesting operand is not CS byte storage')
    if not any(ins.mnemonic == 'inc' and len(ins.operands) == 1
               and direct_mem(ins.operands[0], X86_REG_CS, 1)
               and ins.operands[0].mem.disp == busy.mem.disp
               for ins in bodies['snd_timer_mix_two_channels']):
        raise ValueError('Fast and slow sound timer nesting operands differ')
    if not any(ins.mnemonic == 'jne' and len(ins.operands) == 1
               and ins.operands[0].type == X86_OP_IMM
               and ins.operands[0].imm == locations['snd_timer_reentrant_exit']
               for ins in bodies['snd_timer_mix_two_channels'][:8]):
        raise ValueError('Fast sound timer reentrant exit branch differs')

    old_vector = base + addresses['f_28BC_0000'] - code_frame
    irets = []
    chains = []
    for ins in instructions:
        if ins.mnemonic == 'iret':
            irets.append(ins.address)
        if ins.mnemonic in ('jmp', 'ljmp') and len(ins.operands) == 1:
            operand = ins.operands[0]
            if direct_mem(operand, X86_REG_CS, 4) and operand.mem.disp == old_vector:
                chains.append(ins.address)
    if len(irets) != 4 or len(chains) != 2:
        raise ValueError('Sound timer complete-module IRET/old-vector exits differ')
    for pc in irets + chains:
        previous = next((ins for ins in instructions if ins.address + ins.size == pc), None)
        if not (previous and previous.mnemonic == 'dec' and len(previous.operands) == 1
                and direct_mem(previous.operands[0], X86_REG_CS, 1)
                and previous.operands[0].mem.disp == busy.mem.disp):
            raise ValueError('Sound timer completion does not release its nesting operand')
    current_vector = int.from_bytes(memory[0x20:0x22], 'little') + 16 * int.from_bytes(memory[0x22:0x24], 'little')
    return dict(entries=[(kind, locations[name]) for kind, name in ENTRIES],
                completions=sorted(irets + chains), irets=irets, chains=chains,
                code_frame=code_frame, old_vector=code_frame + old_vector,
                observed_int8=current_vector,
                instructions={ins.address: bytes(ins.bytes).hex() for ins in instructions})


def timer_points(memory, base, addresses):
    return timer_binding(memory, base, addresses)['entries']


def timer_completion_points(memory, base, addresses):
    return timer_binding(memory, base, addresses)['completions']


def timer_tape(path, destination, service_limit):
    """Validate a complete capture and write ticks strictly before the limit.

    T rows contain a chronological service ordinal and mode (0 slow, 1 fast,
    2 nested fast entry rejected by the original busy guard).
    Equal ordinals retain their order. Optional capture comments describe the
    entry preceding a completion; output omits them for the native reader.
    The entire input, including the excluded suffix, must terminate with E.
    """
    import re
    from pathlib import Path
    maximum = (1 << 64) - 1
    if type(service_limit) is not int or not 0 <= service_limit <= maximum:
        raise ValueError('Invalid audio timer service limit')
    rows = []
    previous = 0
    pending = []
    ended = False
    for number, raw in enumerate(Path(path).read_text(encoding='ascii').splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if ended:
            raise ValueError('Audio timer content follows E at line ' + str(number))
        if line == 'E':
            if pending:
                raise ValueError('Audio timer entry has no completion')
            ended = True
            continue
        comment = re.fullmatch(r'# entry ([0-9A-Fa-f]+) ([0-9]+) ([0-9]+) ([0-9]+)', line)
        if comment:
            pc = int(comment[1], 16)
            ordinal, ss, sp = map(int, comment.groups()[1:])
            if not 0 < pc < 0x100000 or not max(previous, pending[-1] if pending else 0) <= ordinal <= maximum or max(ss, sp) > 0xffff:
                raise ValueError('Invalid audio timer entry comment at line ' + str(number))
            pending.append(ordinal)
            continue
        tick = re.fullmatch(r'T ([0-9]+) ([012])', line)
        if not tick:
            raise ValueError('Invalid audio timer row at line ' + str(number))
        ordinal, mode = map(int, tick.groups())
        if not previous <= ordinal <= maximum or pending and ordinal < pending[-1]:
            raise ValueError('Audio timer ordinals decrease at line ' + str(number))
        previous = ordinal
        if pending:
            pending.pop()
        if ordinal < service_limit:
            rows.append(f'T {ordinal} {mode}\n')
    if not ended:
        raise ValueError('Audio timer capture has no E trailer')
    Path(destination).write_text(''.join(rows) + 'E\n', encoding='ascii')
    return len(rows)

