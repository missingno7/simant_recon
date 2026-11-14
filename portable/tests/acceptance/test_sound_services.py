"""Independent function bindings, ID stream coverage and native alias controls."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from .sound_services import (ORDER_MARKER, services, service_manifest, sound_binding,
                             native_sound_include, native_sound_coverage, sound_tape, sound_entry_qualified)
from .capture_dos_steps import capture_addresses
from .state_schema import ROOT, memory_base, sha


class SoundTapeControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)
        self.source, self.order, self.destination = [self.out / name for name in ('sound', 'order', 'prefix')]

    def tape(self, ids, order, limit=None):
        self.source.write_bytes(bytes(ids))
        self.order.write_bytes(bytes(order))
        return sound_tape(self.source, self.order, self.destination, limit)

    def test_complete_marker_count_and_prefix_position(self):
        result = self.tape([1, 2, 1], [10, ORDER_MARKER, 11, ORDER_MARKER, ORDER_MARKER], 4)
        self.assertEqual(result['source_ids'], 3)
        self.assertEqual(result['ids'], [1, 2])
        self.assertEqual(self.destination.read_bytes(), b'\x01\x02')
        compact = sound_tape(self.source, self.order, service_limit=4, include_ids=False)
        self.assertNotIn('ids', compact)
        self.assertEqual((compact['prefix_ids'], compact['used_ids']), (2, [1, 2]))
        self.assertEqual(self.tape([], [], 0)['prefix_ids'], 0)

    def test_malformed_full_suffix_never_writes_prefix(self):
        for ids, order in [([1], []), ([], [ORDER_MARKER]), ([0], [ORDER_MARKER]),
                           ([1, 255], [ORDER_MARKER, ORDER_MARKER])]:
            with self.subTest(ids=ids, order=order):
                self.destination.write_bytes(b'unchanged')
                with self.assertRaises(ValueError):
                    self.tape(ids, order, 0)
                self.assertEqual(self.destination.read_bytes(), b'unchanged')
        for limit in (-1, True, 1.5, 2):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.tape([1], [ORDER_MARKER], limit)

    def test_stable_ids_native_aliases_and_observed_missing_entry(self):
        rows = services()
        self.assertEqual([row['id'] for row in rows], list(range(1, len(rows) + 1)))
        self.assertEqual([row['name'] for row in rows], sorted(row['name'] for row in rows))
        self.assertEqual(service_manifest()['order_marker'], ORDER_MARKER)
        include = native_sound_include()
        self.assertIn('__asm__("__real_snd_port_read_byte");', include)
        self.assertIn('__asm__("__real_snd_service_and_test_stopped");', include)
        absent = [row for row in rows if str(row.get('native_representation', '')).startswith('No standalone native function')]
        self.assertEqual(len(absent), 9)
        self.assertEqual(include.count('__attribute__((weak))'), len(absent))
        for row in rows:
            declaration = next(line for line in include.splitlines()
                               if line.startswith(f'extern void sound_addr_{row["id"]}('))
            self.assertEqual('__attribute__((weak))' in declaration, row in absent)
        self.assertIn('__asm__("__real_snd_expand_sample_resource");', include)
        self.assertIn('#define SOUND_SAMPLE_RESOURCE_ID 20', include)
        self.assertIn('SOUND_SERVICE(1, sound_addr_1)', include)
        names = {row.get('native_name') or row['name']: 100 + row['id'] for row in rows}
        victim = rows[0]
        names.pop(victim.get('native_name') or victim['name'])
        receipt = native_sound_coverage(names)
        self.assertEqual(receipt['missing_profile_entries'], [dict(id=victim['id'], name=victim['name'])])
        with self.assertRaises(ValueError):
            native_sound_coverage(names, [victim['id']])
        with self.assertRaises(ValueError):
            native_sound_coverage(names, [0])

    def test_census_rejects_duplicate_or_renumbered_services(self):
        path = self.out / 'census.json'
        row = services()[0]
        for rows in ([row, row], [dict(row, id=2)]):
            path.write_text(json.dumps(dict(services=rows)))
            with self.assertRaises(ValueError):
                services(path)

    def test_census_input_identity_is_checked_before_accepting_services(self):
        path = self.out / 'census.json'
        witness = self.out / 'canonical-input.c'
        witness.write_bytes(b'canonical source witness')
        path.write_text(json.dumps(dict(services=[services()[0]], inputs=[
            dict(path=witness.as_posix(), sha256=sha(witness))])))
        self.assertEqual(len(service_manifest(path)['services']), 1)
        witness.write_bytes(b'changed source witness')
        with self.assertRaisesRegex(ValueError, 'census input changed'):
            service_manifest(path)

    def test_live_sample_argument_qualifies_only_pcm_and_preserves_other_entries(self):
        sample = next(row for row in services() if row['name'] == 'snd_expand_sample_resource')
        identifier = sample['id']
        self.assertTrue(sound_entry_qualified(identifier, {'type': 5}))
        self.assertTrue(sound_entry_qualified(identifier, [None, None, 111, 5]))
        for value in (0, 1, 2, 4, 6, 18, 20, 22, 65535, -1):
            with self.subTest(type=value):
                self.assertFalse(sound_entry_qualified(identifier, {'type': value}))
        self.assertTrue(sound_entry_qualified(1))
        for args in (None, {}, {'type': True}, {'type': 65536}, {'type': -32769}):
            with self.subTest(args=args), self.assertRaises(ValueError):
                sound_entry_qualified(identifier, args)


class SoundBindingControls(unittest.TestCase):
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
            self.skipTest('No independently identity-matching ' + target + ' frame')
        memory, base, addresses = self.frames[target]
        return memory, base, addresses, sound_binding(memory, base, addresses, target=target)

    def test_original_and_canonical_bind_all_entries_independently(self):
        for target in ('original', 'canonical'):
            with self.subTest(target=target):
                memory, base, addresses, bound = self.bound(target)
                self.assertEqual(bound['entries'], [('s', base + addresses[row['name']], row['id'])
                                                     for row in services()])
                for row in bound['functions']:
                    self.assertEqual(sha_bytes(memory[base + row['start']:base + row['start'] + row['size']]),
                                     row['relocated_function_sha256'])
                if target == 'canonical':
                    self.assertGreater(sum(len(row['resolved_direct_calls']) for row in bound['functions']), 100)
                self.assertEqual(len(bound['guards']), 1)
                guard = bound['guards'][0]
                self.assertEqual((guard['id'], guard['entry_stack_offset'], guard['compare_bp_offset']), (20, 14, 16))
                self.assertEqual(guard['entry'], base + addresses['snd_expand_sample_resource'])

    def test_wrong_entry_and_changed_body_fail(self):
        for target in self.frames:
            memory, base, addresses, bound = self.bound(target)
            for name in ('snd_load_and_start_song', 'snd_control_interrupts_disable', 'snd_opl_write'):
                with self.subTest(target=target, name=name):
                    altered_addresses = dict(addresses)
                    altered_addresses[name] += 1
                    with self.assertRaises(ValueError):
                        sound_binding(memory, base, altered_addresses, target=target)
                    altered_memory = bytearray(memory)
                    altered_memory[base + addresses[name]] ^= 1
                    with self.assertRaises(ValueError):
                        sound_binding(altered_memory, base, addresses, target=target)


class NativeCoffAliasControls(unittest.TestCase):
    def test_profiled_lto_body_matches_strong_alias(self):
        gcc = Path('C:/msys64/mingw64/bin/gcc.exe')
        if not gcc.is_file():
            self.skipTest('Pinned MinGW compiler is unavailable')
        row = next(row for row in services() if row['name'] == 'snd_expand_sample_resource')
        identifier = row['id']
        declaration = next(line for line in native_sound_include().splitlines()
                           if line.startswith(f'extern void sound_addr_{identifier}('))
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            driver = out / 'driver.c'
            driver.write_text('''
extern int observer_finish(void);
static volatile int body_calls;
__attribute__((noinline)) void snd_expand_sample_resource(void) { ++body_calls; }
__attribute__((no_instrument_function)) int main(void) {
    snd_expand_sample_resource();
    return body_calls == 1 ? observer_finish() : 32;
}
''')
            driver_object = out / 'driver.o'

            def compile_command(command):
                run = subprocess.run(command, capture_output=True, text=True, timeout=30)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

            compile_command([str(gcc), '-std=c11', '-O2', '-flto', '-ffat-lto-objects', '-finstrument-functions',
                             '-c', str(driver), '-o', str(driver_object)])
            observations = {}
            for mode in ('strong', 'weak'):
                alias = declaration if mode == 'strong' else declaration.replace(
                    ';', ' __attribute__((weak));', 1)
                hook = out / (mode + '.c')
                hook.write_text('#include <stdint.h>\n#include <stdio.h>\n' + alias + '\n' + f'''
static const struct {{ void (*address)(void); unsigned id; }} services[] =
    {{ {{ sound_addr_{identifier}, {identifier} }}, {{ 0, 0 }} }};
static volatile unsigned service_index;
static unsigned entries, observed_id;
static void *observed_address;
void __cyg_profile_func_enter(void *function, void *caller) {{
    (void)caller; ++entries; observed_address = function;
    unsigned i = service_index;
    if (function == (void *)services[i].address) observed_id = services[i].id;
}}
void __cyg_profile_func_exit(void *function, void *caller) {{ (void)function; (void)caller; }}
int observer_finish(void) {{
    printf("%u %u %llu %llu\\n", entries, observed_id,
           (unsigned long long)(uintptr_t)services[service_index].address,
           (unsigned long long)(uintptr_t)observed_address);
    return entries == 1 && observed_id == {identifier} ? 0 : 31;
}}
''')
                hook_object = out / (mode + '.o')
                executable = out / (mode + '.exe')
                compile_command([str(gcc), '-std=c11', '-O2', '-fno-lto', '-c', str(hook),
                                 '-o', str(hook_object)])
                # Match the observer link: non-LTO aliases precede LTO game objects.
                compile_command([str(gcc), '-O2', '-fno-lto', '-static', '-Wl,--wrap=snd_expand_sample_resource',
                                 str(hook_object), str(driver_object),
                                 '-o', str(executable)])
                run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=10)
                values = tuple(map(int, run.stdout.split()))
                self.assertEqual(len(values), 4, run.stdout + run.stderr)
                observations[mode] = (run.returncode, values)
            status, (entries, observed_id, alias_address, actual_address) = observations['strong']
            self.assertEqual((status, entries, observed_id), (0, 1, identifier), observations)
            self.assertGreater(actual_address, 0)
            self.assertEqual(alias_address, actual_address, observations)
            status, (entries, observed_id, alias_address, actual_address) = observations['weak']
            self.assertEqual(entries, 1, observations)
            self.assertGreater(actual_address, 0, observations)
            if alias_address != actual_address:
                self.assertEqual((status, observed_id), (31, 0), observations)
            else:
                # This toolchain can resolve the weak alias too; its behavior
                # is a diagnostic, not a required negative-control failure.
                self.assertEqual((status, observed_id), (0, identifier), observations)



def sha_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    unittest.main()
