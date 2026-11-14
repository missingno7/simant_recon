"""Shipped no-sound CFG selection and the bounded observer rule's view census."""
from pathlib import Path
import hashlib
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RULE='keyboard-context-v1'

def select_config(raw):
    """Change only the Sound Mode digit; ReadConfig accepts this shipped value."""
    if len(re.findall(rb'(?im)^Sound Mode:[ \t]*[0-9?]',raw))!=1:
        raise ValueError('Unrecognized SIMANT.CFG sound selector')
    selected=re.sub(rb'(?im)^(Sound Mode:[ \t]*)[0-9?]',lambda m:m[1]+b'0',raw)
    if not re.search(rb'(?im)^Display Mode:[ \t]*[VE](?:\s|$)',selected):
        raise ValueError('Keyboard context proof is restricted to supplied 640-wide EGA/VGA')
    return selected

def configuration_receipt(raw):
    selected=select_config(raw)
    return dict(contract='shipped-sound-off-v1',selection='SIMANT.CFG Sound Mode: 0',
        original_sha256=hashlib.sha256(raw).hexdigest(),selected_sha256=hashlib.sha256(selected).hexdigest(),
        arguments=[],script_changes=[],
        source_evidence=['src/startup/dos_config.c:ReadConfig','src/sound/game_interface.c:snd_init_driver_once',
                         'src/sound/game_interface.c:mySongIsDone'])

def context_views(state):
    """The complete global Event/copy census; never infer a mask from its bytes.

    window/events.c copies current to previous. window/menu_helpers.c defines
    input_queue[7]. Other Event copies are locals, outside per-entry global
    views. root:1B73::Queue0 is an 18-byte hot-box record queue, not Event.
    """
    found={}
    for index,item in enumerate(state['items']):
        name=item['name']
        if name in ('window_current_event','window_previous_event','input_queue'):
            expected=112 if name=='input_queue' else 16
            if item['bytes']!=expected or item['sentinel']:
                raise ValueError('Event view layout changed: '+name)
            found[name]=dict(index=index,records=expected//16,bytes=expected)
    if set(found)!={'window_current_event','window_previous_event','input_queue'}:
        raise ValueError('Missing explicitly bound Event storage')
    return found

def context_receipt(state):
    proof=ROOT/'evidence/canonical/native-input-irq/normal-words.md'
    header=HERE/'event_context_rule.h'
    return dict(contract=RULE,views=context_views(state),omitted_offsets=[8,9,10,11],
        event_codes='FA00..FAFF; F081..F087 only',scope='supplied HCEGANT 640-wide EGA/VGA',
        proof=proof.relative_to(ROOT).as_posix(),proof_sha256=hashlib.sha256(proof.read_bytes()).hexdigest(),
        observer_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),raw_observations_retained=True)
