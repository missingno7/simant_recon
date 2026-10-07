"""Canonical storage adjacency: independent DOS vectors and removal controls."""
from pathlib import Path
import copy,hashlib,json,re,subprocess,sys,tempfile,unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'portable'))
sys.path.insert(0,str(ROOT/'tools'))
from canonical_native_abi import scalar,semantic_spans
from workspace import retire


class SemanticSpansTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program=json.loads((ROOT/'src/program.json').read_text())
        cls.texts={m['source']:(ROOT/m['source']).read_text(encoding='latin1') for m in program['modules'] if m['lang']=='c'}
        cls.document=json.loads((ROOT/'portable/semantic-spans.json').read_text())
        scratch=ROOT/'build/scratch';scratch.mkdir(parents=True,exist_ok=True)
        cls.out=Path(tempfile.mkdtemp(prefix='semantic-spans-',dir=scratch))
        cls.contract=semantic_spans.Contracts(ROOT,cls.texts)
        cls.contract.extract('src/data/d3D57.c',scalar.convert(cls.texts['src/data/d3D57.c']))
        cls.source,cls.receipt=cls.contract.emit(cls.out)
        cls.cc='C:/msys64/mingw64/bin/gcc.exe'

    @classmethod
    def tearDownClass(cls):
        retire(cls.out,ROOT)

    def test_complete_saverec_census(self):
        self.assertEqual(len(semantic_spans.save_records(self.texts['src/S09/m35F5.c'])),307)
        self.assertEqual([r['record'] for r in self.contract.cross_records],[28,100])
        self.assertEqual(len(self.contract.cross_accesses),33)
        self.assertEqual(sum(r['file']!='src/root/m00DF.c' for r in self.contract.cross_accesses),29)

    def test_removing_either_span_fails_independent_census(self):
        for span in self.document['spans']:
            doc=copy.deepcopy(self.document)
            doc['spans']=[s for s in doc['spans'] if s['id']!=span['id']]
            with self.subTest(span=span['id']),self.assertRaisesRegex(ValueError,'cross-owner span undeclared'):
                semantic_spans.Contracts(ROOT,self.texts,doc)

    def test_missing_member_and_gap_are_rejected(self):
        for mutation in ('missing','gap'):
            doc=copy.deepcopy(self.document)
            member=doc['spans'][1]['members'][1]
            if mutation=='missing':member['owner']='no_such_owner'
            else:member['offset']+=1
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                semantic_spans.Contracts(ROOT,self.texts,doc)

    def test_new_consumer_must_be_declared(self):
        texts=dict(self.texts)
        texts['src/root/m00DF.c']+='\nint span_probe(void) { return fd_3D57_07A8[5]; }\n'
        doc=copy.deepcopy(self.document)
        for fact in doc['owner_layout'].values():
            if fact['source']=='src/root/m00DF.c':
                fact['source_sha256']=hashlib.sha256(texts[fact['source']].encode('latin1')).hexdigest()
        with self.assertRaisesRegex(ValueError,'consumer appears outside declared span'):
            semantic_spans.Contracts(ROOT,texts,doc)

    def test_missing_native_storage_cannot_be_emitted(self):
        contract=semantic_spans.Contracts(ROOT,self.texts)
        text=scalar.convert(self.texts['src/data/d3D57.c'])
        text=text.replace('fd_3D57_07AA','removed_option_owner')
        contract.extract('src/data/d3D57.c',text)
        with self.assertRaisesRegex(ValueError,'storage missing'):
            contract.emit(self.out)

    def compile(self,source,driver,name):
        main=self.out/(name+'-driver.c');main.write_text(driver)
        exe=self.out/(name+'.exe')
        run=subprocess.run([self.cc,'-std=c11','-fno-strict-aliasing',str(source),str(main),'-o',str(exe)],capture_output=True,text=True,timeout=30)
        (self.out/(name+'.compile.txt')).write_text(run.stdout+run.stderr)
        return run,exe

    def test_wrong_extent_fails_compile_time_assertions(self):
        broken=self.out/'wrong-extent.c'
        broken.write_text(self.source.read_text().replace('fd_3D57_07AA[4]','fd_3D57_07AA[5]',1))
        run,_=self.compile(broken,'int main(void) { return 0; }','wrong-extent')
        self.assertNotEqual(run.returncode,0)
        self.assertIn('static assertion failed',run.stderr)

    def test_removed_group_cannot_satisfy_member_assertions(self):
        broken=self.out/'removed-group.c'
        text=re.sub(r'struct __attribute__\(\(packed,aligned\(2\)\)\) semantic_span_options_storage \{.*?\};\nstruct semantic_span_options_storage semantic_span_options = \{.*?\};\n','',self.source.read_text(),flags=re.S)
        self.assertNotEqual(text,self.source.read_text())
        broken.write_text(text)
        run,_=self.compile(broken,'int main(void) { return 0; }','removed-group')
        self.assertNotEqual(run.returncode,0)
        self.assertIn('semantic_span_options_storage',run.stderr)

    def test_options_and_save_roundtrip_with_split_storage_negative(self):
        # This vector is independently observed in both DOS executables, not
        # inferred from whichever native storage arrangement is under test.
        words=[0,1,1,1,1,0]
        siblings=[r for r in self.contract.cross_accesses if r['file']!='src/root/m00DF.c']
        self.assertEqual(len(siblings),29)
        checks='\n'.join(f'if (fd_3D57_07A8[{r["index"]}] != {words[r["index"]]}) return {30+i};' for i,r in enumerate(self.contract.cross_accesses))
        driver='''#include <stdint.h>
#include <stdio.h>
#include <string.h>
extern int16_t fd_3D57_07A8[];
extern unsigned char fd_3D57_0164[32],fd_3D57_0184[160];
extern unsigned char fd_3D57_07AA[4],fd_3D57_07AE[2],fd_3D57_07B0[2],fd_3D57_07B2[4];
struct SaveRec { int16_t size,count; void *data; };
int main(int argc,char **argv) {
 const int16_t dos_options[6]={0,1,1,1,1,0};
 unsigned char bytes[192]; int i;
 struct SaveRec records[2]={{2,96,fd_3D57_0164},{2,6,fd_3D57_07A8}};
 FILE *f;
 if (memcmp(fd_3D57_07A8,dos_options,12)) return 10;
 CHECKS
 for (i=0;i<6;i++) { fd_3D57_07A8[i]=(int16_t)(0x1200+i); }
 if (fd_3D57_07AA[0]!=1 || fd_3D57_07AA[2]!=2 || fd_3D57_07AE[0]!=3 || fd_3D57_07B0[0]!=4 || fd_3D57_07B2[0]!=5) return 11;
 fd_3D57_07B2[2]=0x5a;fd_3D57_07B2[3]=0xa5;
 for (i=0;i<192;i++) bytes[i]=(unsigned char)(i*37+11);
 memcpy(fd_3D57_0164,bytes,32);memcpy(fd_3D57_0184,bytes+32,160);
 for (i=0;i<2;i++) {
   struct SaveRec *p=&records[i];unsigned int n=p->count*p->size;
   unsigned char before[192];memcpy(before,p->data,n);
   f=fopen(argv[1],"w+b");if (!f) return 12;
   if (fwrite(p->data,1,n,f)!=n) return 13;
   memset(p->data,0,n);rewind(f);
   if (fread(p->data,1,n,f)!=n || memcmp(before,p->data,n)) return 14;
   fclose(f);
 }
 if (memcmp(fd_3D57_0184,bytes+32,160)) return 15;
 if (fd_3D57_07B2[0]!=5) return 16;
 if (fd_3D57_07B2[2]!=0x5a || fd_3D57_07B2[3]!=0xa5) return 17;
 puts("33 option literal reads / 29 siblings; dynamic 0..5 write aliases; SaveRec 28+100 block round-trip PASS");
 return 0;
}
'''.replace('CHECKS',checks)
        run,exe=self.compile(self.source,driver,'positive')
        self.assertEqual(run.returncode,0,run.stderr)
        observed=subprocess.run([str(exe),str(self.out/'wire.bin')],capture_output=True,text=True,timeout=15)
        self.assertEqual(observed.returncode,0,observed.stderr)
        # Canonical owners compiled separately reproduce the original defect:
        # zero owners enter BSS, initialized flag owners enter DATA.
        split=self.out/'split-owner-negative.c'
        split.write_text('#include <stdint.h>\n'+'\n'.join(self.contract.definitions[n].rstrip(';')+' = '+self.contract.initializers[n]+';' for n in sorted(self.contract.names)))
        run,exe=self.compile(split,driver,'split-negative')
        self.assertEqual(run.returncode,0,run.stderr)
        negative=subprocess.run([str(exe),str(self.out/'negative-wire.bin')],capture_output=True,text=True,timeout=15)
        self.assertEqual(negative.returncode,10,'split storage must differ from both DOS option/SaveRec100 bytes')


if __name__=='__main__':unittest.main()
