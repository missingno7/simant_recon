"""ideal-v1 reference identity and one-time executable machine profile."""
import json
from pathlib import Path
from .state_schema import ROOT,sha

def script_path(scenario):
    recipe=json.loads(scenario.read_text())
    return ROOT/'dos/scenarios/ideal-v1'/Path(recipe['script']).name

def machine_profile(capture,executable,original):
    from capstone import Cs,CS_ARCH_X86,CS_MODE_16
    from .capture_dos_steps import capture_addresses
    boundary=json.loads((capture/'boundary-manifest.json').read_text());base=boundary['runtime_base']
    addresses=capture_addresses(original,executable);memory=(capture/'exec-simstep.1.bin').read_bytes()
    start=base+addresses['kbd_int09_hook']
    words=[(i.address,int(i.op_str.split(',')[1],0)) for i in Cs(CS_ARCH_X86,CS_MODE_16).disasm(memory[start:start+80],start)
           if i.mnemonic=='mov' and i.op_str.startswith('dx, 0x')]
    if len(words)!=1:raise ValueError('IRQ09 DGROUP binding is not unique: '+str(words))
    execution=json.loads((capture/'execution-report.json').read_text())
    psp=base//16-16
    if memory[psp*16:psp*16+2]!=b'\xcd\x20':raise ValueError('Load profile PSP is not bound')
    environment_segment=int.from_bytes(memory[psp*16+0x2c:psp*16+0x2e],'little')
    environment_at=environment_segment*16
    environment_end=memory.find(b'\0\0',environment_at,environment_at+32768)
    if environment_end<environment_at:raise ValueError('Unterminated DOS environment')
    environment=[s.decode('latin1') for s in memory[environment_at:environment_end].split(b'\0')]
    profile=dict(contract='ideal-v1',executable_sha256=sha(executable),load_segment=base//16,
        irq09_dgroup=words[0][1],dgroup_instruction=words[0][0],
        psp_segment=psp,environment_segment=environment_segment,dos_environment=environment,
        keyboard_layout=execution['keyboard_layout'],keyboard_environment=execution['keyboard_environment'],
        civil_origin='1992-01-01T12:00:00',bios_origin=0x1800b0//2,ram_seed=0,
        scope='Per-executable constants bound from the real relocated wrapper and pinned launch environment; no per-event register values.')
    (capture.parent/'machine-profile.json').write_text(json.dumps(profile,indent=2)+'\n')
    return profile

def validate(directory,scenario):
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest.get('input_contract')!='ideal-v1' or not manifest.get('complete'):raise ValueError('Incomplete/non-ideal reference')
    if manifest['scenario_sha256']!=sha(scenario) or manifest['script_sha256']!=sha(script_path(scenario)):
        raise ValueError('Changed ideal-v1 scenario/script')
    for name,expected in manifest['files'].items():
        if sha(directory/name)!=expected:raise ValueError('Changed reference file: '+name)
    capture=directory/'capture';boundary=capture/'boundary-manifest.json'
    if sha(boundary)!=manifest['boundary_manifest_sha256']:raise ValueError('Changed capture manifest')
    data=json.loads(boundary.read_text())
    if data['compact_observer']['order_contract']!='ideal-v1':raise ValueError('Mixed recorder contracts')
    if sha(capture/'execution-report.json')!=data['execution_report_sha256']:raise ValueError('Changed execution receipt')
    from .keyboard_environment import validate_keyboard
    validate_keyboard(directory,manifest,json.loads(scenario.read_text()))
    from .frame_check import frame_manifest
    if manifest['frames']!=frame_manifest(capture,manifest['steps'],manifest['frames']['interval'],script_path(scenario).read_text()):
        raise ValueError('Changed frame coverage')
    profile=json.loads((directory/'machine-profile.json').read_text())
    if profile['executable_sha256']!=manifest['executable_sha256']:raise ValueError('Mixed executable/profile')
    execution=json.loads((capture/'execution-report.json').read_text())
    for pin in execution['inputs']:
        path=ROOT/pin['path']
        if pin['path'].startswith('assets/') or pin['path'].endswith('build-report.json'):
            if sha(path)!=pin['sha256']:raise ValueError('Changed reference input: '+pin['path'])
    recipe=json.loads(scenario.read_text())
    if manifest.get('variant')!='sound-off' and (manifest.get('clock_admission')!='native-clock-v1-irq-v3' or data.get('clock_revision')!='native-clock-v1-irq-v3'):
        raise ValueError('Pre-fix sound-on reference: re-record with native-clock-v1-irq-v3; old captures remain negative controls')
    if manifest.get('variant')=='sound-off':
        if manifest.get('clock_admission')!='direct-bda-v2' or not data.get('modifier_byte_reads'):
            raise ValueError('Pre-fix sound-off reference omits direct BIOS modifier-byte admission; use build/reference/sound-off')
        from .sound_off import context_receipt,configuration_receipt
        state=json.loads((directory/'schema.json').read_text())
        from .animation_identity import identity_receipt
        if manifest.get('animation_identity_rule')!=identity_receipt(state) or state.get('animation_identity_rule')!=manifest['animation_identity_rule']:
            raise ValueError('Missing/changed animation identity observation; use build/reference/sound-off-identity')
        if manifest.get('event_context_rule')!=context_receipt(state) or state.get('event_context_rule')!=manifest['event_context_rule']:
            raise ValueError('Changed or unproved keyboard event observation rule')
        if manifest.get('sound_configuration')!=configuration_receipt((ROOT/'assets/SIMANT.CFG').read_bytes()):
            raise ValueError('Changed no-sound configuration policy')
        if execution.get('sound_configuration')!=manifest['sound_configuration']:
            raise ValueError('DOS sound selection differs')
    if recipe.get('saved_game') and sha(ROOT/recipe['saved_game'])!=manifest.get('saved_game_sha256'):
        raise ValueError('Changed reference save')
    return manifest
