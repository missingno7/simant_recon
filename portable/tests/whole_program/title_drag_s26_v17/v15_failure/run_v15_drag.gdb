set pagination off
set confirm off
set print thread-events off
set substitute-path D:/Prog/simant_recon D:/Prog/simant_recon/build/whole-application-v15/inputs
set cwd D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/v15_title_drag
set args --headless --smoke-ms 30000 --frame D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/v15_title_drag/frame.bmp --seed 1 /dV --assets D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/v15_title_drag/runtime-assets --bios-fonts D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/v15_title_drag/runtime-bios-fonts --input-script D:/Prog/simant_recon/build/workers/whole_runtime_flow_review/v15_title_drag/quick-game-title-drag-v1.txt
python exec(open(r"D:\Prog\simant_recon\build\workers\whole_runtime_flow_review\v15_title_drag\probe_v15_drag.py", encoding="utf-8-sig").read())
run
