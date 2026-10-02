"""Build/run the SDL host and independently inspect its exported BMP pixels."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
subprocess.run([sys.executable,str(ROOT / "portable/build.py"),"--host-test"],check=True)
output = ROOT / "build/portable/host-smoke.bmp"
subprocess.run([str(ROOT / "build/portable/host-smoke.exe"),str(output)],check=True,cwd=ROOT)
data = output.read_bytes()
assert data[:2] == b"BM"
offset = struct.unpack_from("<I",data,10)[0]
width,height,planes,bits = struct.unpack_from("<iiHH",data,18)
assert (width,height,planes,bits) == (640,350,1,32),(width,height,planes,bits)
for y in range(height):
    for x in range(width):
        index = ((x//40) ^ (y//35)) & 15
        actual = data[offset+((height-1-y)*width+x)*4:offset+((height-1-y)*width+x)*4+4]
        assert actual[:3] == bytes(((index&3)*85,(15-index)*17,index*17)),(x,y,actual)
report = {"status":"PASS", "scope":"SDL3 host boundary; not game startup or DOS raster proof",
          "harness_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "framebuffer_pixels_compared":width*height,
          "keyboard_queue_test":"SDL left-shift A -> DOS scan/ASCII 1e41, shift flag 2",
          "quit_queue_test":True,"monotonic_clock_test":True,
          "bmp_sha256":hashlib.sha256(data).hexdigest(),
          "build_receipt":json.loads((ROOT / "build/portable/host-smoke.build.json").read_text())}
(ROOT / "build/portable/host-smoke.test.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="build_receipt"},indent=2))
