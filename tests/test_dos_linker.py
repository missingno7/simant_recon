"""Real period tools must resolve source CRT overrides without warning waivers."""
import copy
import json
from pathlib import Path
import re
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dos import build
from workspace import retire


class RuntimeDictionary(unittest.TestCase):
    def test_real_compiler_self_external_and_library_dictionary_control(self):
        scratch = ROOT / 'build/scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix='runtime-dictionary-', dir=scratch))
        previous_work = build.compiler.WORK
        source = '''void far * far malloc(unsigned n) { return (void far *)0; }
void far _ffree(char far *p) { }
void far free(void far *p) { _ffree(p); }
void main(void) { free((void far *)0); }
'''
        try:
            build.compiler.WORK = out / 'cc'
            result = build.compiler.compile_c(source, 'msc600ax',
                ['/AL', '/Oe', '/Og', '/Gs', '/Zi'], basename='OVERRIDE', keep=True)
            self.assertTrue(result.ok, result.log)
            obj = build.OmfReader().read(result.obj, 'override')
            self.assertIn('__ffree', obj.externals)
            self.assertIn('__ffree', [p['name'] for p in obj.publics])
            self.assertTrue(any(f.get('target') == '__ffree' and f.get('segment', '').endswith('_TEXT')
                                for f in obj.fixups), obj.fixups)
            object_path = out / 'OVERRIDE.OBJ'
            object_path.write_bytes(result.obj)
            program = json.loads((ROOT / 'src/program.json').read_text())
            lib = next(l for l in program['dos']['runtime_libraries'] if l['name'].upper() == 'LLIBCR.LIB')
            library_raw, library_pin = build.read_pin(lib['path'], lib['sha256'])
            report = {'inputs': [], 'translation_units': [
                {'unit': 'ROOT', 'basename': 'OVERRIDE', 'object': build.read_pin(object_path)[1]}],
                'runtime_components': [{**library_pin, 'name': lib['name']}], 'symbolic_aliases': []}
            positive = out / 'ordinary'
            positive.mkdir()
            build._link_program({}, positive, report, 'rtlink400')
            self.assertEqual(report['link']['status'], 'LINKED_NOT_EXECUTED', report['link'])
            mapping = (positive / 'link/SOURCE.MAP').read_text()
            log = (positive / 'link/LINK.LOG').read_text()
            self.assertNotIn('fmalloc.asm', log.lower())
            self.assertFalse(build.linker_diagnostics(log))
            addresses = {}
            for name in ('__ffree', '_free'):
                match = re.search(r'^\s*([0-9A-F]+):([0-9A-F]+)\s+.*?\b' +
                                  re.escape(name) + r'\s+.*?\bOVERRIDE\.C\s*$', mapping, re.M)
                self.assertIsNotNone(match, name)
                addresses[name] = int(match[1], 16) * 16 + int(match[2], 16)
            image = (positive / 'link/SOURCE.EXE').read_bytes()
            load = struct.unpack_from('<H', image, 8)[0] * 16
            wrapper = image[load + addresses['_free']:load + addresses['_free'] + 18]
            self.assertEqual(wrapper[9:11], b'\x0e\xe8')  # push CS; near call
            self.assertEqual(addresses['_free'] + 13 + struct.unpack_from('<h', wrapper, 11)[0],
                             addresses['__ffree'])

            # Only the documented dictionary option changes in this negative control.
            negative = out / 'extended'
            negative.mkdir()
            negative_report = copy.deepcopy(report)
            write_bytes = Path.write_bytes
            def extended_dictionary(path, raw):
                if path.name == 'SOURCE.LNK':
                    raw = raw.replace(b'NOEXTDICTIONARY\r\n', b'EXTDICTIONARY\r\n')
                return write_bytes(path, raw)
            with patch.object(Path, 'write_bytes', extended_dictionary):
                build._link_program({}, negative, negative_report, 'rtlink400')
            self.assertEqual(negative_report['link']['status'], 'FAILED')
            negative_log = (negative / 'link/LINK.LOG').read_text()
            self.assertIn("warning wrt0011: Public symbol '__ffree' doubly defined", negative_log)
            self.assertIn('fmalloc.asm', negative_log.lower())
            for trial in (positive, negative):
                self.assertEqual((trial / 'link/OVERRIDE.OBJ').read_bytes(), result.obj)
                self.assertEqual((trial / 'link/LLIBCR.LIB').read_bytes(), library_raw)
        finally:
            build.compiler.WORK = previous_work
            retire(out)


