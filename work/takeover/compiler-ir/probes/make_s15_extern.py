from pathlib import Path

root=Path(__file__).resolve().parents[4]
base=root/"work/takeover/full-search/o15_384C_0239/best.c"
out=root/"build/workers/compiler_ir/sources/s15-top-extern-plus-one.c"
source=base.read_text(encoding="latin1")
needle="typedef char far * far *Handle;"
assert source.count(needle)==1
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(source.replace(needle,needle+" extern int far g_hardtail_probe;",1),encoding="latin1")
print(out)
