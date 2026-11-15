import tempfile
import unittest
from pathlib import Path
from .audio_content import compare_content,read_content


class PlaybackControls(unittest.TestCase):
    def rows(self):
        return ['B 0 0 0 0 100 10001','N 0 0 0 0 100 25 60 100 0',
            'S 0 0 0 0 100 0 14 256 0 2 2 0 4 80828486',
            'P 1 1 0 0 200 0 14 1 130','P 1 1 0 0 200 1 -1 0 128',
            'F 1 1 0 0 300 0','D 1 1 0 0 300 10001','X 1 1 0 0 300 0',
            'C 1 2 1 1 300 1234','E 1 2 1 1 300']

    def compare(self,left,right,tolerance=0,ns=None):
        with tempfile.TemporaryDirectory() as d:
            a,b=[Path(d)/n for n in ('dos','native')]
            for p,rows in ((a,left),(b,right)):
                p.write_text('SIMANT_AUDIO_CONTENT 2\n'+'\n'.join(rows)+'\n')
            return compare_content(a,b,1,tolerance=tolerance,playback=True,playback_tolerance_ns=ns)

    def test_absolute_game_time_ignores_irq_count_and_raw_opl(self):
        a=self.rows();b=[]
        for s in a:
            f=s.split();f[1]=str(int(f[1])*9);b.append(' '.join(f))
        # Raw register output is diagnostic, including different channel order.
        b.insert(0,'O 0 0 0 0 0 0 32 7')
        self.assertEqual(self.compare(a,b)['status'],'AUDIO_EQUAL')

    def test_song_note_instrument_volume_stop_and_missing_are_detected(self):
        a=self.rows()
        for old,new in [('10001','10002'),('25 60 100','26 60 100'),
                        ('25 60 100','25 61 100'),('25 60 100','25 60 101')]:
            b=[s.replace(old,new) for s in a]
            self.assertEqual(self.compare(a,b)['first_difference']['kind'],'PLAYBACK_CONTENT')
        for tag in ('B','N','F','D'):
            b=[s for s in a if not s.startswith(tag+' ')]
            self.assertEqual(self.compare(a,b)['status'],'AUDIO_DIFFERENCE')

    def test_interior_sample_byte_is_never_waived(self):
        a=self.rows();b=[s.replace('1 130','1 131') for s in a]
        result=self.compare(a,b,16)
        self.assertEqual(result['first_difference']['kind'],'SAMPLE_OUTPUT_BYTE')
        self.assertEqual(result['first_difference']['layer'],'sample-mixer')

    def test_time_and_completion_fail_closed(self):
        a=self.rows();b=[]
        for s in a:
            f=s.split();f[5]=str(int(f[5])+100 if int(f[5])==300 else int(f[5]));b.append(' '.join(f))
        self.assertEqual(self.compare(a,b)['status'],'AUDIO_DIFFERENCE')
        self.assertEqual(self.compare(a,b,1)['status'],'AUDIO_EQUAL')
        self.assertEqual(self.compare(a,b[:-1])['status'],'AUDIO_INCOMPLETE')
        b=a.copy();b[1]=b[1].replace(' 100 25',' 99 25')
        self.assertEqual(self.compare(a,b)['status'],'AUDIO_INCOMPLETE')

    def test_nanosecond_bound_uses_integer_sample_time(self):
        a=[]
        for row in self.rows():
            f=row.split();f[5]=str(int(f[5])+495_000_000_000);a.append(' '.join(f))
        for delta,expected in [(0,'AUDIO_EQUAL'),(1,'AUDIO_EQUAL'),(2,'AUDIO_DIFFERENCE')]:
            b=[]
            for row in a:
                f=row.split()
                if f[0]=='P':f[5]=str(int(f[5])+delta)
                b.append(' '.join(f))
            result=self.compare(a,b,ns=1)
            self.assertEqual(result['status'],expected)
            self.assertEqual(result['maximum_sample_ns']['output'],delta)
        self.assertEqual(self.compare(a,b,ns=0)['status'],'AUDIO_DIFFERENCE')

    def test_loop_metadata_and_wrapped_emissions(self):
        a=['S 0 0 0 0 100 0 14 256 0 2 1 128 4 80828486',
            'P 1 1 0 0 200 0 14 1 130','P 1 1 0 0 200 1 -1 0 128',
            'P 2 2 0 0 300 0 14 0 128','P 2 2 0 0 300 1 -1 0 128',
            'P 3 3 0 0 400 0 14 1 130','P 3 3 0 0 400 1 -1 0 128',
            'X 4 4 0 0 500 0','C 4 5 1 1 500 1234','E 4 5 1 1 500']
        self.assertEqual(self.compare(a,a)['status'],'AUDIO_EQUAL')
        b=[s.replace('2 1 128 4','2 2 128 4') for s in a]
        self.assertEqual(self.compare(a,b)['first_difference']['kind'],'SAMPLE_IDENTITY_OR_CONTENT')
        b=[s.replace('0 14 0 128','0 14 1 128') for s in a]
        self.assertEqual(self.compare(a,b)['first_difference']['kind'],'SAMPLE_OUTPUT_BYTE')


if __name__=='__main__':unittest.main()
