"""Shared ideal state rules keep their original narrow scope in every variant."""
import copy,unittest
from .ideal_observation import configuration,rules,validate_rules,SIDECARS
from .event_context import context_views,validate_display_domain
from .animation_identity import ARRAYS,SCALARS,PREFIX,identity_views

class IdealObservation(unittest.TestCase):
    def state(self):
        widths={'window_current_event':16,'window_previous_event':16,'input_queue':112,
                **{n:2*k for n,k in ARRAYS.items()},**{PREFIX+n:2 for n in SCALARS},'unlisted_animation_ids':8}
        state=dict(items=[dict(name=n,bytes=b,sentinel=False,category='game_state',verdict=True) for n,b in widths.items()])
        state.update(rules(state));return state

    def test_one_census_in_both_serializations(self):
        state=self.state();self.assertEqual(len(context_views(state)),3);self.assertEqual(len(identity_views(state)),11)
        grouped=configuration(state,True).splitlines();flat=configuration(state,False).splitlines();expanded=[]
        while grouped:
            tag,count=grouped.pop(0).split()
            expanded.extend(tag+' '+grouped.pop(0) for _ in range(int(count)))
        self.assertEqual(expanded,flat)
        indices={int(line.split()[1]) for line in flat}
        self.assertNotIn(len(state['items'])-1,indices)

    def test_receipts_and_pinned_streams_are_mandatory(self):
        state=self.state();manifest=dict(rules(state),files={'capture/'+n:'pin' for n in SIDECARS})
        validate_rules(state,manifest)
        for name in ('event_context_rule','animation_identity_rule'):
            bad=copy.deepcopy(manifest);del bad[name]
            with self.assertRaises(ValueError):validate_rules(state,bad)
        for name in SIDECARS:
            bad=copy.deepcopy(manifest);del bad['files']['capture/'+name]
            with self.assertRaises(ValueError):validate_rules(state,bad)
        bad=copy.deepcopy(manifest);bad['event_context_rule']['omitted_offsets']=[0,1,8,9,10,11]
        with self.assertRaises(ValueError):validate_rules(state,bad)

    def test_scope_width_and_display_negatives(self):
        state=self.state()
        for name in ('window_current_event','yard_rain_anim_indices'):
            bad=copy.deepcopy(state);next(v for v in bad['items'] if v['name']==name)['bytes']+=2
            with self.assertRaises(ValueError):configuration(bad,True)
        validate_display_domain(b'Display Mode: V\nSound Mode: 6\n')
        validate_display_domain(b'Display Mode: E\nSound Mode: 0\n')
        with self.assertRaises(ValueError):validate_display_domain(b'Display Mode: T\nSound Mode: 6\n')

if __name__=='__main__':unittest.main()
