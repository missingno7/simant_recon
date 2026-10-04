"""SOURCE_ONLY_DOS: source preparation, period compilation and fail-closed audit.

No hybrid collection, original-image loader, binary stubs or object rewriting.
The original game image is inaccessible to this process, including through aliases.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import compiler
import csrc
import dos_source_bindings
import dos_alignment_debt
from omf import OmfReader

PAUSED_COMMIT = 'c850830006e0b7d456bb500bf101dd432bbe8ee3'
ORIGINAL_SHA = 'aa0596c6766322a8229ee3c36e57048c92adc82d50fbe2ef37afb8b85fcf4f11'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def install_input_guard():
    """Deny oracle paths before opening; check renamed full-image copies too."""
    denied = []
    def audit(event, args):
        if event != 'open' or not isinstance(args[0], (str, bytes, os.PathLike)):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        mode = args[1]
        if isinstance(mode, str) and all(x not in mode for x in ('r', '+')):
            return
        # Assets are runtime/oracle inputs, never compiler/linker inputs.
        if (ROOT / 'assets') in path.parents or path.name.lower() in {
                'simant.exe', 'simanth.exe', 'simant.hybrid.exe'}:
            denied.append(str(path))
            raise PermissionError(f'SOURCE_ONLY_DOS forbids oracle input: {path}')
    sys.addaudithook(audit)
    return denied


def pin(path, expected=None):
    raw = path.read_bytes()
    digest = sha(raw)
    if expected is not None and digest != expected:
        raise ValueError(f'stale source/evidence pin: {path}')
    if digest == ORIGINAL_SHA:
        raise ValueError(f'original executable under another name: {path}')
    return raw, {'path': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                 'sha256': digest, 'size': len(raw)}


def identifier_aliases(symbols):
    aliases = {}
    for table in ('code', 'data'):
        for name, row in symbols[table].items():
            if row.get('alias_of'):
                aliases[name] = row['alias_of']
            for history in row.get('history', []):
                if history.get('was'):
                    aliases[history['was']] = row.get('alias_of', name)
    return aliases


def rename_identifiers(text, aliases):
    # Token spans protect strings, comments, preprocessor text and inline ASM.
    edits = [(t.s, t.e, aliases[t.text]) for t in csrc.tokenize(text)
             if t.kind == 'id' and t.text in aliases and aliases[t.text] != t.text]
    for lo, hi, replacement in reversed(edits):
        text = text[:lo] + replacement + text[hi:]
    return text


def reviewed_context(canonical, reviewed, name):
    """A pinned body is usable only in its pinned DOS type/macro/parameter context."""
    def normalized(text):
        return ' '.join(t.text for t in csrc.tokenize(text) if t.kind not in ('ws', 'nl', 'cmt'))
    a, b = csrc.Source(canonical).function(name), csrc.Source(reviewed).function(name)
    parameters_a = [normalized(t) for t, _ in a.params]
    parameters_b = [normalized(t) for t, _ in b.params]
    return_a = normalized(canonical[a.head_s:a.params_s])
    return_b = normalized(reviewed[b.head_s:b.params_s])
    if parameters_a != parameters_b or return_a != return_b:
        raise ValueError(f'reviewed DOS function signature context differs: {name}')
    pattern = r'(?:typedef\s+)?(?:struct|union)\s+(?:\w+\s*)?\{[^{}]*\}[^;]*;'
    types_a = [normalized(t) for t in re.findall(pattern, canonical)]
    types_b = [normalized(t) for t in re.findall(pattern, reviewed)]
    if types_a != types_b:
        raise ValueError(f'reviewed DOS aggregate type context differs: {name}')
    def macros(text):
        return [' '.join(t.text.split()) for t in csrc.tokenize(text)
                if t.kind == 'pp' and re.match(r'\s*#\s*define\b', t.text)]
    macros_a, macros_b = macros(canonical), macros(reviewed)
    if macros_a != macros_b:
        raise ValueError(f'reviewed DOS macro context differs: {name}')
    return {'signature': return_a, 'parameter_types': parameters_a,
            'aggregate_types_sha256': sha(json.dumps(types_a).encode()),
            'macros_sha256': sha(json.dumps(macros_a).encode()), 'status': 'MATCH'}


def strict_static_reviews(registry, report, index_path=None):
    """A historical finite registration cannot silently close static semantics."""
    index_path = index_path or ROOT / 'work/source-only-dos/static-completeness/index-v1.json'
    raw, identity = pin(index_path)
    index = json.loads(raw)
    if (index.get('schema') != 'simant-dos-strict-static-index-v1'
            or set(index.get('entries', {})) != set(registry['entries'])):
        raise ValueError('strict static audit does not cover the behavioral registry')
    report['inputs'].append(identity)
    reviews = {}
    for name, entry in registry['entries'].items():
        item = index['entries'][name]
        raw, receipt_pin = pin(ROOT / item['path'], item['sha256'])
        receipt = json.loads(raw)
        evidence_raw, evidence_pin = pin(ROOT / entry['evidence_path'], entry['evidence_sha256'])
        original_source = json.loads(evidence_raw)['source']
        audit = receipt.get('audit', {})
        review = receipt.get('root_review', {})
        status = receipt.get('status')
        if (receipt.get('schema') != 'simant-dos-strict-static-review-v1'
                or receipt.get('function') != name or review.get('reviewer') != 'root'
                or receipt.get('registered_evidence', {}).get('sha256') != evidence_pin['sha256']
                or receipt.get('registered_source', {}).get('sha256') != original_source['sha256']
                or status not in ('BEHAVIOR_EXACT_CONFIRMED', 'EXACT', 'CONTRACT_EQUIVALENT', 'UNRESOLVED')
                or audit.get('status') != status):
            raise ValueError('invalid strict static audit identity/verdict: ' + name)
        if status in ('BEHAVIOR_EXACT_CONFIRMED', 'EXACT'):
            if (audit.get('unexplained_semantic_differences') != []
                    or not all(review.get(axis) is True for axis in
                        ('complete_cfg', 'complete_data_widths', 'complete_calls_effects', 'codegen_only_residue'))):
                raise ValueError('incomplete strict static acceptance: ' + name)
            if status == 'EXACT' and not review.get('byte_exact_verified'):
                raise ValueError('static semantics alone cannot claim EXACT: ' + name)
        source = receipt.get('source_override', original_source)
        if source.get('module') != original_source.get('module'):
            raise ValueError('strict source override changes the module: ' + name)
        if receipt.get('source_override') and review.get('source_correction_reviewed') is not True:
            raise ValueError('unreviewed strict source correction: ' + name)
        pin(ROOT / source['path'], source['sha256'])
        if audit.get('source', {}).get('sha256') != source['sha256']:
            raise ValueError('strict audit does not describe the imported source: ' + name)
        report['inputs'].append(receipt_pin)
        reviews[name] = {'status': status, 'receipt': receipt_pin,
                         'source_override': receipt.get('source_override'), 'root_review': review}
    report['strict_static_audit'] = reviews
    report['unresolved_semantics'] = [{'function': name, 'kind': 'semantic', 'status': r['status'],
                                      'receipt': r['receipt']}
                                     for name, r in reviews.items()
                                     if r['status'] not in ('BEHAVIOR_EXACT_CONFIRMED', 'EXACT')]
    report['unresolved_functions'] = list(report['unresolved_semantics'])
    return reviews


def prepare(out, report):
    manifest_raw, manifest_pin = pin(ROOT / 'layout/manifest.json')
    manifest = json.loads(manifest_raw)
    registry_raw, registry_pin = pin(ROOT / 'evidence/behavior/manifest.json')
    registry = json.loads(registry_raw)
    static_reviews = strict_static_reviews(registry, report)
    symbols_raw, symbols_pin = pin(ROOT / 'layout/symbols.json')
    symbols = json.loads(symbols_raw)
    aliases = identifier_aliases(symbols)
    report['inputs'] += [manifest_pin, registry_pin, symbols_pin]
    raw, identity = pin(ROOT / 'work/source-only-dos/far-data-paragraph-fill-contract-v1.json')
    alignment = json.loads(raw)
    dos_alignment_debt.require_contract(alignment)
    for item in (alignment['inputs'] + alignment['pinned_tool_inputs'] + alignment['runtime_artifacts']
                 + [alignment['research_receipt'], alignment['root_admission']]):
        path = Path(item['path'])
        report['inputs'].append(pin(path if path.is_absolute() else ROOT / path, item['sha256'])[1])
    report['inputs'].append(identity)
    report['far_data_alignment_contract'] = alignment
    raw, identity = pin(ROOT / 'work/source-only-dos/clip-pointer-data-disposition-v22.json')
    disposition = json.loads(raw)
    if disposition.get('root_reviewed') is not True or disposition.get('historical_data_debt_modified') is not False:
        raise ValueError('unreviewed functional clip-pointer data disposition')
    report['inputs'].append(identity)
    for item in disposition['review_inputs']:
        report['inputs'].append(pin(ROOT / item['path'], item['sha256'])[1])
    report['clip_pointer_data_disposition'] = disposition
    bindings = {}
    binding_origins = {}
    providers = []
    report['reviewed_data_aliases'] = []
    report['reviewed_communal_aliases'] = []
    for filename in ('source-bindings-v1.json', 'c-data-bindings-v1.json', 'history-storage-bindings-v1.json',
                     'queue-storage-bindings-v1.json', 'assembly-frame-bindings-v1.json',
                     'world-scalar-bindings-v1.json', 'population-owner-bindings-v1.json',
                     'lion-owner-bindings-v1.json', 'callback-table-bindings-v1.json',
                     'init-sim-scalar-bindings-v1.json', 'yellow-scalar-bindings-v1.json',
                     'driver-ss-frame-bindings-v1.json', 'near-state-bindings-v1.json',
                     'pattern-bank-bindings-v1.json', 'render-scalar-bindings-v1.json',
                     'memory-far-storage-bindings-v1.json', 'water-storage-bindings-v1.json',
                     'driver-local-frame-bindings-v1.json', 'mono-pattern-prefix-bindings-v1.json',
                     'clip-pointer-bindings-v1.json', 'yard-scalar-bindings-v1.json',
                     'database-index-state-bindings-v1.json', 'spider-counter-bindings-v1.json',
                     'lion-array-storage-bindings-v1.json', 'dgroup-rect-frame-bindings-v1.json',
                     'mouse-code-offset-frame-bindings-v1.json',
                     'spider-control-storage-bindings-v1.json', 'point-state-bindings-v1.json',
                     'database-record-state-bindings-v1.json',
                     'graphics-formula-bindings-v1.json', 'g2108-color-translation-bindings-v1.json',
                     'driver-indexed-address-bindings-v1.json',
                     'ant-list-counts-bindings-v1.json',
                     'colony-simulation-words-bindings-v1.json',
                     'player-locations-bindings-v1.json',
                     'ant-counters-timer-bindings-v1.json',
                     'language-string-list-pointers-bindings-v1.json',
                     'dead-ant-coordinate-rings-bindings-v1.json',
                     'ant-player-state-words-bindings-v1.json',
                     'display-mode-selector-bindings-v1.json',
                     'ant-ui-control-state-bindings-v1.json',
                     'ui-resource-scalars-bindings-v1.json',
                     'terrain-state-words-bindings-v1.json',
                     'swarm-serialized-buffers-bindings-v1.json',
                     'population-work-arrays-bindings-v1.json',
                     'saved-sound-state-bindings-v1.json',
                     'control-flag-words-bindings-v1.json',
                     'count-ants-transition-word-bindings-v1.json',
                     'sound-control-words-bindings-v1.json',
                     'sound-record-arrays-bindings-v1.json',
                     'ant-movement-words-bindings-v1.json',
                     'world-output-state-bindings-v1.json',
                     'history-scalar-state-bindings-v1.json',
                     'ant-class-histogram-bindings-v1.json',
                     'event-records-bindings-v1.json',
                     'remaining-preparestrings-string-pointers-bindings-v1.json',
                     'yard-init-state-bindings-v1.json',
                     'yard-animation-arrays-bindings-v1.json',
                     'balloon-deadline-timers-bindings-v1.json',
                     'experiment-anchor-bindings-v1.json',
                     'window-clip-handles-bindings-v1.json',
                     'remaining-history-words-bindings-v1.json',
                     'mode-population-vectors-bindings-v1.json',
                     'floor-task-words-bindings-v1.json',
                     'ui-geometry-state-bindings-v1.json',
                     'remaining-world-state-bindings-v1.json',
                     'remaining-ant-state-bindings-v1.json',
                     'remaining-ui-state-bindings-v1.json',
                     'remaining-window-state-bindings-v1.json',
                     'remaining-scalar-tail-bindings-v1.json',
                     'balloon-buffer-tables-bindings-v1.json',
                     'render-delay-word-bindings-v1.json',
                     'window-ralloc-handles-bindings-v1.json',
                     'remaining-sound-storage-bindings-v1.json',
                     'remaining-misc-storage-bindings-v1.json',
                     's01-pattern-4220-bindings-v1.json'):
        binding_raw, binding_pin = pin(ROOT / 'work/source-only-dos' / filename)
        binding_packet = json.loads(binding_raw)
        if binding_packet['category'] not in ('REVIEWED_SOURCE_LINK_BINDING', 'REVIEWED_SOURCE_STORAGE_BINDING'):
            raise ValueError('unreviewed DOS source bindings')
        report['inputs'].append(binding_pin)
        for review_source in binding_packet.get('review_sources', []):
            report['inputs'].append(pin(ROOT / review_source['path'], review_source['sha256'])[1])
        if binding_packet.get('runtime_contract'):
            contract_pin = binding_packet['runtime_contract']
            raw, identity = pin(ROOT / contract_pin['path'], contract_pin['sha256'])
            contract = json.loads(raw)
            if not contract['all_required_checks_pass']:
                raise ValueError('storage runtime contract is not verified')
            script = contract['probe_source']
            report['inputs'] += [identity, pin(ROOT / script['path'], script['sha256'])[1]]
            report[binding_packet.get('runtime_contract_key', 'history_storage_contract')] = contract
        for contract_key, contract_pin in binding_packet.get('runtime_contracts', {}).items():
            raw, identity = pin(ROOT / contract_pin['path'], contract_pin['sha256'])
            contract = json.loads(raw)
            if not contract['all_required_checks_pass']:
                raise ValueError('scalar runtime contract is not verified')
            script = contract['probe_source']
            report['inputs'] += [identity, pin(ROOT / script['path'], script['sha256'])[1]]
            report[contract_key] = contract
        for binding in binding_packet['bindings']:
            if binding['module'] in bindings:
                previous = bindings[binding['module']]
                base = binding_packet.get('extends_packet')
                scalar_extension = (binding['module'] == 'S08:35F5'
                                    and binding.get('scalar_storage') == {'families': ['init_sim']}
                                    and previous.get('scalar_storage') == {'families': ['health', 'food_cycle']})
                pattern_extension = (binding['module'] == 'S00:31AD'
                                     and binding.get('pattern_bank_operands') is True)
                water_extension = (binding['module'] == 'root:0BE8'
                                   and binding.get('array_storage') == {'families': ['water_drop']}
                                   and previous.get('scalar_storage') == {'families': ['population']})
                local_extension = (binding['module'] in dos_source_bindings.LOCAL_SS_SITES
                                   and bool(binding.get('local_reframes')))
                segment_extension = (binding['module'] == 'root:1B73'
                                     and bool(binding.get('segment_corrections')))
                code_offset_extension = (binding['module'] == 'root:1B73'
                                         and bool(binding.get('code_offset_reframes')))
                indexed_extension = (binding['module'] in dos_source_bindings.INDEXED_OPERANDS
                                     and binding.get('indexed_address_operands') is True)
                s01_view_extension = (binding['module'] == 'S01:3126'
                                      and binding.get('s01_pattern_view_operands') is True)
                if pattern_extension or local_extension or segment_extension or code_offset_extension or indexed_extension or s01_view_extension:
                    # This third layer extends the effective binding, including the
                    # previously admitted frames. Pin its complete provenance and
                    # content rather than silently replacing either frozen packet.
                    chain = binding.get('extends_packets', binding_packet.get('extends_packets', []))
                    if [p['path'].replace('\\', '/') for p in chain] != binding_origins[binding['module']]:
                        raise ValueError('DOS layout extension has a different binding chain')
                    for parent in chain:
                        report['inputs'].append(pin(ROOT / parent['path'], parent['sha256'])[1])
                    digest = hashlib.sha256(json.dumps(previous, sort_keys=True,
                        separators=(',', ':')).encode()).hexdigest()
                    if digest != binding.get('extends_effective_binding_sha256'):
                        raise ValueError('DOS layout extension has a different effective control binding')
                elif not base or not (binding.get('reframes') or scalar_extension or water_extension):
                    raise ValueError('duplicate DOS binding module')
                if not (pattern_extension or local_extension or segment_extension or code_offset_extension or indexed_extension or s01_view_extension):
                    base_raw, base_pin = pin(ROOT / base['path'], base['sha256'])
                    if previous not in json.loads(base_raw)['bindings']:
                        raise ValueError('DOS frame extension has a different source/control binding')
                    report['inputs'].append(base_pin)
                if any(binding[k] != previous[k] for k in ('module', 'source', 'source_sha256')):
                    raise ValueError('DOS frame extension has a different source/control binding')
                combined = dict(previous)
                keys = ('edits', 'exports', 'relocations', 'reframes', 'communals')
                if 'local_reframes' in previous or 'local_reframes' in binding:
                    keys += ('local_reframes',)
                if 'segment_corrections' in previous or 'segment_corrections' in binding:
                    keys += ('segment_corrections',)
                if 'code_offset_reframes' in previous or 'code_offset_reframes' in binding:
                    keys += ('code_offset_reframes',)
                for key in keys:
                    combined[key] = previous.get(key, []) + binding.get(key, [])
                if scalar_extension:
                    combined['scalar_storage'] = {'families': previous['scalar_storage']['families'] + ['init_sim']}
                if binding.get('reframes'):
                    combined['frame_review'] = binding['frame_review']
                if pattern_extension:
                    combined['pattern_bank_operands'] = True
                if water_extension:
                    combined['array_storage'] = binding['array_storage']
                if indexed_extension:
                    combined['indexed_address_operands'] = True
                if s01_view_extension:
                    combined['s01_pattern_view_operands'] = True
                    combined['s01_pattern_view_owner'] = binding['s01_pattern_view_owner']
                binding = combined
            bindings[binding['module']] = binding
            binding_origins.setdefault(binding['module'], []).append(binding_pin['path'].replace('\\', '/'))
        report['reviewed_data_aliases'] += binding_packet.get('aliases', [])
        report['reviewed_communal_aliases'] += binding_packet.get('communal_aliases', [])
        providers += binding_packet.get('providers', [])
    contract_raw, contract_pin = pin(ROOT / 'work/source-only-dos/linker-alias-contract-v2.json')
    contract = json.loads(contract_raw)
    if not contract['all_checks_pass'] or len(contract['cases']) != 10:
        raise ValueError('linker interior alias contract not verified')
    _, probe_pin = pin(ROOT / contract['probe_source']['path'], contract['probe_source']['sha256'])
    report['inputs'] += [contract_pin, probe_pin]
    report['linker_alias_contract'] = contract
    replacements = {}
    for name, entry in registry['entries'].items():
        if entry['status'] != 'BEHAVIOR_EXACT':
            raise ValueError(f'unreviewed behavioral entry: {name}')
        evidence_raw, evidence_pin = pin(ROOT / entry['evidence_path'], entry['evidence_sha256'])
        packet = json.loads(evidence_raw)
        source = static_reviews[name]['source_override'] or packet['source']
        source_raw, source_pin = pin(ROOT / source['path'], source['sha256'])
        text = rename_identifiers(source_raw.decode('latin1'), aliases)
        actual_name = aliases.get(name, name)
        fn = csrc.Source(text).function(actual_name)
        # The canonical TU owns declarations/data. Only the reviewed definition is imported.
        definition = text[fn.head_s:fn.e]
        unit_key = source['module']
        if unit_key not in manifest['modules']:
            candidates = [k for k in manifest['modules'] if k.startswith(unit_key + ':')]
            if len(candidates) != 1:
                raise ValueError(f'ambiguous behavioral module: {unit_key}')
            unit_key = candidates[0]
        replacements.setdefault(unit_key, {})[actual_name] = (definition, text, source_pin, evidence_pin)
        report['semantic_substitutions'].append({
            'function': actual_name, 'module': unit_key, 'category': static_reviews[name]['status'],
            'source': source_pin, 'evidence': evidence_pin,
            'strict_status': static_reviews[name]['status'],
            'static_receipt': static_reviews[name]['receipt'],
            'scope': 'reviewed definition only; canonical TU declarations/data retained'})
        report['inputs'] += [source_pin, evidence_pin]
    source_dir = out / 'sources'
    source_dir.mkdir(parents=True, exist_ok=True)
    for number, (key, module) in enumerate(sorted(manifest['modules'].items())):
        raw, source_pin = pin(ROOT / module['source'], module['source_sha256'])
        report['inputs'].append(source_pin)
        text = raw.decode('latin1')
        binding = bindings.get(key)
        imported = replacements.get(key, {})
        if imported:
            text = rename_identifiers(text, aliases)
        for name, (definition, reviewed_module, _, _) in imported.items():
            context_check = reviewed_context(text, reviewed_module, name)
            fn = csrc.Source(text).function(name)
            # Restore reviewed extern context when the accepted partial file lacked it.
            # These are source declarations, never synthesized definitions/initializers.
            declarations = []
            for match in re.finditer(r'(?m)^extern\s+[^;]+;', reviewed_module):
                declaration = match.group()
                names = re.findall(r'\b([A-Za-z_]\w*)\s*(?=\[|\(|;)', declaration)
                if names and not any(re.search(r'\b' + re.escape(n) + r'\b', text[:fn.head_s]) for n in names):
                    declarations.append(declaration)
            context = '\n'.join(declarations) + '\n' if declarations else ''
            text = text[:fn.head_s] + context + definition + text[fn.e:]
            report['semantic_substitutions'][next(i for i, r in enumerate(report['semantic_substitutions'])
                                                  if r['function'] == name)]['restored_extern_declarations'] = declarations
            report['semantic_substitutions'][next(i for i, r in enumerate(report['semantic_substitutions'])
                                                  if r['function'] == name)]['dos_context_check'] = context_check
        # Remove only markers for imported reviewed bodies; an unreviewed scaffold is fatal.
        for name in module.get('scaffold', []):
            if name not in imported:
                raise ValueError(f'unreviewed scaffold: {key}/{name}')
        if module.get('lang') != 'asm':
            text = re.sub(r'/\*\s*SCAFFOLD BEGIN.*?\*/|/\*\s*SCAFFOLD END\s*\*/', '', text, flags=re.S)
        suffix = '.asm' if module.get('lang') == 'asm' else '.c'
        basename = f'U{number:03d}'
        control_pin = None
        if binding:
            if (module['source'] != binding['source']
                    or source_pin['sha256'] != binding['source_sha256']):
                raise ValueError('DOS binding canonical source changed: ' + key)
            dos_source_bindings.review_addresses(binding, module, symbols)
            # C controls include exactly the same reviewed body substitutions.
            # A visibility change is compared after semantic closure, not against
            # the historical partial TU's unclaimed candidate bodies.
            if suffix == '.c':
                control_dir = out / 'binding-controls'
                control_dir.mkdir(exist_ok=True)
                control = control_dir / (basename + suffix)
                control.write_bytes(text.encode('latin1'))
                control_pin = pin(control)[1]
                report['generated_files'].append(control_pin)
            else:
                control_pin = source_pin
            text = dos_source_bindings.apply_binding(text.replace('\r\n', '\n'), binding)
        path = source_dir / (basename + suffix)
        path.write_bytes(text.encode('latin1'))
        generated_pin = pin(path)[1]
        report['generated_files'].append(generated_pin)
        report['translation_units'].append({
            'module': key, 'unit': module['unit'], 'basename': basename,
            'source': source_pin, 'generated_source': generated_pin,
            'lang': module.get('lang', 'c'), 'profile': module['profile'], 'flags': module['flags'],
            'reviewed_bodies': sorted(imported), 'source_binding': binding,
            'binding_control_source': control_pin, 'status': 'PREPARED'})
    for provider in providers:
        source = provider['source']
        raw, source_pin = pin(ROOT / source['path'], source['sha256'])
        text = raw.decode('ascii')
        dos_source_bindings.review_provider_source(text, provider, symbols)
        basename = provider['basename']
        if (basename != dos_source_bindings.PROVIDER_SPECS[provider['module']][0]
                or provider['profile'] != 'msc600ax'
                or provider['flags'] != ['/AL', '/Os', '/Gs']):
            raise ValueError('unreviewed storage provider compiler context')
        path = source_dir / (basename + '.c')
        path.write_bytes(raw)
        generated_pin = pin(path)[1]
        report['inputs'].append(source_pin)
        report['generated_files'].append(generated_pin)
        report['translation_units'].append({
            'module': provider['module'], 'unit': 'root', 'basename': basename,
            'source': source_pin, 'generated_source': generated_pin, 'lang': 'c',
            'profile': provider['profile'], 'flags': provider['flags'],
            'reviewed_bodies': [], 'source_binding': None, 'storage_provider': provider,
            'status': 'PREPARED'})
    report['function_dispositions'] = {
        'EXACT_C': sum(c.get('kind') == 'C' for m in manifest['modules'].values() for c in m.get('claims', [])),
        'GENUINE_ASM': sum(c.get('kind') == 'ASM' for m in manifest['modules'].values() for c in m.get('claims', [])),
        'BEHAVIOR_EXACT_CONFIRMED': sum(r['status'] == 'BEHAVIOR_EXACT_CONFIRMED' for r in static_reviews.values()),
        'EXACT_AFTER_STATIC_AUDIT': sum(r['status'] == 'EXACT' for r in static_reviews.values()),
        'CONTRACT_EQUIVALENT': sum(r['status'] == 'CONTRACT_EQUIVALENT' for r in static_reviews.values()),
        'UNRESOLVED': sum(r['status'] == 'UNRESOLVED' for r in static_reviews.values())}
    report['historical_behavior_registrations'] = len(registry['entries'])
    # Approved dispositions are a debt inventory, never initializer/build material.
    debt_raw, debt_pin = pin(ROOT / 'work/takeover/behavioral-oracle/data-debt-disposition-approved-v1.json')
    report['inputs'].append(debt_pin)
    report['unresolved_data'] = [{k: s[k] for k in ('id', 'classification', 'size', 'semantic_assessment')}
                                 for s in json.loads(debt_raw)['spans']]
    report['historical_data_debt'] = [dict(s) for s in report['unresolved_data']]
    report['resolved_initialized_data'] = []
    report['runtime_components'] = []
    for name, library in manifest['runtime']['libraries'].items():
        _, library_pin = pin(Path(library['path']), library['sha256'])
        report['runtime_components'].append({'name': name, 'role': 'third-party MSC runtime library',
                                             **library_pin})
        report['inputs'].append(library_pin)
    return manifest, symbols


def compile_units(out, report, jobs, reuse):
    obj_dir = out / 'objects'
    obj_dir.mkdir(exist_ok=True)
    cache_path = out / 'compile-cache.json'
    cache = json.loads(cache_path.read_text()) if reuse and cache_path.exists() else {}
    tc_raw, tc_pin = pin(ROOT / 'layout/toolchain.json')
    report['inputs'].append(tc_pin)
    identities = {}
    profiles = sorted({row['profile'] for row in report['translation_units']})
    for name in profiles:
        profile = compiler.verify_profile(name)
        identities[name] = profile
        report['build_tools'].append({'profile': name, 'role': 'compiler/assembler', 'definition': profile})
        for rel, digest in profile['files'].items():
            report['inputs'].append(pin(Path(profile['directory']) / rel, digest)[1])
        inc = compiler.include_root(profile)
        for rel, digest in profile.get('include_files', {}).items():
            path = ROOT / rel[5:] if rel.startswith('repo:') else inc / rel
            report['inputs'].append(pin(path, digest)[1])
        tc = compiler.toolchain()
        runner = tc['runners'][profile['runner']] if profile.get('runner') else tc['runner']
        report['inputs'].append(pin(Path(runner['path']), runner['sha256'])[1])
    new_cache = {}
    def build(row):
        source = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
        key = sha(json.dumps({'source': row['generated_source'], 'profile': identities[row['profile']],
                             'flags': row['flags'], 'toolchain_sha': tc_pin['sha256']}, sort_keys=True).encode())
        path = obj_dir / (row['basename'] + '.OBJ')
        old = cache.get(row['module'], {})
        if old.get('key') == key and path.exists() and sha(path.read_bytes()) == old.get('sha256'):
            row['status'] = 'COMPILED_REUSED'
        else:
            run = compiler.assemble if row['lang'] == 'asm' else compiler.compile_c
            result = run(source, row['profile'], row['flags'], basename=row['basename'])
            log = out / (row['basename'] + '.log')
            log.write_text(result.log, encoding='utf-8')
            row['compiler_log'] = pin(log)[1]
            if not result.ok:
                row['status'] = 'COMPILE_FAILED'
                row['error'] = result.log[-3000:]
                return
            path.write_bytes(result.obj)
            row['status'] = 'COMPILED'
        row['object'] = pin(path)[1]
        if row.get('storage_provider'):
            row['provider_verification'] = dos_source_bindings.verify_provider(
                OmfReader(communals=True).read(path.read_bytes()), row['storage_provider'])
        if row.get('source_binding'):
            # This reference object is source-built before visibility/address edits, never linked.
            # Reassemble it so a cached derived object cannot bypass the proof.
            control_pin = row['binding_control_source']
            canonical = pin(ROOT / control_pin['path'], control_pin['sha256'])[0].decode('latin1')
            build_control = compiler.assemble if row['lang'] == 'asm' else compiler.compile_c
            reference = build_control(canonical, row['profile'], row['flags'], basename=row['basename'])
            if not reference.ok:
                raise ValueError('canonical binding control failed: ' + row['module'])
            reference_dir = out / 'binding-controls'
            reference_dir.mkdir(exist_ok=True)
            reference_path = reference_dir / path.name
            reference_path.write_bytes(reference.obj)
            reader = OmfReader(communals=True)
            row['binding_verification'] = dos_source_bindings.verify_objects(
                reader.read(reference.obj), reader.read(path.read_bytes()), row['source_binding'])
            row['binding_verification']['canonical_control_object'] = pin(reference_path)[1]
        new_cache[row['module']] = {'key': key, 'sha256': row['object']['sha256']}
        print(row['module'], row['status'], flush=True)
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(build, report['translation_units']))
    cache_path.write_text(json.dumps(new_cache, indent=2) + '\n')
    report['generated_files'].append(pin(cache_path)[1])
    report['generated_files'] += [pin(p)[1] for p in sorted(out.glob('U*.log'))]
    report['generated_files'] += [row['object'] for row in report['translation_units'] if 'object' in row]
    report['generated_files'] += [row['binding_verification']['canonical_control_object']
        for row in report['translation_units'] if 'binding_verification' in row]


def audit_layout(report):
    """Record source-visible fixed offsets; do not guess replacement semantics."""
    sites = []
    for row in report['translation_units']:
        if row['lang'] != 'asm':
            continue
        text = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(r'(?i)\b3DFCh\b', line.split(';', 1)[0]):
                sites.append({'module': row['module'], 'source': row['source'],
                              'line': number, 'instruction': line.strip()})
    queue = next((r for r in report['translation_units'] if r['module'] == 'root:1FD2'), {})
    queue_source = (ROOT / queue['generated_source']['path']).read_text(encoding='latin1') if queue else ''
    queue_bound = (queue.get('source_binding', {}).get('queue_storage') ==
                   {'slots': 7, 'stride': 16, 'pointer_view': '_g_5FFE'}
                   and '(int)0x91b0' not in queue_source)
    report['layout_dependencies'] = [{
        'id': 'driver-row-offset-buffer', 'status': 'UNRESOLVED' if sites else 'SOURCE_BOUND',
        'sites': sites, 'storage_source': 'src/root/m1B4E.asm',
        'storage_label': '_g_3DFC', 'size_from_source': 964,
        'reason': 'Driver initialization and raster paths use a fixed DGROUP offset. '
                  'The accepted owner defines _g_3DFC and _g_3DAE as the DGROUP segment. '
                  'A changed layout needs reviewed symbolic references or proven placement.',
        'scope_limit': 'This is one confirmed family, not a completed scan of every numeric operand.'}, {
        'id': 'driver-callback-table-owner',
        'status': 'SOURCE_BOUND' if any(r['module'] == 'source-owned:driver-callback-table' for r in report['translation_units']) else 'UNRESOLVED',
        'owner': '_driver_callback_table', 'slots': 25, 'slot_bytes': 4,
        'reason': 'Source reset/copy and four driver tables prove 25 far-pointer slots. One typed near communal owns the slots; 23 registered names are bounded aliases. The existing symbolic _g_3DF8 pointer is verified under shifted DGROUP on both linkers. Historical COMDEF TU/order and wider driver frame integration remain separate.'}, {
        'id': 'remaining-assembly-address-audit', 'status': 'UNRESOLVED',
        'reason': 'The broader audit of fixed numeric operands and segment/group frames is pending. '
                  'Indexed numeric bases, g_5A9C storage/initializers and unchecked error-path addresses remain separate gates.'}, {
        'id': 'sound-selector-out-of-range-layout', 'status': 'UNRESOLVED',
        'sources': ['src/S20/m39F1.c', 'src/S15/m384C.c', 'src/root/m15F8.c', 'src/root/m00DF.c', 'src/root/m277E.c',
                    'src/root/m293A.c', 'src/root/m2815.c'],
        'reason': 'The command-line parser accepts /s9, but detector/setup/cleanup '
                  'tables have only nine entries (0..8). If the sound DB open returns, '
                  'detector index 9 reads the adjacent same-TU saved-state pointer '
                  'and calls its source-owned data as code. Return and effects are '
                  'unproved. Conditional later setup/cleanup overreads include '
                  'cross-TU data adjacency. Complete saved-state storage does not '
                  'resolve this executable/layout dependency; no clamp, extra slot '
                  'or padding is introduced.'}, {
        'id': 'graphics-computed-copy-layout', 'status': 'UNRESOLVED',
        'source': 'src/root/m1E57.c',
        'reason': 'The clip sentinel/generation count controls a copy to FAR_BSS 50F6:3C14. '
                  'Large counts can intersect the historical graphics table addresses. '
                  'Initial-state recipes do not prove those counts unreachable or preserve '
                  'such physical overlap under an independent layout. Punt return and '
                  'sentinel-copy bounds remain unresolved.'}, {
        'id': 'driver-indexed-addresses',
        'status': 'SOURCE_BOUND' if all(any(r['module'] == module and
            (r.get('source_binding') or {}).get('indexed_address_operands') for r in report['translation_units'])
            for module in dos_source_bindings.INDEXED_OPERANDS) and any(r['module'] == 'root:2650' and
            (r.get('source_binding') or {}).get('glyph_edge_owner') for r in report['translation_units']) else 'UNRESOLVED',
        'operand_count': 10,
        'reason': 'The bounded 3DCA, 6778 and 2226 indexed reads bind to existing source storage. '
                  'A generated-only glyph label adds no allocation. Closed site sets and '
                  'whole-object checks preserve all other bytes and ordered fixups.'}, {
        'id': 'graphics-tail-mask-addresses',
        'status': 'SOURCE_BOUND' if all(any(r['module'] == module and any(s.get('graphics_mask_operand')
            for s in (r.get('source_binding') or {}).get('relocations', [])) for r in report['translation_units'])
            for module in dos_source_bindings.GRAPHICS_MASK_OPERANDS) else 'UNRESOLVED',
        'operand_count': 2,
        'reason': 'Two bounded mask reads bind symbolically to mutable formula-derived near arrays '
                  'with exact DGROUP-frame OFFSET16 sites. Initial state and unchecked copies are separate proofs.'}, {
        'id': 'map-viewport-grid-layout', 'status': 'UNRESOLVED',
        'sources': ['src/root/m0250.c', 'src/S26/m39C7.c'],
        'declared_grid': 'fd_50F6_15C4[30][40]',
        'reason': 'ZapEuMapAt and InvalEuMap bound writes against runtime viewport dimensions, '
                  'rather than the thirty-row/forty-column storage extent. Dimensions derive '
                  'from object 4 rectangles; resize and loaded window offsets are not yet proved '
                  'to enforce that grid bound. A baseline resource rectangle in range does not '
                  'prove all reachable writes or preserve cross-object overreads under a new layout.'}, {
        'id': 'menu-table-cross-owner-layout', 'status': 'UNRESOLVED',
        'sources': ['src/root/m1FD2.c', 'src/S10/m35F5.c', 'src/S17/m384C.c'],
        'historical_intersections': [
            {'array': 'fd_50F6_46BC', 'index': 10, 'target': 'fd_50F6_46D0'},
            {'array': 'fd_50F6_46A8', 'index': 20, 'target': 'fd_50F6_46D0'}],
        'reason': 'Menu title-length and x-position arrays are written until a resource '
                  'title sentinel, with no established capacity or title-count cap. '
                  'Original word indices 10 and 20 respectively reach the separately '
                  'owned render-delay word. Further words reach the bitmap Handle slot. '
                  'The scalar owner does not prove those writes unreachable or preserve '
                  'their cross-object effects under an independent layout.'}, {
        'id': 'database-open-minus-one-record', 'status': 'UNRESOLVED',
        'source': 'src/root/m1A28.c', 'normal_owner': 'fd_50F6_3958[4]',
        'historical_failure_address': '50F6:38DC',
        'reason': 'GetFreeHandle returns -1 when four slots are occupied. OpenDB calls Punt '
                  'and then computes the record address if it returns. A four-record typed '
                  'owner supplies no preceding storage; returning-Punt reachability and layout '
                  'semantics must be proved separately.'}, {
        'id': 'database-handle-plus-four', 'status': 'UNRESOLVED',
        'source': 'src/root/m1A53.c', 'normal_owner': 'db_handles[4]',
        'historical_failure_address': '50F6:3B58',
        'reason': 'A returning failed OpenDB can be stored at db_handles[4] before the '
                  'front end checks the negative result. The original address overlaps the '
                  'distinct fd_50F6_3B58 object. No fifth slot, padding or noreturn assumption '
                  'is introduced; this remains a separate source-only preflight gate.'}, {
        'id': 'clip-rect-segment-frame',
        'status': 'SOURCE_BOUND' if any((r.get('source_binding') or {}).get('segment_corrections')
                                      for r in report['translation_units']) else 'UNRESOLVED',
        'operand_count': 1,
        'reason': 'The g_5A9C OFFSET is DGROUP-relative. Its paired SEG must name DGROUP; '
                  'the exact BASE16 site changes target/frame together, preserving all bytes and '
                  'ordered unrelated fixups. Both linkers pass the shifted-group helper and explicitly '
                  'fail the old segment frame before dereference. Rect ownership/initializers remain open.'}, {
        'id': 'mouse-callback-code-offset-frames',
        'status': 'SOURCE_BOUND' if any(r['module'] == 'root:1B73' and len(
            (r.get('source_binding') or {}).get('code_offset_reframes', [])) == 5
            for r in report['translation_units']) else 'UNRESOLVED',
        'operand_count': 5,
        'reason': 'Four interrupt callback offsets and one same-module near callback use MOUSE_TEXT. '
                  'Natural LEA source operands retain every instruction byte and all target displacements; '
                  'five closed OMF frame fields change from DGROUP to the code segment. '
                  'Both linkers pass separate shifted-group fixtures; the wrong-frame negative fails before its callback call.'}, {
        'id': 'driver-local-ss-frames',
        'status': 'SOURCE_BOUND' if all(any(r['module'] == module and len(
            (r.get('source_binding') or {}).get('local_reframes', [])) == len(sites)
            for r in report['translation_units']) for module, sites in dos_source_bindings.LOCAL_SS_SITES.items()) else 'UNRESOLVED',
        'operand_count': 10,
        'reason': 'Same-TU source labels own these local fields. Exact SEGDEF displacements and source anchors are guarded; scoped SS frames become DGROUP without changing bytes or ordered fixup identities. Both linkers validate shifted group addresses and paragraph-frame normalization.'}, {
        'id': 'driver-pattern-bank-addresses',
        'status': 'SOURCE_BOUND' if all(any(r['module'] == module and
            (r.get('source_binding') or {}).get(key) for r in report['translation_units'])
            for module, key in [('root:1B4E', 'pattern_bank_owner'), ('S00:31AD', 'pattern_bank_operands')]) else 'UNRESOLVED',
        'operand_count': 3, 'owner': dos_source_bindings.PATTERN_BANK_OWNER,
        'reason': 'Sixteen accepted source records own the 256-byte bank. Selector and phase arithmetic bounds every read. A zero-byte public and exactly three symbolic DGROUP operands remove the historical numeric base; original table bytes and unrelated fixups are preserved.'}, {
        'id': 's01-pattern-view-4220',
        'status': 'SOURCE_BOUND' if any((r.get('source_binding') or {}).get('s01_pattern_view_operands')
            for r in report['translation_units']) else 'UNRESOLVED',
        'site': ['S01:3126', 'S01A_TEXT', 0x5A8, '_g_4220'],
        'owner': '_g_41D0', 'owner_bytes': 256, 'view_offset': 80, 'max_displacement': 0x76,
        'reason': 'Source initialized high byte and masked overlapping word producer bound the phase reads within the existing bank. Scoped DGROUP frame and whole ordered-object proof remove one historical literal.',
        'scope_limit': 'Reviewed normal/interrupt SS routes and direct writer closure only; the broader numeric/frame audit remains unresolved.'}, {
        'id': 'driver-external-ss-frames',
        'status': 'SOURCE_BOUND' if all(any(r['module'] == module and len(
            (r.get('source_binding') or {}).get('reframes', [])) == count
            for r in report['translation_units']) for module, count in
            [('S00:31AD', 64), ('S01:3126', 36), ('S02:3126', 2), ('S03:3126', 26)]) else 'UNRESOLVED',
        'operand_count': 128,
        'reason': 'CRT and interrupt CFG provenance establishes SS=DGROUP. Only the signed external OFFSET16 sites receive scoped DGROUP frames; whole-object checks preserve all bytes and ordered unrelated fixups.',
        'scope_limit': 'This excludes local-symbol operands, numeric pattern addresses and g_5A9C.'}, {
        'id': 'input-event-queue-fixed-pointer', 'status': 'SOURCE_BOUND' if queue_bound else 'UNRESOLVED',
        'source': 'src/root/m1FD2.c', 'initializer': '(int)0x91b0',
        'storage_view': 'g_5FF2 + 12 (_g_5FFE)',
        'consumer_source': 'src/root/m1B73.asm',
        'consumer_functions': ['_f_1B73_032E', '_f_1B73_036E'],
        'capacity_from_source': 7, 'event_stride_from_source': 16,
        'generated_storage': '_input_queue' if queue_bound else None,
        'generated_symbolic_initializer': '(int)(struct Event near *)input_queue' if queue_bound else None,
        'reason': 'The C initializer is an input-event queue address, not an ordinary timer '
                  'count. ASM enqueue/dequeue load it into SI, index by 16*slot, and read/write '
                  '16 bytes with a seven-slot wrap bound. No accepted source placement owns '
                  'DGROUP:91B0. The reviewed generated binding supplies a 112-byte near communal '
                  'and symbolic pointer. Admission requires whole-object checks and the selected '
                  'linker/MSC-startup execution contract; without that binding the literal remains unsafe.'}]


def accept_binding_checks(report):
    bound = [r for r in report['translation_units'] if r.get('source_binding')]
    providers = [r for r in report['translation_units'] if r.get('storage_provider')]
    if (bound and all(r.get('binding_verification', {}).get('status') == 'PASS' for r in bound)
            and all(r.get('provider_verification', {}).get('status') == 'PASS' for r in providers)):
        if (not report.get('resolved_segment_alignment') and any(
                r.get('module') == 'root:1F80' and 'object' in r for r in report['translation_units'])):
            proof = dos_alignment_debt.verify_source_object(ROOT, report)
            debt = [s for s in report['unresolved_data'] if s['id'] == 'far_data']
            if len(debt) != 1 or debt[0]['size'] != 12:
                raise ValueError('FAR_DATA alignment debt inventory changed')
            report['resolved_segment_alignment'] = [dict(proof, id='far_data', size=12)]
            report['unresolved_data'] = [s for s in report['unresolved_data'] if s['id'] != 'far_data']
        for dependency in report['layout_dependencies']:
            if dependency['status'] == 'SOURCE_BOUND':
                dependency['status'] = 'RESOLVED'
        initialized = {r['module'] for r in providers if r['module'] in dos_source_bindings.INITIALIZED_PROVIDER_SPECS}
        if initialized == set(dos_source_bindings.INITIALIZED_PROVIDER_SPECS) and not report.get('resolved_initialized_data'):
            # Functional initialization is discharged only after whole-object proof.
            # Keep the historical ownership ledger and the independent copy gate.
            sizes = {s['id']: s['size'] for s in report['unresolved_data']}
            if sizes.get('dgroup_2100') != 24 or sizes.get('dgroup_68ac') != 10:
                raise ValueError('initialized data debt inventory changed')
            report['resolved_initialized_data'] = [
                {'id': 'dgroup_2100', 'offset': 0, 'size': 8, 'module': 'source-owned:graphics-formulas'},
                {'id': 'dgroup_2100', 'offset': 8, 'size': 16, 'module': 'source-owned:g2108-color-translation'},
                {'id': 'dgroup_68ac', 'offset': 0, 'size': 10, 'module': 'source-owned:graphics-formulas'}]
            report['unresolved_data'] = [s for s in report['unresolved_data'] if s['id'] not in ('dgroup_2100', 'dgroup_68ac')]
        if (any(r['module'] == 'source-owned:display-mode-selector' for r in providers)
                and not report.get('resolved_source_state')):
            shared = next(s for s in report['unresolved_data'] if s['id'] == 'dgroup_5a96')
            if shared['size'] != 26:
                raise ValueError('display selector shared-state debt inventory changed')
            shared['size'] = 25
            shared['residual_ranges'] = [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 24}]
            report['resolved_source_state'] = [{
                'id': 'dgroup_5a96', 'offset': 1, 'size': 1,
                'module': 'source-owned:display-mode-selector',
                'proof': 'Reviewed source first-write dominance plus real config-producer/CRT tests; original initializer unobserved.',
                'scope_limit': 'Other shared UI bytes, Rect sentinel and computed-copy layout remain unresolved.'}]
        accept_clip_pointer_data(report)


def accept_clip_pointer_data(report):
    """Account for an already admitted pointer without closing its pointee debt."""
    module = 'source-owned:clip-pointer'
    owners = [r for r in report['translation_units'] if r.get('module') == module]
    if not owners:
        return
    expected = [{'name': '_g_5AAC', 'kind': 'near', 'length': 4}]
    if (len(owners) != 1 or owners[0].get('provider_verification') != {
            'status': 'PASS', 'data_only': True, 'live_initialized_bytes': 0,
            'code_bytes': 0, 'communals': expected, 'publics': [], 'fixups': []}):
        return  # An uncompiled or incomplete proof cannot discharge data debt.
    disposition = report.get('clip_pointer_data_disposition', {})
    accepted = [{'id': 'dgroup_5a96', 'offset': 22, 'size': 4, 'module': module,
        'owner': '_g_5AAC', 'view': '_g_5AAE', 'view_offset': 2, 'view_size': 2,
        'new_residual_ranges': [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 20}]}]
    if (disposition.get('root_reviewed') is not True or disposition.get('accepted') != accepted
            or disposition.get('historical_data_debt_modified') is not False):
        raise ValueError('clip-pointer data disposition lacks its bounded root decision')
    contract = report.get('clip_pointer_contract', {})
    required = {'positive_communal_alias_plus2': 'PASS', 'wrong_alias_plus0': 'FAIL',
                'nonzero_initializer': 'FAIL'}
    if contract.get('required_cases') != required:
        raise ValueError('clip-pointer data disposition lacks its exact controls')
    for profile in ('rtlink400', 'rtlink610'):
        dos_source_bindings.require_provider_contracts(report, profile,
            compiler.toolchain()['linkers'][profile], [(module, 'clip_pointer_contract', 2)])
    state = report.setdefault('resolved_source_state', [])
    shared = next(r for r in report['unresolved_data'] if r['id'] == 'dgroup_5a96')
    resolution = {'id': 'dgroup_5a96', 'offset': 22, 'size': 4, 'module': module,
        'proof': 'Reviewed typed pointer and +2 segment-word view, whole data-only object and both RTLink/MSC startup controls.',
        'contract': 'work/source-only-dos/clip-pointer-contract-v1.json',
        'scope_limit': 'Only functional pointer storage; historical ledger, Rect/sentinel and computed-copy layout remain unresolved.'}
    previous = [r for r in state if r.get('module') == module]
    if previous:
        if (previous != [resolution] or shared['size'] != 21 or shared.get('residual_ranges') !=
                [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 20}]):
            raise ValueError('clip-pointer data disposition recorded state changed')
        return
    if (shared['size'] != 25 or shared.get('residual_ranges') !=
            [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 24}]):
        raise ValueError('clip-pointer data disposition residual inventory changed')
    shared['size'] = 21
    shared['residual_ranges'] = [{'offset': 0, 'size': 1}, {'offset': 2, 'size': 20}]
    state.append(resolution)


def unresolved_symbols(out, report, symbols, manifest):
    reader = OmfReader(communals=True)
    owners, uses, kinds, objects = {}, {}, {}, {}
    for row in report['translation_units']:
        if 'object' not in row:
            continue
        obj = reader.read((ROOT / row['object']['path']).read_bytes(), row['module'])
        objects[row['module']] = obj
        for p in obj.publics:
            owners.setdefault(p['name'], []).append(row['module'])
            kinds[p['name']] = 'code' if p['segment'].endswith('_TEXT') else 'data'
        for p in obj.communals:
            owners.setdefault(p['name'], []).append(row['module'] + ' (communal)')
        for n in obj.externals:
            uses.setdefault(n, []).append(row['module'])
    libraries = set()
    for lib in report['runtime_components']:
        modules = reader.split_library(Path(lib['path']).read_bytes())
        for member_name, member_raw in modules:
            obj = reader.read(member_raw, member_name)
            libraries.update(p['name'] for p in obj.publics)
            libraries.update(p['name'] for p in obj.communals)
    linker_publics = {'_edata', '_end'}
    # Assembly and old prototypes retain registry aliases. Linker DEFINE joins
    # identical function addresses symbolically; no machine bytes are rewritten.
    names_at = {}
    for table in ('code', 'data'):
        for name, row in symbols[table].items():
            names_at.setdefault((table, row.get('unit', 'S27'), row['seg'], row['off']), []).append(name)
    definitions = []
    for name in sorted(set(uses) - set(owners) - libraries - linker_publics):
        reg_name = name[1:] if name.startswith(('_', '@')) else name
        table = 'code' if reg_name in symbols['code'] else 'data'
        row = symbols[table].get(reg_name)
        if row:
            address = (table, row.get('unit', 'S27'), row['seg'], row['off'])
            candidates = [prefix + n for n in names_at[address]
                          for prefix in ('_', '@') if prefix + n in owners]
            if len(candidates) == 1:
                definitions.append({'alias': name, 'owner': candidates[0],
                                    'kind': table, 'reason': 'same reviewed symbol registry address',
                                    'address': list(address[1:])})
    for spec in report.get('reviewed_data_aliases', []):
        if spec['alias'] in owners or spec['alias'] in {d['alias'] for d in definitions}:
            raise ValueError('data alias already has a different definition')
        if owners.get(spec['owner']) != [spec['module']]:
            raise ValueError('data alias source owner is missing or duplicated')
        row = next(r for r in report['translation_units'] if r['module'] == spec['module'])
        definitions.append(dos_source_bindings.bind_data_alias(
            spec, objects[spec['module']], row, manifest['modules'][spec['module']], symbols))
    for spec in report.get('reviewed_communal_aliases', []):
        if spec['alias'] in owners or spec['alias'] in {d['alias'] for d in definitions}:
            raise ValueError('communal alias already has a different definition')
        if owners.get(spec['owner']) != [spec['module'] + ' (communal)']:
            raise ValueError('communal alias source owner is missing or duplicated')
        row = next(r for r in report['translation_units'] if r['module'] == spec['module'])
        definitions.append(dos_source_bindings.bind_communal_alias(spec, objects[spec['module']], row, symbols))
    report['symbolic_aliases'] = definitions
    linker_publics.update(d['alias'] for d in definitions)
    missing = sorted(set(uses) - set(owners) - libraries - linker_publics)
    report['unresolved_symbols'] = []
    for n in missing:
        name = n[1:] if n.startswith(('_', '@')) else n
        table = 'code' if name in symbols['code'] else 'data' if name in symbols['data'] else 'unknown'
        item = {'name': n, 'kind': table, 'consumers': sorted(set(uses[n])),
                'registry': symbols.get(table, {}).get(name)}
        if table == 'data':
            address = item['registry']
            candidates = []
            for key, module in manifest['modules'].items():
                for segment, placement in module.get('placements', {}).items():
                    if (placement['seg'] == address['seg'] and placement['off'] <= address['off']
                            < placement['off'] + placement['size']):
                        candidates.append({'module': key, 'segment': segment,
                            'source': module['source'], 'source_sha256': module['source_sha256'],
                            'offset_in_accepted_placement': address['off'] - placement['off'],
                            'placement': placement})
            item['accepted_storage_candidates'] = candidates
            item['required_resolution'] = ('reviewed FAR_BSS definition and compatible consumer views'
                if address['seg'] == 0x50F6 else 'source owner/public or interior symbolic alias'
                if candidates else 'source storage/reachability investigation')
            item['declaration_contexts'] = []
            for row in report['translation_units']:
                if row['lang'] != 'c' or row['module'] not in item['consumers']:
                    continue
                text = (ROOT / row['generated_source']['path']).read_text(encoding='latin1')
                for match in re.finditer(r'(?m)^extern\s+[^;]+;', text):
                    if re.search(r'\b' + re.escape(name) + r'\b', match.group()):
                        item['declaration_contexts'].append({'module': row['module'],
                            'declaration': match.group(), 'source': row['generated_source']})
        report['unresolved_symbols'].append(item)
    report['duplicate_publics'] = {n: rows for n, rows in owners.items()
                                  if len([x for x in rows if '(communal)' not in x]) > 1}
    report['unresolved_functions'] = (list(report.get('unresolved_semantics', []))
        + [r for r in report['unresolved_symbols'] if r['kind'] == 'code'])


def independent_link_diagnostics(log_text):
    """Reject RTLink diagnostics even when it writes a partial MZ image."""
    return bool(re.search(r'\bwrt\d{4}\b|\b(?:warnings?|errors?|fatal|undefined|unresolved|aborted)\b|cannot\s+open',
                          log_text, re.IGNORECASE))


def link_units(out, report, profile):
    """Independent period link. Only successful, complete inputs can reach it."""
    if (report['errors'] or report['unresolved_functions'] or report['unresolved_data']
            or any(r['status'] != 'RESOLVED' for r in report.get('layout_dependencies', []))
            or report.get('unresolved_symbols') or report.get('duplicate_publics')
            or any('object' not in row for row in report['translation_units'])):
        report['errors'].append('independent link refused: incomplete source/data preflight')
        return
    link_dir = out / 'link'
    if link_dir.exists():
        raise ValueError('link output directory already exists; use a fresh --out')
    link_dir.mkdir()
    tc = compiler.toolchain()
    tool = tc['linkers'][profile]
    components = [(str(Path(tool['directory']) / name), digest) for name, digest in tool['files'].items()]
    components += [(r['path'], r['sha256']) for r in report['runtime_components']]
    dos_alignment_debt.require_contract(report['far_data_alignment_contract'], profile, components)
    dos_source_bindings.require_history_startup_contract(report, profile, tool)
    dos_source_bindings.require_scalar_startup_contracts(report, profile, tool)
    dos_source_bindings.require_array_startup_contracts(report, profile, tool)
    dos_source_bindings.require_callback_storage_contract(report, profile, tool)
    dos_source_bindings.require_near_storage_contracts(report, profile, tool)
    dos_source_bindings.require_additional_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v15_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v17_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v18_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v19_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v20_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v21_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v22_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v23_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v24_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v25_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v26_storage_contracts(report, profile, tool)
    dos_source_bindings.require_v27_storage_contracts(report, profile, tool)
    dos_source_bindings.require_display_selector_contract(report, profile, tool)
    dos_source_bindings.require_queue_startup_contract(report, profile, tool)
    dos_source_bindings.require_assembly_frame_contract(report, profile, tool)
    dos_source_bindings.require_dgroup_rect_frame_contract(report, profile, tool)
    dos_source_bindings.require_mouse_code_offset_contract(report, profile, tool)
    dos_source_bindings.require_driver_ss_frame_contract(report, profile, tool)
    dos_source_bindings.require_pattern_bank_contract(report, profile, tool)
    dos_source_bindings.require_s01_pattern_view_contract(report, profile, tool)
    dos_source_bindings.require_local_frame_contract(report, profile, tool)
    dos_source_bindings.require_initialized_and_indexed_contracts(report, profile, tool)
    contract = report.get('linker_alias_contract', {})
    if any(row.get('offset') for row in report.get('symbolic_aliases', [])):
        cases = [r for r in contract.get('cases', []) if r['linker'] == profile]
        contract_inputs = {p['path'].replace('\\', '/'): p['sha256'] for p in contract.get('inputs', [])}
        required = {'correct': 'PASS', 'wrong_near': 'FAIL', 'wrong_far': 'FAIL',
                    'unsuffixed_near': 'FAIL', 'unsuffixed_far': 'FAIL'}
        if (len(cases) != len(required) or {r['case'] for r in cases} != set(required)
                or not all(r['passed'] and r['actual'] == r['expected'] == required[r['case']] for r in cases)
                or any(contract_inputs.get(str(Path(tool['directory']) / name).replace('\\', '/')) != digest
                       for name, digest in tool['files'].items())):
            raise ValueError('selected linker lacks a matching reviewed interior alias contract')
    runner = tc['runners']['dosbox-x']
    report['linker_components'].append({'profile': profile,
        'role': 'third-party linker and stock overlay manager; not extracted from SimAnt', 'definition': tool})
    for rel, digest in tool['files'].items():
        report['inputs'].append(pin(Path(tool['directory']) / rel, digest)[1])
    report['inputs'].append(pin(Path(runner['path']), runner['sha256'])[1])
    tools_dir = compiler.pinned_tree(tool)
    for row in report['translation_units']:
        source = ROOT / row['object']['path']
        pin(source, row['object']['sha256'])
        shutil.copyfile(source, link_dir / source.name)
    for lib in report['runtime_components']:
        source = Path(lib['path'])
        pin(source, lib['sha256'])
        shutil.copyfile(source, link_dir / source.name.upper())
    # Keep the original four-area organization, but use the linker's own
    # generated vectors/manager/layout. No original executable is inspected.
    lines = ['OUTPUT SOURCE', 'MAP = SOURCE S,N,A,L,V,X', 'NODEFLIB',
             'LIBRARY LLIBCR, LIBH', 'RELOAD FAR 400', 'VERBOSE']
    def emit_files(rows, prefix='FILE '):
        names = [row['basename'] for row in rows]
        for i in range(0, len(names), 8):
            lines.append(prefix + ', '.join(names[i:i + 8]))
    emit_files([row for row in report['translation_units'] if row['unit'] == 'root'])
    emit_files([row for row in report['translation_units'] if row['module'].startswith('data:')])
    for lo, hi in ((0, 3), (4, 11), (12, 19), (20, 26)):
        lines.append('BEGINAREA')
        for section in range(lo, hi + 1):
            rows = [row for row in report['translation_units'] if row['unit'] == f'S{section:02d}']
            names = ', '.join(row['basename'] for row in rows)
            lines.append('SECTION FILE ' + names + (' PRELOAD' if section == 0 else ''))
        lines.append('ENDAREA')
    quote = lambda name: '"' + name + '"' if name.startswith('@') else name
    for row in report.get('symbolic_aliases', []):
        delta = dos_source_bindings.rtlink_alias_delta(row.get('offset', 0))
        lines.append(f"DEFINE {quote(row['alias'])} = {quote(row['owner'])}{delta}")
    script = link_dir / 'SOURCE.LNK'
    script.write_bytes(('\r\n'.join(lines) + '\r\n').encode('ascii'))
    (link_dir / 'RTLINK.CFG').write_bytes(b'SYNTAX = FREEFORMAT\r\n')
    (link_dir / 'RUN.BAT').write_bytes(
        f'@echo off\r\nD:\\{tool["executable"]} @SOURCE.LNK < NUL > LINK.LOG\r\n'.encode('ascii'))
    config = []
    for section, settings in runner['conf'].items():
        config.append('[' + section + ']')
        config += [f'{key}={value}' for key, value in settings.items()]
    config += ['[autoexec]', f'mount c "{link_dir}"', f'mount d "{tools_dir}" -ro',
               'c:', 'set LIB=C:\\;D:\\', 'call RUN.BAT', 'exit']
    conf = link_dir / 'dosbox.conf'
    conf.write_text('\n'.join(config) + '\n')
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    result = subprocess.run([runner['path'], '-conf', str(conf), '-fastlaunch', '-exit', '-nomenu'],
                            cwd=link_dir, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            timeout=900, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log = link_dir / 'LINK.LOG'
    log_text = log.read_text(encoding='latin1') if log.exists() else ''
    report['linker_log'] = pin(log)[1] if log.exists() else None
    image = link_dir / 'SOURCE.EXE'
    if result.returncode or not image.exists() or not log_text.strip() or independent_link_diagnostics(log_text):
        report['errors'].append('independent linker failed; inspect linker log')
        return
    raw, image_pin = pin(image)
    if raw[:2] != b'MZ':
        report['errors'].append('link output is not an MZ executable')
        return
    report['standalone_dos_executable'] = True
    report['executable'] = image_pin
    report['status'] = 'LINKED_NOT_EXECUTED'
    report['generated_files'] += [pin(p)[1] for p in link_dir.iterdir() if p.is_file()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'build/source-only-dos')
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--reuse', action='store_true')
    parser.add_argument('--link', action='store_true')
    parser.add_argument('--linker', choices=('rtlink400', 'rtlink610'), default='rtlink400')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    out = args.out.resolve()
    out.relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=True)
    denied = install_input_guard()
    report = {'schema': 'simant-source-only-dos-build-v1', 'target': 'SOURCE_ONLY_DOS',
              'paused_sdl3_commit': PAUSED_COMMIT, 'semantic_oracle': 'dos-semantic-oracle-v1',
              'inputs': [], 'generated_files': [], 'translation_units': [], 'build_tools': [],
              'runtime_components': [], 'linker_components': [], 'semantic_substitutions': [],
              'platform_runtime_substitutions': [], 'unresolved_functions': [], 'unresolved_data': [],
              'original_exe_bytes_used': {'game_code': 0, 'game_data': 0, 'fallback_debt': 0,
                                          'executable_fragments': 0},
              'standalone_dos_executable': False, 'runnable': 'NOT_EXECUTED',
              'historical_byte_identity': 'NOT_REQUIRED', 'human_acceptance': 'PENDING',
              'status': 'INCOMPLETE', 'errors': []}
    try:
        report['inputs'] += [pin(ROOT / 'tools' / name)[1] for name in
                             ('source_only_dos.py', 'compiler.py', 'csrc.py', 'omf.py', 'dos_alignment_debt.py',
                              'dos_storage_contracts.py', 'dos_storage_policies_v25.py', 'dos_storage_policies_v26.py', 'dos_storage_policies_v27.py')]
        report['inputs'].append(pin(ROOT / 'tools/dos_source_bindings.py')[1])
        manifest, symbols = prepare(out, report)
        audit_layout(report)
        if args.compile or args.link:
            compile_units(out, report, args.jobs, args.reuse)
            accept_binding_checks(report)
            unresolved_symbols(out, report, symbols, manifest)
        report['errors'] += [f"compile failed: {r['module']}" for r in report['translation_units']
                              if r['status'] == 'COMPILE_FAILED']
        if report['unresolved_data']:
            report['errors'].append('data dispositions still need source-built semantic resolution')
        if report.get('unresolved_symbols'):
            report['errors'].append(f"{len(report['unresolved_symbols'])} unresolved source symbols")
        if report.get('unresolved_semantics'):
            report['errors'].append(f"{len(report['unresolved_semantics'])} functions lack strict static semantic closure")
        if report.get('duplicate_publics'):
            report['errors'].append('duplicate mutable storage/function owners')
        if any(r['status'] != 'RESOLVED' for r in report.get('layout_dependencies', [])):
            report['errors'].append('source address/layout contracts remain unresolved')
        if any(report['original_exe_bytes_used'].values()):
            report['errors'].append('zero-original-byte invariant violated')
        if args.link:
            link_units(out, report, args.linker)
    except Exception as exc:
        report['errors'].append(f'{type(exc).__name__}: {exc}')
    report['denied_oracle_reads'] = denied
    if denied:
        report['errors'].append('forbidden oracle input was attempted')
    # A linked build can pass its build gate without claiming execution or acceptance.
    report['inputs'] = list({p['path']: p for p in report['inputs']}.values())
    report['generated_files'] = list({p['path']: p for p in report['generated_files']}.values())
    path = out / 'build-report.json'
    path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"SOURCE_ONLY_DOS {report['status']}: {len(report['translation_units'])} TUs; report {path}")
    for error in report['errors']:
        print(error)
    return 0 if report['standalone_dos_executable'] and not report['errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
