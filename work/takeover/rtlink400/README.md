# RTLink/Plus 4.00 extraction and trial (2026-10-01)

The six-part archive is now extracted and tested. It remains an experimental
instrument: its stock RELOAD manager has 16-byte section records, while SimAnt has
18-byte records, and its intercept offset is 033A rather than SimAnt's 0529.
The exact original linker version and independent whole build remain unresolved.

## Provenance and extraction

The unchanged archive C:/tools/RTLink-Plus-4.00-DiscMaster/RTLINK40.ZIP has SHA-256
065cc748274addd3ac6f4aca314e67305e5f9a05758dee9b9cf76a19de5c69d5.
Earlier acquisition provenance is in work/linker_hunt/inventory-search.md and its
C:/tools sidecar. install.py verifies the archive, installer, 7-Zip extractor and
DOSBox-X identities, extracts six nested disk images, and runs the vendor installer
headlessly with only a fresh worker directory mounted. No host drive is exposed.
The installer completed with all file checksums OK. install.log and
payload-manifest.json record the clean DOS/source/documentation/examples installation
(181 files). No historical binaries or vendor sources are committed here.

```
python work/takeover/rtlink400/install.py build/workers/NAME/rtlink400-install
python work/takeover/rtlink400/manager_inventory.py build/workers/NAME/rtlink400-install/dest
```

The installed profile rtlink400 points to
C:/tools/RTLink-Plus-4.00-DiscMaster/installed/dest. Its four linker/support pins
match the fresh extraction. That earlier installation additionally contains two
OS/2 execution files from an initial installer-input trial; these are not link inputs.
The library inventory has 31 members. Member 2 is the 2,566-byte RELOAD manager
with $$RTLOVLINITR; manager-inventory.json records its segment/public inventory.
This inventory is descriptive and supplies no reconstruction claim.

## Trials and tooling fix

Both profiles link the same current collection: 99 real objects, 67 explicitly
labelled code stubs (106,081 bytes), and unresolved __acrtused. Both finish with
three linker warnings. 400-trial.json / 610-trial.json retain inputs and stub labels;
400-T.LNK / 610-T.LNK are the generated diagnostic scripts.

```
python tools/rtlink.py build/workers/NAME/rtlink400 --profile rtlink400 --jobs 6
python tools/rtlink.py build/workers/NAME/rtlink610 --profile rtlink610 --jobs 6
```

4.00 defaults to positional command syntax. run_link now writes the vendor-documented
RTLINK.CFG setting `SYNTAX = FREEFORMAT`, which also succeeds under the 6.10 control.
The trial summarizer formerly assumed 18-byte records and fixed offsets from
$$OVLINFO; it now follows the count/table pointers and record size in $$OVLPBLOCK.
16-byte records derive image bounds from the next file position; 18-byte records use
their file-length word. The final three unwritten padding bytes in the 6.10 resident
section are explicitly reported. No bytes are manufactured or omitted from comparison.
Length differences are counted as well as differing bytes. Four format tests cover
both formats, alternate pointers, truncation, unsupported formats and partial EOF fill.

Both summaries have 14 overlay images without trial code stubs. Thirteen relocation
sets agree; S04 differs. Only S21's relocation order agrees. All fourteen raw images
differ, including rebased fixup fields; S04 is also 32 bytes shorter. The results are
diagnostic, never acceptance. 400-summary.json / 610-summary.json preserve the full
comparison. The original's 18-byte format excludes this stock 4.00 manager; it does
not establish which later version or customization was used.

Full validation and the identical hybrid hash passed; transcripts are retained in
../blockers/. No canonical sources, manifest, oracle lock or promotion journal changed.
