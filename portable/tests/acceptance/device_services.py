"""Timing-dependent device queries at their source-function return boundary.

h is the serviced MIDI completion answer; j is a byte read from a sound port
(DSP/MPU busy, acknowledgement, or probe status). No game state is a provider.
"""
SERVICES = {'h': ('snd_service_and_test_stopped', 0xffff),
            'j': ('snd_port_read_byte', 0xff)}


def return_points(memory, address):
    """Reachable instruction CFG from this executable's independently named entry."""
    from capstone import Cs, CS_ARCH_X86, CS_MODE_16, CS_GRP_JUMP, CS_GRP_RET
    from capstone.x86 import X86_OP_IMM
    decoder = Cs(CS_ARCH_X86, CS_MODE_16); decoder.detail = True
    pending = [address]; seen = {}; returns = []
    while pending:
        pc = pending.pop()
        if pc in seen: continue
        if not address <= pc < address + 1024:
            raise ValueError('Device query CFG escapes its bounded function')
        ins = next(decoder.disasm(memory[pc:pc+15], pc, count=1), None)
        if ins is None: raise ValueError('Invalid device-query instruction')
        seen[pc] = bytes(ins.bytes).hex()
        if ins.group(CS_GRP_RET):
            if ins.mnemonic != 'retf': raise ValueError('Device query must return far')
            returns.append(pc); continue
        if ins.group(CS_GRP_JUMP):
            if not ins.operands or ins.operands[0].type != X86_OP_IMM:
                raise ValueError('Indirect device-query branch')
            pending.append(ins.operands[0].imm)
            if ins.mnemonic == 'jmp': continue
        pending.append(pc + ins.size)
    if not returns: raise ValueError('Missing device query RETF')
    return sorted(returns), dict(sorted(seen.items()))
