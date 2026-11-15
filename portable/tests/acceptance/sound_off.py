"""Shipped no-sound CFG selection; observer rules live in ideal_observation."""
from pathlib import Path
import hashlib
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
# Compatibility imports for historical analysis scripts; one implementation.
try:
    from .event_context import context_views,context_receipt,validate_display_domain
except ImportError:
    from event_context import context_views,context_receipt,validate_display_domain

def select_config(raw):
    """Change only the Sound Mode digit; ReadConfig accepts this shipped value."""
    if len(re.findall(rb'(?im)^Sound Mode:[ \t]*[0-9?]',raw))!=1:
        raise ValueError('Unrecognized SIMANT.CFG sound selector')
    selected=re.sub(rb'(?im)^(Sound Mode:[ \t]*)[0-9?]',lambda m:m[1]+b'0',raw)
    validate_display_domain(selected)
    return selected

def configuration_receipt(raw):
    selected=select_config(raw)
    return dict(contract='shipped-sound-off-v1',selection='SIMANT.CFG Sound Mode: 0',
        original_sha256=hashlib.sha256(raw).hexdigest(),selected_sha256=hashlib.sha256(selected).hexdigest(),
        arguments=[],script_changes=[],
        source_evidence=['src/startup/dos_config.c:ReadConfig','src/sound/game_interface.c:snd_init_driver_once',
                         'src/sound/game_interface.c:mySongIsDone'])
