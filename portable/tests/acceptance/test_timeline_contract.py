"""Machine-profile and observation negatives replacing replay admission controls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from .state_schema import ROOT
from .ideal_reference import validate_machine_profile
from .audio_content import read_content


class TimelineContract(unittest.TestCase):
    def test_fixed_profile_binds_both_executables_and_rejects_changes(self):
        for target in ('original','canonical'):
            directory=ROOT/'build/reference/sound-on-identity-v1/experiment'/target
            profile=json.loads((directory/'machine-profile.json').read_text())
            manifest=json.loads((directory/'manifest.json').read_text())
            boundary=json.loads((directory/'capture/boundary-manifest.json').read_text())
            memory=(directory/'capture/exec-simstep.1.bin').read_bytes()
            def check(value):validate_machine_profile(value,manifest['executable_sha256'],boundary['runtime_base'],memory)
            check(profile)
            for key in ('irq09_dgroup','dgroup_instruction','load_segment','environment_segment','bios_origin','ram_seed'):
                bad=copy.deepcopy(profile);bad[key]+=1
                with self.subTest(target=target,key=key),self.assertRaises(ValueError):check(bad)
            bad=copy.deepcopy(profile);bad['dos_environment'].append('BUG=1')
            with self.assertRaises(ValueError):check(bad)
            bad=copy.deepcopy(profile);bad['executable_sha256']='0'*64
            with self.assertRaises(ValueError):check(bad)

    def test_silent_content_isr_count_requires_complete_observation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'content'
            path.write_text('SIMANT_AUDIO_CONTENT 1\nC 0 1 1 1 1234\nE 0 1 1 1\n')
            self.assertEqual(read_content(path)['end']['tick'],0)
            path.write_text('SIMANT_AUDIO_CONTENT 1\nC 1 1 1 1 1234\nE 1 1 1 1\n')
            self.assertNotEqual(read_content(path)['end']['tick'],0)
            path.write_text('SIMANT_AUDIO_CONTENT 1\nC 0 1 1 1 1234\n')
            with self.assertRaises(ValueError):read_content(path)


if __name__=='__main__':unittest.main()