class OverlayVectors(unittest.TestCase):
    def test_inventory_preserves_recovered_symbolic_vector_targets(self):
        import exe
        import match
        program = json.loads((ROOT / 'src/program.json').read_text())
        targets = []
        for row in build.overlay_vectors(program):
            target = match.obj_name_lookup(row['symbol'])
            self.assertIsNotNone(target, row['symbol'])
            self.assertEqual(target['kind'], 'code')
            targets.append((target['unit'], target['seg'], target['off']))
        original = {(v.unit, v.target_seg, v.target_off) for v in exe.load().vectors}
        self.assertEqual(len(targets), len(set(targets)))
        self.assertEqual(set(targets), original)

    def test_selective_driver_pointer_and_both_entry_names(self):
        """An IRQ callback stays direct; canonical and alias entry calls still load."""
        scratch = ROOT / 'build/scratch'
        scratch.mkdir(parents=True, exist_ok=True)
        out = Path(tempfile.mkdtemp(prefix='overlay-vectors-', dir=scratch))
        previous_work = build.compiler.WORK
        try:
            build.compiler.WORK = out / 'cc'
            sources = {
                'ROOT': ('extern int far callback(void); extern int far entry(void); '
                         'extern int far oldentry(void); '
                         'int (far *driver)(void) = callback; '
                         'int far invoke(void) { return entry() + oldentry(); } '
                         'void main(void) { invoke(); }'),
                'DISPLAY': 'int far callback(void) { return 1; } int far entry(void) { return 2; }',
            }
            rows = []
            objects = {}
            for name, source in sources.items():
                result = build.compiler.compile_c(source, 'msc600ax',
                    ['/AL', '/Gs', '/Od'], basename=name, keep=True)
                self.assertTrue(result.ok, result.log)
                objects[name] = result.obj
                path = out / (name + '.OBJ')
                path.write_bytes(result.obj)
                rows.append({'key': name, 'unit': 'root' if name == 'ROOT' else 'S00',
                             'basename': name, 'object': build.read_pin(path)[1]})
            inventory = json.loads((ROOT / 'src/program.json').read_text())
            lib = next(l for l in inventory['dos']['runtime_libraries'] if l['name'].upper() == 'LLIBCR.LIB')
            library_raw, library_pin = build.read_pin(lib['path'], lib['sha256'])
            base = {'inputs': [], 'translation_units': rows,
                    'runtime_components': [{**library_pin, 'name': lib['name']}],
                    'symbolic_aliases': [{'alias': '_oldentry', 'target': '_entry',
                                         'offset': 0, 'referenced': True}]}
            policy = {'dos': {'overlay_vectors': {'policy': 'EXPLICIT_SYMBOLS',
                       'vectors': [{'symbol': '_entry', 'module': 'DISPLAY'}]}}}
            results = {}
            for mode in ('selective', 'automatic'):
                trial = out / mode
                trial.mkdir()
                report = copy.deepcopy(base)
                write_bytes = Path.write_bytes
                def automatic_vectors(path, raw):
                    if path.name == 'SOURCE.LNK':
                        raw = raw.replace(b'VECTOROFF\r\n', b'')
                    return write_bytes(path, raw)
                if mode == 'automatic':
                    with patch.object(Path, 'write_bytes', automatic_vectors):
                        build._link_program(policy, trial, report, 'rtlink400')
                    self.assertEqual(report['link']['status'], 'FAILED', report['link'])
                    self.assertEqual(report['link']['reason'], 'overlay vector policy mismatch')
                    self.assertEqual(report['link']['vectors']['unexpected'], ['_callback'])
                else:
                    build._link_program(policy, trial, report, 'rtlink400')
                    self.assertEqual(report['link']['status'], 'LINKED_NOT_EXECUTED', report['link'])
                mapping = (trial / 'link/SOURCE.MAP').read_text()
                image = (trial / 'link/SOURCE.EXE').read_bytes()
                header = struct.unpack_from('<H', image, 8)[0] * 16
                def address(name):
                    hit = re.search(r'^\s*([0-9A-F]+):([0-9A-F]+)\s+\S+\s+' +
                                    re.escape(name) + r'\s', mapping, re.M)
                    self.assertIsNotNone(hit, name)
                    return int(hit[1], 16), int(hit[2], 16)
                vectors = set(re.findall(r'\s(\S+)_@@@_RTLOVL_VECTOR\s', mapping))
                # RTLink 4 writes resident data after overlay records. Read its
                # documented info structure rather than treating data as MZ root.
                manager, info_offset = address('$$OVLINFO')
                info = header + manager * 16 + info_offset
                count = struct.unpack_from('<H', image, info + 12)[0]
                def data_at(seg, offset, size):
                    linear = seg * 16 + offset
                    for i in range(count):
                        desc = struct.unpack_from('<8H', image, info + 18 + i * 16)
                        start = desc[0] * 16
                        if start <= linear and linear + size <= start + desc[4] * 16:
                            record = (desc[2] + ((desc[3] & 255) << 16)) * 16
                            payload = record + ((desc[5] * 4 + 15) // 16) * 16
                            return image[payload + linear - start:payload + linear - start + size]
                    self.fail('symbol outside linked section')
                driver = struct.unpack('<HH', data_at(*address('_driver'), 4))
                invoke_seg, invoke_offset = address('_invoke')
                obj = build.OmfReader().read(objects['ROOT'])
                seen_entry_names = set()
                for fixup in obj.fixups:
                    if fixup.get('target') not in ('_entry', '_oldentry'):
                        continue
                    seen_entry_names.add(fixup['target'])
                    bound = struct.unpack_from('<HH', image,
                        header + invoke_seg * 16 + invoke_offset + fixup['offset'])
                    vector_seg, vector_off = address(fixup['target'] + '_@@@_RTLOVL_VECTOR')
                    self.assertEqual(bound, (vector_off, vector_seg))
                    vector = image[header + vector_seg * 16 + vector_off:
                                   header + vector_seg * 16 + vector_off + 10]
                    self.assertEqual(vector[3], 0xEA)
                    target_seg, target_off = address('_entry')
                    self.assertEqual(struct.unpack_from('<HH', vector, 4), (target_off, target_seg))
                self.assertEqual(seen_entry_names, {'_entry', '_oldentry'})
                results[mode] = (driver, vectors, address('_callback'), manager)
                for name, raw in objects.items():
                    self.assertEqual((trial / 'link' / (name + '.OBJ')).read_bytes(), raw)
                self.assertEqual((trial / 'link/LLIBCR.LIB').read_bytes(), library_raw)
            driver, vectors, callback, manager = results['selective']
            self.assertEqual(vectors, {'_entry', '_oldentry'})
            self.assertEqual(driver, (callback[1], callback[0]))
            self.assertNotEqual(driver[1], manager)
            driver, vectors, _, manager = results['automatic']
            self.assertIn('_callback', vectors)
            self.assertEqual(driver[1], manager)
        finally:
            build.compiler.WORK = previous_work
            retire(out)


if __name__ == '__main__':
    unittest.main()
