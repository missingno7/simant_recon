"""The shared ideal-v1 state contract for every sound variant.

These rules describe source use of Event words and yard IDs. Configuration
selection belongs to sound_off.py; neither rule takes a sound-mode argument.
"""
from .event_context import context_views,context_receipt
from .animation_identity import extend_schema,identity_views,identity_receipt

CONTRACT='ideal-state-v2'
SIDECARS=('observer.txt.hash.keyboard-context-v1','observer.txt.hash.ideal-state-v2','observer.txt.anim-ids')


def prepare_schema(state):
    state=extend_schema(state)
    state['event_context_rule']=context_receipt(state)
    state['animation_identity_rule']=identity_receipt(state)
    return state


def rules(state):
    return dict(event_context_rule=context_receipt(state),animation_identity_rule=identity_receipt(state))


def validate_rules(state,manifest):
    for name,receipt in rules(state).items():
        if state.get(name)!=receipt or manifest.get(name)!=receipt:
            raise ValueError('Missing/changed ideal-v1 observer rule: '+name)
    for name in SIDECARS:
        if 'capture/'+name not in manifest['files']:
            raise ValueError('Missing pinned ideal-v1 observation: '+name)


def configuration(state,grouped):
    """Same census, native grouped records or DOS individual records."""
    lines=[]
    for tag,views,width in [('KEYBOARD_CONTEXT',context_views(state),'records'),
                            ('IDENTITY_PATTERN',identity_views(state),'slots')]:
        if grouped:lines.append(f'{tag} {len(views)}')
        lines.extend(f'{"" if grouped else tag+" "}{v["index"]} {v[width]}' for v in views.values())
    return '\n'.join(lines)+'\n'
