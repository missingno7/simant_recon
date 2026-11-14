"""Independent DOS ISR bindings and strict chronological replay prefixes."""
import json
import tempfile
import unittest
from pathlib import Path

from .audio_timer import ENTRIES, timer_binding, timer_tape
from .capture_dos_steps import capture_addresses
from .state_schema import ROOT, memory_base, sha


class TimerTapeControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name) / 'capture.timer'
        self.output = Path(self.tmp.name) / 'prefix.timer'

    def tape(self, text, limit=3):
        self.source.write_text(text, encoding='ascii')
        return timer_tape(self.source, self.output, limit)

    def test_prefix_keeps_equal_ordinal_order_and_excludes_limit(self):
        count = self.tape('# entry 30000 0 4096 16\nT 0 1\n'
                          'T 2 0\nT 2 1\nT 3 0\nT 9 1\nE\n')
        self.assertEqual(count, 3)
        self.assertEqual(self.output.read_text(), 'T 0 1\nT 2 0\nT 2 1\nE\n')

    def test_zero_limit_and_empty_capture(self):
        self.assertEqual(self.tape('T 0 0\nE\n', 0), 0)
        self.assertEqual(self.output.read_text(), 'E\n')
        self.assertEqual(self.tape('E\n'), 0)

    def test_nested_busy_rejection_retains_completion_order(self):
        count = self.tape('# entry 30000 0 4096 16\n'
                          '# entry 30000 1 4096 32\nT 1 2\nT 2 1\nE\n')
        self.assertEqual(count, 2)
        self.assertEqual(self.output.read_text(), 'T 1 2\nT 2 1\nE\n')

    def test_malformed_capture_never_writes_prefix(self):
        malformed = ('T 1 1\n', 'T 1 1\nE\nT 2 0\n', 'E 1\n',
                     'T 1 3\nE\n', 'T -1 0\nE\n', 'T 1 1 extra\nE\n',
                     'T 2 0\nT 1 1\nE\n', '# unknown\nE\n',
                     '# entry 0 0 1 1\nT 0 0\nE\n',
                     '# entry 30000 0 65536 1\nT 0 0\nE\n',
                     '# entry 30000 2 1 1\nT 1 0\nE\n',
                     '# entry 30000 2 1 1\nE\n',
                     '# entry 30000 2 1 1\n# entry 30000 2 1 1\nT 2 0\nE\n',
                     'T 18446744073709551616 1\nE\n',
                     'T 0 0\nT 9 3\nE\n')
        for text in malformed:
            with self.subTest(text=text):
                self.output.write_text('unchanged')
                with self.assertRaises(ValueError):
                    self.tape(text)
                self.assertEqual(self.output.read_text(), 'unchanged')

    def test_invalid_limit(self):
        for limit in (-1, True, 1.5, 1 << 64):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.tape('E\n', limit)


class TimerBindingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = {}
        for manifest in sorted((ROOT / 'build/reference/experiment').glob('*/manifest.json')):
            spec = json.loads(manifest.read_text())
            target = spec.get('target')
            if target not in ('original', 'canonical') or target in cls.frames:
                continue
            executable = ROOT / ('assets/SIMANT.EXE' if target == 'original'
                                 else 'build/current/dos/link/SOURCE.EXE')
            frame = manifest.parent / 'capture/exec-simstep.1.bin'
            if not executable.is_file() or not frame.is_file() or sha(executable) != spec.get('executable_sha256'):
                continue
            addresses = capture_addresses(target == 'original', executable)
            memory = frame.read_bytes()
            cls.frames[target] = memory, memory_base(memory, addresses), addresses

    def bound(self, target):
        if target not in self.frames:
            self.skipTest('No identity-matching ' + target + ' DOS frame available')
        memory, base, addresses = self.frames[target]
        return memory, base, addresses, timer_binding(memory, base, addresses)

    def check_binding(self, target):
        memory, base, addresses, bound = self.bound(target)
        self.assertEqual(bound['entries'], [(kind, base + addresses[name]) for kind, name in ENTRIES])
        self.assertEqual(len(bound['irets']), 4)
        self.assertEqual(len(bound['chains']), 2)
        self.assertEqual(bound['completions'], sorted(bound['irets'] + bound['chains']))
        for pc, raw in bound['instructions'].items():
            self.assertEqual(memory[pc:pc + len(raw) // 2].hex(), raw)

    def test_original_binding(self):
        self.check_binding('original')

    def test_canonical_binding(self):
        self.check_binding('canonical')

    def test_mutations_reject_named_entry_and_code_changes(self):
        if not self.frames:
            self.skipTest('No identity-matching DOS frame available')
        from capstone import Cs, CS_ARCH_X86, CS_MODE_16
        for target in self.frames:
            memory, base, addresses, bound = self.bound(target)
            for _, name in ENTRIES:
                with self.subTest(target=target, name=name):
                    shifted = dict(addresses)
                    shifted[name] += 1
                    with self.assertRaises(ValueError):
                        timer_binding(memory, base, shifted)
            decoder = Cs(CS_ARCH_X86, CS_MODE_16)
            start = base + addresses['snd_select_four_channel_timer']
            end = base + addresses['snd_select_two_channel_timer']
            selector = [ins for ins in decoder.disasm(memory[start:end], start)
                        if ins.mnemonic == 'mov' and ins.op_str.startswith('word ptr')][-1]
            start = base + addresses['snd_install_slow_timer_regs']
            slow = next(ins for ins in decoder.disasm(memory[start:end], start)
                        if ins.mnemonic == 'mov' and ins.op_str.startswith('dx, 0x'))
            mutations = {'entry_opcode': bound['entries'][0][1],
                         'shared_iret': bound['irets'][1],
                         'selector_offset': selector.address + selector.size - 1,
                         'slow_ivt_offset': slow.address + slow.size - 1}
            for kind, pc in mutations.items():
                with self.subTest(target=target, mutation=kind):
                    altered = bytearray(memory)
                    altered[pc] ^= 1
                    with self.assertRaises(ValueError):
                        timer_binding(altered, base, addresses)


if __name__ == '__main__':
    unittest.main()
