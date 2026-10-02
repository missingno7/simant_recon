#!/usr/bin/env python3
"""Project-local MinGW/SDL3 build. Historical inputs are read-only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from portable.tools.profile_next9 import validate_next9
from portable.tools.profile_next10 import validate_next10

VERSION = "3.4.16"
SDK_SHA = "9828bb735cf8a007bcf0ac5aa9f01f3fcb54b7ca67c932e775c905c5d5053a60"
SDK_URL = f"https://github.com/libsdl-org/SDL/releases/download/release-{VERSION}/SDL3-devel-{VERSION}-mingw.zip"

# Standalone research models have their own differential build commands.
# Link them into the SDL host after their contracts and callers are reviewed.
UNINTEGRATED_MODELS = {
    "portable/ui_model/windows/zoom.c",
    "portable/ui_model/windows/history_render.c",
    "portable/ui_model/dialogs/menu_quit.c",
}


def sdk_path() -> Path:
    return ROOT / "build" / "sdl3-sdk" / f"SDL3-{VERSION}" / "x86_64-w64-mingw32"


def install_sdk() -> None:
    archive = ROOT / "build" / "sdl3-sdk" / f"SDL3-devel-{VERSION}-mingw.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        urllib.request.urlretrieve(SDK_URL, archive)
    actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    if actual != SDK_SHA:
        raise SystemExit(f"SDL3 SDK checksum mismatch: {actual}")
    with zipfile.ZipFile(archive) as z:
        for entry in z.infolist():
            target = (archive.parent / entry.filename).resolve()
            if not target.is_relative_to(archive.parent.resolve()):
                raise SystemExit("Unsafe SDK archive entry")
        z.extractall(archive.parent)
    print(f"Verified SDL3 {VERSION}: {actual}")


def build(main: Path, output: Path, sources: list[Path],
          profile: Path | None = None) -> None:
    sdk = sdk_path()
    if not (sdk / "include" / "SDL3" / "SDL.h").exists():
        raise SystemExit("SDL3 SDK missing; run python portable/build.py --setup-sdk")
    compiler = os.environ.get("SIMANT_CC") or shutil.which("gcc")
    if not compiler:
        candidate = Path("C:/msys64/mingw64/bin/gcc.exe")
        compiler = str(candidate) if candidate.exists() else None
    if not compiler:
        raise SystemExit("MinGW-w64 GCC required; set SIMANT_CC")
    output.parent.mkdir(parents=True, exist_ok=True)
    frozen_check = output.parent / "frozen-oracle-check.json"
    subprocess.run([sys.executable, str(ROOT / "tools/oracle_checkpoint.py"),
                    "--output", str(frozen_check)], cwd=ROOT, check=True)
    if not json.loads(frozen_check.read_text())["ready"]:
        raise SystemExit("Frozen historical input identity check failed")
    core_objects=[]
    core_hashes={}
    extra_flags=[]
    if profile is not None:
        profile=profile.resolve()
        if not profile.is_relative_to(ROOT):
            raise SystemExit("Source profile must be in the workspace")
        provenance=json.loads((profile / "provenance.json").read_text())
        if not all(row.get("compile", {}).get("passed")
                   for row in provenance["modules"]) or not (
                provenance.get("support_compile", {}).get("passed") and
                provenance.get("native_adapter_compile", {}).get("passed")):
            raise SystemExit("Source profile has not passed its complete compile gate")
        selected_provenance = provenance
        next10_input_pins = {}
        if "versioned_profile_extension_next10" in provenance:
            # Validate the complete unchanged parent through every existing
            # gate; separately admit all actual Next10 generated inputs.
            provenance, next10_input_pins = validate_next10(provenance)
        state=provenance["recovered_state"]
        if state["binding_status"] != "COMPLETE" or state["source_data_initializer_mismatches"]:
            raise SystemExit("Incomplete recovered source profile")
        expected={state["path"]:state["header_sha256"],
                  state["source_path"]:state["source_sha256"],
                  provenance["native_adapter_compile"]["path"]:
                      provenance["native_adapter_compile"]["source_sha256"]}
        expected["portable/tools/recover_source.py"] = provenance["generator_sha256"]
        extension = provenance.get("versioned_profile_extension")
        next5 = provenance.get("versioned_profile_extension_next5")
        next6 = provenance.get("versioned_profile_extension_next6")
        next7 = provenance.get("versioned_profile_extension_next7")
        next8 = provenance.get("versioned_profile_extension_next8")
        next9 = provenance.get("versioned_profile_extension_next9")
        if any(key.startswith("versioned_profile_extension_") and
               key not in ("versioned_profile_extension_next5",
                           "versioned_profile_extension_next6",
                           "versioned_profile_extension_next7",
                           "versioned_profile_extension_next8",
                           "versioned_profile_extension_next9") for key in provenance):
            raise SystemExit("Unreviewed recovered profile generation")
        inherited_state = {"recovered_state.h": state["header_sha256"],
                           "recovered_state.c": state["source_sha256"]}
        if next9 is not None:
            extra_expected, inherited_state = validate_next9(provenance)
            expected.update(extra_expected)
        if next8 is not None:
            lowering8 = next8.get("lowering", {})
            if (next7 is None or next5 is None or
                    next8.get("schema") != "simant-recovered-source-profile-extension-v1" or
                    next8.get("id") != "s24-event-code-width-next8-v1" or
                    next8.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION" or
                    next8.get("selected_functions") != ["ProcHistoryEvent"] or
                    next8.get("parent_wrapper") != next7.get("wrapper_path") or
                    next8.get("parent_wrapper_sha256") != next7.get("wrapper_sha256") or
                    lowering8.get("changed_function") != "ProcHistoryEvent" or
                    lowering8.get("source_member_type") != "unsigned (16-bit under MSC large model)" or
                    lowering8.get("host_member_type") != "uint16_t (fixed 16-bit)" or
                    lowering8.get("before_generated_sha256") !=
                        next5.get("parent_module_hashes", {}).get("S24_m39C7")):
                raise SystemExit("Unreviewed history-event word ABI")
            row8 = next((row for row in provenance["modules"]
                         if row["name"] == "S24_m39C7"), {})
            parent8 = next8.get("parent_profile", {})
            if (row8.get("generated") != lowering8.get("path") or
                    row8.get("generated_sha256") != lowering8.get("after_generated_sha256") or
                    parent8.get("changed_modules") != ["S24_m39C7"] or
                    parent8.get("module_count") != 25 or
                    parent8.get("state_hashes") != inherited_state):
                raise SystemExit("History-event lowering changed its profile boundary")
            expected[next8["wrapper_path"]] = next8["wrapper_sha256"]
            for anchor in next8["selected_source"]["function_anchors"].values():
                expected[anchor["source_path"]] = anchor["source_sha256"]
        if next7 is not None:
            lowering7 = next7.get("lowering", {})
            if (next6 is None or next5 is None or
                    next7.get("schema") != "simant-recovered-source-profile-extension-v1" or
                    next7.get("id") != "explicit-yellow-rng-order-next7-v1" or
                    next7.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION" or
                    next7.get("selected_functions") != ["InitYelloAnt"] or
                    next7.get("parent_wrapper") != next6.get("wrapper_path") or
                    next7.get("parent_wrapper_sha256") != next6.get("wrapper_sha256") or
                    lowering7.get("changed_function") != "InitYelloAnt" or
                    lowering7.get("targeted_call_order") != [
                        "SRand16:right", "SRand16:left", "SRand8:right", "SRand8:left"] or
                    lowering7.get("before_generated_sha256") !=
                        next5.get("parent_module_hashes", {}).get("S08_m35F5")):
                raise SystemExit("Unreviewed yellow-ant RNG sequencing")
            row7 = next((row for row in provenance["modules"]
                         if row["name"] == "S08_m35F5"), {})
            if (row7.get("generated") != lowering7.get("path") or
                    row7.get("generated_sha256") != lowering7.get("after_generated_sha256")):
                raise SystemExit("Yellow-ant lowering identity mismatch")
            state_hashes = next7.get("parent_module_hashes_unchanged_except_target", {}).get("state_hashes", {})
            if state_hashes != inherited_state:
                raise SystemExit("RNG lowering changed the parent state profile")
            expected[next7["wrapper_path"]] = next7["wrapper_sha256"]
            for anchor in next7["selected_source"]["function_anchors"].values():
                expected[anchor["source_path"]] = anchor["source_sha256"]
        if next6 is not None:
            lowering = next6.get("lowering", {})
            if (next5 is None or
                    next6.get("schema") != "simant-recovered-source-profile-extension-v1" or
                    next6.get("id") != "explicit-antlion-rng-order-next6-v1" or
                    next6.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION" or
                    next6.get("selected_functions") != ["AddRandAntLion"] or
                    next6.get("parent_wrapper") != next5.get("wrapper_path") or
                    next6.get("parent_wrapper_sha256") != next5.get("wrapper_sha256") or
                    lowering.get("changed_function") != "AddRandAntLion" or
                    lowering.get("targeted_call_order") != [65, 64, 33, 32] or
                    lowering.get("before_generated_sha256") !=
                        next5.get("parent_module_hashes", {}).get("root_m0AD9")):
                raise SystemExit("Unreviewed ant-lion RNG sequencing")
            modules = {row["name"]: row for row in provenance["modules"]}
            row = modules.get("root_m0AD9", {})
            if (row.get("generated") != lowering.get("path") or
                    row.get("generated_sha256") != lowering.get("after_generated_sha256") or
                    any(modules.get(name, {}).get("generated_sha256") != digest
                        for name, digest in next5["parent_module_hashes"].items()
                        if name != "root_m0AD9" and
                        not (next7 is not None and name == "S08_m35F5") and
                        not (next8 is not None and name == "S24_m39C7"))):
                raise SystemExit("RNG lowering changed an unrelated parent module")
            expected[next6["wrapper_path"]] = next6["wrapper_sha256"]
            for anchor in next6["selected_source"]["function_anchors"].values():
                expected[anchor["source_path"]] = anchor["source_sha256"]
        if next5 is not None:
            if (next5.get("schema") != "simant-recovered-source-profile-extension-v1" or
                    next5.get("id") != "selected-S15-newgame-source-next5-v1" or
                    next5.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION" or
                    next5.get("selected_functions") != ["SetDefaultWindows", "NewGame"] or
                    extension is None or
                    extension.get("id") != "selected-control-init-source-next4-v1" or
                    next5.get("parent_wrapper") != extension.get("wrapper_path") or
                    next5.get("parent_wrapper_sha256") != extension.get("wrapper_sha256")):
                raise SystemExit("Unreviewed selected new-game source")
            expected[next5["wrapper_path"]] = next5["wrapper_sha256"]
            for anchor in next5["selected_source"]["function_anchors"].values():
                expected[anchor["source_path"]] = anchor["source_sha256"]
        if extension is not None:
            chain = [extension]
            if extension.get("id") == "selected-control-init-source-next4-v1":
                parent = provenance.get("parent_profile_extension", {})
                if (parent.get("id") != "balloon-source-state-next3-v1" or
                        extension.get("parent_extension_id") != parent.get("id") or
                        extension.get("parent_extension_wrapper_sha256") != parent.get("wrapper_sha256")):
                    raise SystemExit("Recovered profile parent identity mismatch")
                if extension.get("selected_functions") != [
                        "InitTriVars", "SetTriLatPoint", "cvtLevels2IdealCaste",
                        "win_ModeControlClosed", "win_CasteControlClosed",
                        "win_ModeControlChanged", "win_CasteControlChanged", "initControls"]:
                    raise SystemExit("Unreviewed selected controls source")
                chain.append(parent)
            for item in chain:
                if (item.get("schema") != "simant-recovered-source-profile-extension-v1" or
                        item.get("id") not in ("balloon-source-state-next3-v1",
                                               "selected-control-init-source-next4-v1") or
                        item.get("status") != "DIAGNOSTIC_ONLY_NOT_PRODUCTION"):
                    raise SystemExit("Unreviewed recovered profile extension")
                expected[item["base_generator_path"]] = item["base_generator_sha256"]
                expected[item["wrapper_path"]] = item["wrapper_sha256"]
                for field in item.get("added_fields", {}).values():
                    expected[field["source_path"]] = field["source_sha256"]
                    expected[field["layout_path"]] = field["layout_sha256"]
                for anchor in item.get("selected_source", {}).get("function_anchors", {}).values():
                    expected[anchor["source_path"]] = anchor["source_sha256"]
        for row in provenance["modules"]:
            expected[row["source"]]=row["source_sha256"]
            expected[row["generated"]]=row["generated_sha256"]
        expected.update(next10_input_pins)
        provenance = selected_provenance
        for name,digest in expected.items():
            input_path = (ROOT / name).resolve()
            if not input_path.is_relative_to(ROOT):
                raise SystemExit(f"Recovered source input outside workspace: {name}")
            if hashlib.sha256(input_path.read_bytes()).hexdigest()!=digest:
                raise SystemExit(f"Recovered source profile identity mismatch: {name}")
        core_hashes={**expected, (profile / "provenance.json").relative_to(ROOT).as_posix():
                     hashlib.sha256((profile / "provenance.json").read_bytes()).hexdigest()}
        for row in provenance["modules"]:
            obj=output.parent / "core-objects" / (row["name"]+".o")
            obj.parent.mkdir(parents=True,exist_ok=True)
            # Preserve the profile's recorded warning policy for historical
            # bodies. Native adapters and host code keep the strict gate.
            flags=[flag for flag in row["compile"]["command"]
                   if flag.startswith("-W") or flag.startswith("-std=")]
            subprocess.run([compiler,*flags,"-I",str(ROOT),"-I",str(profile),
                            "-c",str(ROOT / row["generated"]),"-o",str(obj)],
                           cwd=ROOT,check=True)
            core_objects.append(obj)
        sources=[*sources,profile / "recovered_state.c",
                 profile / "recovered_native_adapters.c",
                 *(ROOT / "portable/game/recovered" / name for name in
                   ("engine.c","session_bridge.c","audio_adapter.c","nest_adapter.c",
                    "memory_adapter.c", "menu_adapter.c", "control_adapter.c"))]
        extra_flags=["-DSIMANT_ENABLE_RECOVERED_CORE=1","-I",str(profile),"-I",str(ROOT)]
        if next9 is not None:
            # Backing admission is separate from a reviewed save codec and
            # filesystem lifecycle. Standalone codec probes stay unlinked.
            extra_flags.append("-DSIMANT_ENABLE_SAVE_STATE_NEXT9=1")
        if extension is not None:
            # This reviewed extension supplies all twelve omitted source cue
            # fields. Cue submission does not imply a completed frame renderer.
            sources.append(ROOT / "portable/game/recovered/balloon_adapter.c")
            extra_flags.append("-DSIMANT_ENABLE_BALLOON_STATE_NEXT3=1")
            if extension["id"] == "selected-control-init-source-next4-v1":
                extra_flags.append("-DSIMANT_ENABLE_CONTROL_INIT_NEXT4=1")
            if next5 is not None:
                extra_flags.append("-DSIMANT_ENABLE_NEW_GAME_NEXT5=1")
    # Link beside the destination, retaining the last successful executable
    # when compilation or the source-stability check fails.
    fd, temporary_name = tempfile.mkstemp(prefix=output.stem + "-link-",
                                          suffix=".exe", dir=output.parent)
    os.close(fd)
    linked_output = Path(temporary_name)
    command = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
               "-I", str(ROOT / "portable"), "-I", str(sdk / "include"),
               *extra_flags,str(main), *(str(p) for p in sources),*(str(p) for p in core_objects),
               "-L", str(sdk / "lib"), "-lSDL3", "-o", str(linked_output)]
    dependencies = subprocess.check_output(
        [compiler, "-std=c11", "-I", "portable", "-I", str(sdk / "include"),*extra_flags,
         "-MM", "-MT", "SIMANT_DEP",
         *(p.relative_to(ROOT).as_posix() for p in [main, *sources])],
        text=True, cwd=ROOT)
    dependencies = dependencies.replace("\\\n", " ")
    inputs = {main, *sources, Path(__file__).resolve(),
              ROOT / "portable/tools/profile_next9.py",
              ROOT / "portable/tools/profile_next10.py"}
    for block in dependencies.split("SIMANT_DEP:")[1:]:
        for token in shlex.split(block):
            dependency = (ROOT / token).resolve()
            if dependency.is_relative_to(ROOT / "portable"):
                inputs.add(dependency)
    input_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(
        p.read_bytes()).hexdigest() for p in sorted(inputs)}
    input_hashes.update(core_hashes)
    try:
        subprocess.run(command, check=True, cwd=ROOT)
        changed = [name for name,expected in input_hashes.items()
                   if hashlib.sha256((ROOT / name).read_bytes()).hexdigest()!=expected]
        if changed:
            raise SystemExit(f"Sources changed during compilation; rebuild required: {changed}")
        linked_output.replace(output)
    finally:
        linked_output.unlink(missing_ok=True)
    shutil.copy2(sdk / "bin" / "SDL3.dll", output.parent / "SDL3.dll")
    receipt = {"sdl_version": VERSION, "sdl_sdk_sha256": SDK_SHA,
               "sdl_sdk_url": SDK_URL, "compiler": subprocess.check_output(
                   [compiler, "--version"], text=True).splitlines()[0],
               "oracle": subprocess.check_output(["git", "-c",
                   f"safe.directory={ROOT.as_posix()}", "rev-parse",
                   "dos-semantic-oracle-v1^{commit}"], text=True, cwd=ROOT).strip(),
               "frozen_oracle_inputs": {"status": "PASS", "receipt_sha256":
                   hashlib.sha256(frozen_check.read_bytes()).hexdigest()},
               "command": command,
               "installed_output": output.relative_to(ROOT).as_posix(),
               "inputs": input_hashes,
               "sources_stable_during_build": True,
               "compiler_sha256":hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
               "sdl_library_sha256": hashlib.sha256((sdk / "bin/SDL3.dll").read_bytes()).hexdigest(),
               "executable_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    if profile is not None:
        receipt["recovered_core"]={"status":"DIAGNOSTIC_INTEGRATION",
             "profile":profile.relative_to(ROOT).as_posix(),
             "objects":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in core_objects}}
    output.with_suffix(".build.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup-sdk", action="store_true")
    parser.add_argument("--host-test", action="store_true")
    parser.add_argument("--core-profile",type=Path,
                        help="explicit diagnostic source-reuse profile; no default")
    args = parser.parse_args()
    if args.setup_sdk:
        install_sdk()
        return
    if args.host_test:
        build(ROOT / "portable/tests/host/smoke.c",
              ROOT / "build/portable/host-smoke.exe",
              [ROOT / "portable/platform/sdl3/host.c"])
        return
    main_file = ROOT / "portable/main.c"
    if not main_file.exists():
        raise SystemExit("Native startup is still being integrated; --host-test builds the host boundary")
    sources = sorted(p for folder in ("game", "render", "ui_model", "audio", "platform")
                     for p in (ROOT / "portable" / folder).rglob("*.c")
                     if not p.is_relative_to(ROOT / "portable/game/recovered") and
                     not p.is_relative_to(ROOT / "portable/game/save") and
                     p.relative_to(ROOT).as_posix() not in UNINTEGRATED_MODELS)
    build(main_file, ROOT / "build/portable/simant-sdl3.exe", sources,args.core_profile)


if __name__ == "__main__":
    main()
