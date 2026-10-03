set pagination off
set confirm off
set print thread-events off
set substitute-path D:/Prog/simant_recon D:/Prog/simant_recon/build/whole-application-v13/inputs
set cwd D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5
set args --headless --smoke-ms 30000 --frame D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/frame-v13-present.bmp --seed 1 /dV --assets D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-assets --bios-fonts D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/isolate5/runtime-bios-fonts --input-script D:/Prog/simant_recon/portable/tests/whole_program/application_input/quick-game-vga-v1.txt
python exec(open(r"D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\probe_v13_present.py", encoding="utf-8-sig").read())
run
