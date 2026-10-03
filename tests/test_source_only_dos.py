"""The standalone lane must expose debt and never import the hybrid oracle."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import csrc
import compiler
import dos_source_bindings as bindings
from omf import OmfReader
import source_only_dos as dos


class SourceOnlyDosTests(unittest.TestCase):
    def test_rtlink_alias_offsets_are_explicit_hexadecimal(self):
        self.assertEqual(bindings.rtlink_alias_delta(12), ' + 0Ch')
        self.assertEqual(bindings.rtlink_alias_delta(40), ' + 028h')
        self.assertEqual(bindings.rtlink_alias_delta(0), '')
        with self.assertRaises(ValueError):
            bindings.rtlink_alias_delta(-1)

    def test_oracle_read_guard_in_isolated_process(self):
        # The audit hook is intentionally permanent: isolate it from historical tests.
        program = (
            "import sys; from pathlib import Path; sys.path.insert(0,'tools'); "
            "import source_only_dos as d; denied=d.install_input_guard(); "
            "p=d.ROOT/'assets'/'SIMANT.EXE'; "
            "\ntry: p.read_bytes()\nexcept PermissionError: pass\n"
            "else: raise AssertionError('oracle read allowed')\n"
            "assert len(denied)==1\n"
        )
        run = subprocess.run([sys.executable, '-c', program], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_aliases_do_not_rewrite_literals_or_comments(self):
        source = '/* old_name */ char *s="old_name"; int old_name;'
        self.assertEqual(dos.rename_identifiers(source, {'old_name': 'new_name'}),
                         '/* old_name */ char *s="old_name"; int new_name;')

    def test_preparation_uses_registered_bodies_and_preserves_module_order(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            self.assertEqual(len(report['translation_units']), len(manifest['modules']) + 3)
            self.assertEqual(report['function_dispositions'], {
                'EXACT_C': 1244, 'GENUINE_ASM': 367, 'BEHAVIOR_EXACT_CONFIRMED': 29,
                'EXACT_AFTER_STATIC_AUDIT': 0, 'CONTRACT_EQUIVALENT': 0, 'UNRESOLVED': 0})
            self.assertEqual(report['historical_behavior_registrations'], 29)
            self.assertEqual(len(report['semantic_substitutions']), 29)
            aliases = dos.identifier_aliases(symbols)
            for row in report['translation_units']:
                original = (ROOT / row['source']['path']).read_text(encoding='latin1')
                generated = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                if row['lang'] == 'asm':
                    if not row.get('source_binding'):
                        self.assertEqual(generated, original)
                elif row['reviewed_bodies']:
                    names_before = [aliases.get(f.name, f.name) for f in csrc.Source(original).functions()]
                    names_after = [f.name for f in csrc.Source(generated).functions()]
                    self.assertEqual(names_before, names_after, row['module'])
                    self.assertNotIn('SCAFFOLD BEGIN', generated)
            # Live/unknown data dispositions must remain visible, never emitted as bytes.
            self.assertEqual(sum(r['size'] for r in report['unresolved_data']), 113)
            self.assertTrue(any(r['classification'] == 'UNKNOWN_FIELD_SEMANTICS'
                                for r in report['unresolved_data']))

    def test_stale_registered_source_rejected(self):
        with self.assertRaisesRegex(ValueError, 'stale source/evidence pin'):
            dos.pin(ROOT / 'README.md', '0' * 64)

    def test_strict_static_gate_rejects_missing_mapping_and_unexplained_semantics(self):
        registry = json.loads((ROOT / 'evidence/behavior/manifest.json').read_text())
        index = json.loads((ROOT / 'work/source-only-dos/static-completeness/index-v1.json').read_text())
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            directory = Path(directory)
            missing = {**index, 'entries': dict(index['entries'])}
            missing['entries'].pop('DrawBalloons')
            path = directory / 'index.json'
            path.write_text(json.dumps(missing))
            with self.assertRaisesRegex(ValueError, 'does not cover'):
                dos.strict_static_reviews(registry, {'inputs': []}, path)
            original = json.loads((ROOT / index['entries']['DrawBalloons']['path']).read_text())
            for change in ('missing_axis', 'semantic_gap', 'stale_source', 'false_exact', 'unreviewed_correction'):
                receipt = json.loads(json.dumps(original))
                if change == 'missing_axis':
                    receipt['root_review']['complete_cfg'] = False
                elif change == 'semantic_gap':
                    receipt['audit']['unexplained_semantic_differences'] = ['unknown write']
                elif change == 'stale_source':
                    receipt['audit']['source']['sha256'] = '0' * 64
                elif change == 'false_exact':
                    receipt['status'] = receipt['audit']['status'] = 'EXACT'
                else:
                    receipt['root_review']['source_correction_reviewed'] = False
                altered = directory / 'receipt.json'
                altered.write_text(json.dumps(receipt))
                updated = {**index, 'entries': {**index['entries'], 'DrawBalloons': dos.pin(altered)[1]}}
                path.write_text(json.dumps(updated))
                with self.assertRaises(ValueError, msg=change):
                    dos.strict_static_reviews(registry, {'inputs': []}, path)

    def test_contract_only_static_verdict_remains_a_link_blocker(self):
        registry = json.loads((ROOT / 'evidence/behavior/manifest.json').read_text())
        index = json.loads((ROOT / 'work/source-only-dos/static-completeness/index-v1.json').read_text())
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            directory = Path(directory)
            receipt = json.loads((ROOT / index['entries']['DrawBalloons']['path']).read_text())
            receipt['status'] = receipt['audit']['status'] = 'CONTRACT_EQUIVALENT'
            path = directory / 'receipt.json'
            path.write_text(json.dumps(receipt))
            index['entries']['DrawBalloons'] = dos.pin(path)[1]
            path = directory / 'index.json'
            path.write_text(json.dumps(index))
            report = {'inputs': [], 'errors': [], 'unresolved_data': [], 'translation_units': []}
            dos.strict_static_reviews(registry, report, path)
            self.assertEqual([r['function'] for r in report['unresolved_functions']], ['DrawBalloons'])
            dos.link_units(directory, report, 'rtlink400')
            self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])

    def test_reviewed_body_cannot_use_different_macro_or_type_context(self):
        original = '#define WIDTH 2\nstruct X { int a; };\nint f(int n) { return n; }'
        self.assertEqual(dos.reviewed_context(original, original, 'f')['status'], 'MATCH')
        for changed in (original.replace('WIDTH 2', 'WIDTH 4'),
                        original.replace('int a;', 'long a;'),
                        original.replace('int n)', 'long n)')):
            with self.assertRaises(ValueError):
                dos.reviewed_context(original, changed, 'f')

    def test_link_refuses_debt_before_launching_tool(self):
        report = {'errors': [], 'unresolved_functions': [], 'unresolved_data': [{'id': 'unknown'}],
                  'translation_units': []}
        dos.link_units(ROOT / 'build/workers/source_only_dos_tests/never-link', report, 'rtlink400')
        self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])

    def test_link_refuses_unknown_queue_layout_with_other_gates_clear(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'errors': [], 'unresolved_functions': [], 'unresolved_data': [],
                      'unresolved_symbols': [], 'duplicate_publics': {},
                      'translation_units': [], 'layout_dependencies': [
                          {'id': 'input-event-queue-fixed-pointer', 'status': 'UNRESOLVED'}]}
            dos.link_units(Path(directory), report, 'rtlink400')
            self.assertIn('independent link refused: incomplete source/data preflight', report['errors'])
            self.assertFalse((Path(directory) / 'link').exists())

    def test_binding_proof_rejects_wrong_frames_and_unrelated_instruction_changes(self):
        packet = json.loads((ROOT / 'work/source-only-dos/source-bindings-v1.json').read_text())
        binding = next(r for r in packet['bindings'] if r['module'] == 'S01:3126')
        module = json.loads((ROOT / 'layout/manifest.json').read_text())['modules'][binding['module']]
        canonical = dos.pin(ROOT / binding['source'], binding['source_sha256'])[0].decode('latin1')
        generated = bindings.apply_binding(canonical.replace('\r\n', '\n'), binding)
        def assemble(text):
            result = compiler.assemble(text, module['profile'], module['flags'], basename='CONTROL')
            self.assertTrue(result.ok, result.log)
            return OmfReader().read(result.obj)
        control = assemble(canonical)
        self.assertEqual(bindings.verify_objects(control, assemble(generated), binding)['status'], 'PASS')
        # These are separately assembled source contrasts, never patched objects.
        for contrast in (generated.replace('assume ss:DGROUP', 'assume ss:nothing'),
                         generated.replace('OFFSET DGROUP:_g_3DFC', 'OFFSET _g_3DFC'),
                         generated.replace('mov cx, 4000h', 'mov cx, 4001h')):
            self.assertTrue(contrast != generated, 'contrast did not change source')
            with self.assertRaises(ValueError):
                bindings.verify_objects(control, assemble(contrast), binding)

    def test_binding_proof_rejects_exporting_a_different_timer_word(self):
        packet = json.loads((ROOT / 'work/source-only-dos/source-bindings-v1.json').read_text())
        binding = next(r for r in packet['bindings'] if r['module'] == 'root:1B73')
        module = json.loads((ROOT / 'layout/manifest.json').read_text())['modules'][binding['module']]
        canonical = dos.pin(ROOT / binding['source'], binding['source_sha256'])[0].decode('latin1')
        generated = bindings.apply_binding(canonical.replace('\r\n', '\n'), binding)
        label = '_fd_1B73_0006 label word\n'
        contrast = generated.replace(label, '').replace('mickey_mode\tdb', label+'mickey_mode\tdb')
        def assemble(text):
            result = compiler.assemble(text, module['profile'], module['flags'], basename='TIMER')
            self.assertTrue(result.ok, result.log)
            return OmfReader().read(result.obj)
        control = assemble(canonical)
        self.assertEqual(bindings.verify_objects(control, assemble(generated), binding)['status'], 'PASS')
        with self.assertRaisesRegex(ValueError, 'exported wrong storage'):
            bindings.verify_objects(control, assemble(contrast), binding)

    def test_c_visibility_exports_preserve_full_reviewed_objects(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            for row in report['translation_units']:
                if row['lang'] != 'c' or not row.get('source_binding'):
                    continue
                if row['source_binding'].get('communals'):
                    continue
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def compile(text):
                    result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader().read(result.obj)
                control = compile(before)
                self.assertEqual(bindings.verify_objects(control, compile(after),
                    row['source_binding'])['status'], 'PASS')
                if row['module'] == 'S12:384C':
                    contrast = after.replace('int g_2996 = 0;', 'int g_2996 = 1;')
                    self.assertTrue(contrast != after)
                    with self.assertRaisesRegex(ValueError, 'outside reviewed address operands'):
                        bindings.verify_objects(control, compile(contrast), row['source_binding'])

    def test_history_communal_contract_rejects_wrong_extent_type_initialization_and_code(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'S24:39C7')
            before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control = compile(before)
            proof = bindings.verify_objects(control, compile(after), row['source_binding'])
            self.assertEqual(proof['status'], 'PASS')
            self.assertEqual(len(proof['added_communals']), 10)
            declaration = 'int far fd_50F6_0516[64];'
            for contrast in (after.replace(declaration, 'int far fd_50F6_0516[63];'),
                             after.replace(declaration, 'long far fd_50F6_0516[64];'),
                             after.replace(declaration, 'int far fd_50F6_0516[64] = {1};'),
                             after.replace('for (i = 0; i < 64; i++)', 'for (i = 0; i < 63; i++)')):
                self.assertNotEqual(after, contrast)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, compile(contrast), row['source_binding'])

    def test_history_storage_requires_matching_linker_and_msc_runtime(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [],
                      'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_history_startup_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_history_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

            wrong = json.loads(json.dumps(report))
            for case in wrong['history_storage_contract']['cases']:
                if case['case'] == 'crt_overlay_zero_communal':
                    case['startup'] = 'USE'
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_history_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_scalar_owners_preserve_complete_objects_and_reject_storage_guesses(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            manifest, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if (r.get('source_binding') or {}).get('scalar_storage')]
            self.assertEqual({r['module'] for r in rows}, {'S08:35F5', 'S22:39C7', 'root:0BE8', 'root:0AD9'})
            self.assertEqual(sum(len(r['source_binding']['communals']) for r in rows), 21)
            for row in rows:
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def compile(text):
                    result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                control = compile(before)
                binding = row['source_binding']
                self.assertEqual(bindings.verify_objects(control, compile(after), binding)['status'], 'PASS')
                owner = binding['communals'][0]['name'][1:]
                declaration = f'int far {owner};'
                for contrast in (after.replace(declaration, f'long far {owner};'),
                                 after.replace(declaration, f'int far {owner}[2];'),
                                 after.replace(declaration, f'int far {owner} = 1;')):
                    self.assertNotEqual(after, contrast)
                    result = compiler.compile_c(contrast, row['profile'], row['flags'], basename=row['basename'])
                    if result.ok:
                        with self.assertRaises(ValueError):
                            bindings.verify_objects(control, OmfReader(communals=True).read(result.obj), binding)
                    else:
                        self.assertIn('error', result.log.lower())
                wrong = json.loads(json.dumps(binding))
                wrong['communals'][0]['historical_address'][1] += 1
                with self.assertRaises(ValueError):
                    bindings.review_addresses(wrong, manifest['modules'][row['module']], symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_scalar_startup_contracts(report, profile, tc['linkers'][profile])
            for key in ('health_storage_contract', 'food_cycle_storage_contract',
                        'population_storage_contract', 'lion_storage_contract',
                        'init_sim_storage_contract', 'yellow_reset_storage_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_scalar_startup_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_scalar_startup_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_queue_owner_rejects_extent_initializer_pointer_and_other_field_changes(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:1FD2')
            before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control = compile(before)
            proof = bindings.verify_objects(control, compile(after), row['source_binding'])
            self.assertEqual(proof['status'], 'PASS')
            self.assertTrue(proof['live_segment_extents_unchanged'])
            self.assertEqual(proof['added_communals'], [{'name': '_input_queue', 'kind': 'near', 'length': 112}])
            for contrast in (after.replace('input_queue[7]', 'input_queue[6]'),
                             after.replace('input_queue[7];', 'input_queue[7] = {{1}};'),
                             after.replace('(struct Event near *)input_queue', '(struct Event near *)(input_queue + 1)'),
                             after.replace('int g_5FF0 = 7;', 'int g_5FF0 = 6;')):
                self.assertNotEqual(after, contrast)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, compile(contrast), row['source_binding'])
            wrong = json.loads(json.dumps(row['source_binding']))
            wrong['debug_contributions']['$$SYMBOLS']['generated'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'debug contribution or relocation'):
                bindings.verify_objects(control, compile(after), wrong)

    def test_queue_storage_requires_matching_runtime_and_frame_contrasts(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_queue_startup_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_queue_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['queue_storage_contract']['cases'] = [r for r in wrong['queue_storage_contract']['cases']
                                                       if r['case'] != 'data_segment_frame_contrast']
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_queue_startup_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])
    def test_data_aliases_require_existing_bounded_source_storage(self):
        source = ("_DATA segment word public 'DATA'\npublic _owner\n"
                  "db 30 dup (0)\n_owner db 8 dup (1)\n_DATA ends\nend\n")
        result = compiler.assemble(source, 'masm510', ['/Mx'], basename='ALIAS')
        self.assertTrue(result.ok, result.log)
        obj = OmfReader().read(result.obj)
        spec = {'alias': '_view', 'owner': '_owner', 'source': 'fixture.asm',
                'source_sha256': 'a'*64, 'segment': '_DATA', 'owner_offset': 30,
                'owner_size': 8, 'offset': 2, 'view_size': 2, 'source_anchor': 'fixture'}
        module = {'source': 'fixture.asm', 'source_sha256': 'a'*64,
                  'placements': {'_DATA': {'seg': 0x55B3, 'off': 100, 'size': 38}}}
        row = {'basename': 'ALIAS', 'module': 'fixture'}
        symbols = {'data': {'view': {'seg': 0x55B3, 'off': 132}}}
        self.assertEqual(bindings.bind_data_alias(spec, obj, row, module, symbols)['offset'], 2)
        for field, wrong in (('offset', 4), ('view_size', 7), ('owner', '_missing'),
                             ('source_sha256', 'b'*64), ('owner_offset', 32)):
            with self.assertRaises(ValueError):
                bindings.bind_data_alias({**spec, field: wrong}, obj, row, module, symbols)

    def test_callback_provider_requires_one_typed_object_and_bounded_registry_views(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'source-owned:driver-callback-table')
            text = (ROOT / row['source']['path']).read_text(encoding='ascii')
            def compile(text):
                result = compiler.compile_c(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            obj = compile(text)
            self.assertEqual(bindings.verify_provider(obj, row['storage_provider'])['status'], 'PASS')
            for contrast in (text.replace('[25]', '[24]'), text.replace('[25]', '[26]'),
                             text.replace('();', '() = {0};'), text + '\nvoid extra(void) {}\n'):
                with self.assertRaises(ValueError):
                    bindings.verify_provider(compile(contrast), row['storage_provider'])
            self.assertEqual(len(report['reviewed_communal_aliases']), 23)
            for spec in report['reviewed_communal_aliases']:
                self.assertEqual(bindings.bind_communal_alias(spec, obj, row, symbols)['offset'], spec['offset'])
            spec = report['reviewed_communal_aliases'][0]
            for field, value in (('offset', 100), ('offset', 2), ('view_size', 2),
                                 ('source_sha256', '0' * 64), ('owner', '_other')):
                with self.assertRaises(ValueError):
                    bindings.bind_communal_alias({**spec, field: value}, obj, row, symbols)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_callback_storage_contract(report, profile, tc['linkers'][profile])
            wrong = json.loads(json.dumps(report))
            wrong['callback_storage_contract']['cases'].pop(0)
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_callback_storage_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_assembly_frame_scope_changes_only_three_reviewed_fixups(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            row = next(r for r in report['translation_units'] if r['module'] == 'root:1B73')
            before = (ROOT / row['source']['path']).read_text(encoding='latin1')
            after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
            def assemble(text):
                result = compiler.assemble(text, row['profile'], row['flags'], basename=row['basename'])
                self.assertTrue(result.ok, result.log)
                return OmfReader(communals=True).read(result.obj)
            control = assemble(before)
            generated = assemble(after)
            self.assertEqual(len(bindings.verify_objects(control, generated, row['source_binding'])['reviewed_frame_corrections']), 3)
            for contrast in (after.replace('assume es:DGROUP', 'assume es:_DATA'),
                             after.replace('mov cx, word ptr es:_g_9122', 'mov cx, word ptr es:_g_9124')):
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, assemble(contrast), row['source_binding'])
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_assembly_frame_contract(report, profile, tc['linkers'][profile])
            report['assembly_frame_contract']['cases'] = [r for r in report['assembly_frame_contract']['cases']
                                                         if r['case'] != 'canonical_data_frame']
            with self.assertRaisesRegex(ValueError, 'shifted DGROUP contract'):
                bindings.require_assembly_frame_contract(report, 'rtlink400', tc['linkers']['rtlink400'])

    def test_typed_near_owners_reject_extent_type_initialization_and_runtime_gaps(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            _, symbols = dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in
                    ('source-owned:mouse-words', 'source-owned:memory-state')]
            self.assertEqual(sum(sum(c['length'] for c in r['storage_provider']['communals']) for r in rows), 22)
            for row in rows:
                text = (ROOT / row['source']['path']).read_text(encoding='ascii')
                provider = row['storage_provider']
                def compile(source):
                    result = compiler.compile_c(source, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                bindings.review_provider_source(text, provider, symbols)
                self.assertEqual(bindings.verify_provider(compile(text), provider)['status'], 'PASS')
                if row['module'] == 'source-owned:mouse-words':
                    contrasts = [text.replace('int near g_9122;', 'char near g_9122;'),
                                 text.replace('int near g_9120;', 'int near g_9120 = 1;')]
                    wrong_type = text.replace('int near g_9122;', 'unsigned near g_9122;')
                else:
                    contrasts = [text.replace('Block far * near g_91A4;', 'Block near * near g_91A4;'),
                                 text.replace('unsigned near g_91A0;', 'unsigned near g_91A0 = 1;')]
                    wrong_type = text.replace('unsigned near g_91A0;', 'int near g_91A0;')
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(wrong_type, provider, symbols)
                for contrast in contrasts + [text + '\nvoid extra(void) {}\n']:
                    with self.assertRaises(ValueError):
                        bindings.verify_provider(compile(contrast), provider)
                wrong = json.loads(json.dumps(symbols))
                name = provider['communals'][0]['name'][1:]
                wrong['data'][name]['off'] += 1
                with self.assertRaises(ValueError):
                    bindings.review_provider_source(text, provider, wrong)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_near_storage_contracts(report, profile, tc['linkers'][profile])
            for key in ('mouse_storage_contract', 'memory_storage_contract'):
                wrong = json.loads(json.dumps(report))
                wrong[key]['cases'].pop(0)
                with self.assertRaisesRegex(ValueError, 'startup contract'):
                    bindings.require_near_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])
            wrong = json.loads(json.dumps(report))
            wrong['runtime_components'][0]['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'startup contract'):
                bindings.require_near_storage_contracts(wrong, 'rtlink400', tc['linkers']['rtlink400'])

    def test_driver_ss_frames_preserve_whole_modules_and_require_exact_site_sets(self):
        worker = ROOT / 'build/workers/source_only_dos_tests'
        worker.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=worker) as directory:
            report = {'inputs': [], 'generated_files': [], 'translation_units': [], 'semantic_substitutions': []}
            dos.prepare(Path(directory), report)
            rows = [r for r in report['translation_units'] if r['module'] in bindings.DRIVER_SS_SITE_HASHES]
            self.assertEqual(sum(len(r['source_binding']['reframes']) for r in rows), 128)
            for row in rows:
                before = (ROOT / row['binding_control_source']['path']).read_text(encoding='latin1')
                after = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                def assemble(text):
                    result = compiler.assemble(text, row['profile'], row['flags'], basename=row['basename'])
                    self.assertTrue(result.ok, result.log)
                    return OmfReader(communals=True).read(result.obj)
                control, generated = assemble(before), assemble(after)
                proof = bindings.verify_objects(control, generated, row['source_binding'])
                self.assertEqual(len(proof['reviewed_frame_corrections']), len(row['source_binding']['reframes']))
                contrast = after.replace('assume ss:DGROUP', 'assume ss:_DATA', 1)
                self.assertNotEqual(contrast, after)
                with self.assertRaises(ValueError):
                    bindings.verify_objects(control, assemble(contrast), row['source_binding'])
                for change in ('remove', 'offset', 'target'):
                    wrong = json.loads(json.dumps(row['source_binding']))
                    if change == 'remove': wrong['reframes'].pop()
                    elif change == 'offset': wrong['reframes'][0]['offset'] += 1
                    else: wrong['reframes'][0]['target'] = '_g_9120'
                    with self.assertRaisesRegex(ValueError, 'location set'):
                        bindings.verify_objects(control, generated, wrong)
            tc = compiler.toolchain()
            for profile in ('rtlink400', 'rtlink610'):
                bindings.require_driver_ss_frame_contract(report, profile, tc['linkers'][profile])
            for change in ('case', 'site', 'runtime'):
                wrong = json.loads(json.dumps(report))
                if change == 'case': wrong['driver_ss_frame_contract']['runtime_fixture']['cases'].pop(0)
                elif change == 'site': wrong['driver_ss_frame_contract']['signed_site_tuples'][0][2] += 1
                else: wrong['runtime_components'][0]['sha256'] = '0' * 64
                with self.assertRaisesRegex(ValueError, 'shifted DGROUP contract'):
                    bindings.require_driver_ss_frame_contract(wrong, 'rtlink400', tc['linkers']['rtlink400'])


if __name__ == '__main__':
    unittest.main()
