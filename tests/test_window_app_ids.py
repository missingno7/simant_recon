from pathlib import Path
import hashlib,importlib.util,json,unittest
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'src/program.json').is_file())
HERE=ROOT/'evidence/canonical/window-domain'
def module(name):
 spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'))
 result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
class ApplicationIDControls(unittest.TestCase):
 def test_full_writer_call_and_saved_span_census(self):
  facts=json.loads((HERE/'application-ids.json').read_text())
  self.assertEqual(module('application_ids_census').collect(),facts['census'])
  self.assertEqual(len(facts['census']['writers']),7)
  self.assertEqual(facts['census']['save_record_count'],307)
  self.assertEqual(facts['census']['save_coverage']['ExpSubStates'],[])
  self.assertEqual(facts['census']['save_coverage']['fd_3D57_07BE'],[])
 def test_original_signed_history_and_range_contrasts(self):
  facts=json.loads((HERE/'application-ids.json').read_text());probe=module('application_ids_probe')
  self.assertEqual(probe.exe.load().sha256,facts['oracle_sha256'])
  self.assertEqual(probe.controls(),facts['controls'])
  self.assertEqual(facts['controls']['cleared_proxy_contrast']['result'],253)
  self.assertTrue(facts['object_graphics_effects_remaining_open'])
  self.assertFalse(facts['handle_provider_proposed'])
 def test_source_pins(self):
  for path,digest in json.loads((HERE/'application-ids.json').read_text())['source_sha256'].items():
   self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
if __name__=='__main__':unittest.main()
