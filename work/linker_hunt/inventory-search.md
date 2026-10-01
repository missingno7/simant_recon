# Historical RTLink/Plus inventory search

Purpose: locate a complete Pocket Soft RTLink/Plus DOS distribution near late 1991, including the linker and its manager library. Candidate names include `RTLINK*`, `RTL4xx`, `RTL5xx`, `RTUTILS`, and Pocket Soft product references. A name match alone would still need archive inspection and provenance/hash recording before it could count as a usable toolchain.

## Result

A strong RTLink/Plus 4.00 six-disk candidate was located in a historical BBS archive and preserved at the user's authorized `C:\tools` destination. Its public listing identifies the release as 4.00, but the six included disk images have not been mounted, so the presence and exact filename of the manager library remain unverified. A separate 1989 2.0-era distribution was also preserved as nonmatching archival evidence. Neither archive was executed or tried in a linker run. The findings below are additional to the prior direct-catalogue work in [the takeover search note](../takeover/rtlink-search.md).

## 1991 PC shareware CD inventories

Each item below is an Internet Archive record in the CD-BBS / software collection. For items with external file listings, both `file_listing-ls.txt` and `file_listing-printed.txt` were searched for case-insensitive `RTLINK`, `RTLINKPLUS`, `RTL4*`, `RTL5*`, `RTUTILS`, and `POCKET SOFT`/`POCKETSOFT`. Every listed inventory returned zero target hits.

| Collection | Record and available inventory | Finding |
|---|---|---|
| Hall of Fame CD-ROM, September 1991 (9,965 files) | [item](https://archive.org/details/HallofFameCDROM); [ls listing](https://archive.org/download/HallofFameCDROM/file_listing-ls.txt); [printed listing](https://archive.org/download/HallofFameCDROM/file_listing-printed.txt) | Both text inventories: zero target hits. |
| So Much Shareware!, 1991 | [item](https://archive.org/details/SoMuchSharewareV1_918); [ls listing](https://archive.org/download/SoMuchSharewareV1_918/file_listing-ls.txt); [printed listing](https://archive.org/download/SoMuchSharewareV1_918/file_listing-printed.txt) | Both text inventories: zero. |
| Shareware Solutions CD-ROM, volume 1 no. 2, winter 1991 | [item](https://archive.org/details/SharewareSolutions); [ls listing](https://archive.org/download/SharewareSolutions/file_listing-ls.txt); [printed listing](https://archive.org/download/SharewareSolutions/file_listing-printed.txt) | Both text inventories: zero. |
| 1st Canadian Shareware, August 1991 | [item](https://archive.org/details/1stCanadian); [ls listing](https://archive.org/download/1stCanadian/file_listing-ls.txt); [printed listing](https://archive.org/download/1stCanadian/file_listing-printed.txt) | Both text inventories: zero. |
| Shareware Gold II, 1991 | [item](https://archive.org/details/Gold_II); [ls listing](https://archive.org/download/Gold_II/file_listing-ls.txt); [printed listing](https://archive.org/download/Gold_II/file_listing-printed.txt) | Both text inventories: zero. |
| Phoenix CD 2.0, December 1991 | [item](https://archive.org/details/Phoenix_CD); [ls listing](https://archive.org/download/Phoenix_CD/file_listing-ls.txt); [printed listing](https://archive.org/download/Phoenix_CD/file_listing-printed.txt) | Both text inventories: zero. |
| VGA Spectrum, August 1991 | [item](https://archive.org/details/UGASpectrum); [ls listing](https://archive.org/download/UGASpectrum/file_listing-ls.txt); [printed listing](https://archive.org/download/UGASpectrum/file_listing-printed.txt) | Both text inventories: zero. |
| Night Owl PDSI005, 1991 | [item and ISO](https://archive.org/details/cdrom-nopdsi005) | Searched all 58 embedded `TEXT/DIR*.;1` catalogues and the directory entries in all 80 numbered root directories by HTTP range. Zero target hits. |
| Alternate 1st Canadian Shareware Disc 1991 ISO | [item and ISO](https://archive.org/details/1stCanadianSharewareDisc1991) | No external file listing. Read all 10 category `CATALOG.;1` files and root category directory names; zero target hits. The image has no programming-specific root category. |

The public [CD-BBS archive description](https://philharris.co.uk/AllSystems/archive.org/details/cdbbsarchive.html) explains that these BBS-ready discs carried readable file-description indexes. Its [CD.TEXTFILES catalogue](https://norayr.am/archive/oberon/atari_st/stjo2122/cd.textfiles.com/directory.html) identifies Hall of Fame as a DOS/Windows 3.1 shareware CD from 1991.

## Other historical developer and software inventories

| Collection | Record and inventory inspected | Finding / scope |
|---|---|---|
| PC-SIG Library, 1991 CD (IBM-PC software) | [item and ISO](https://archive.org/details/pc-sig-library-1991-cd) | No external listing. Searched the `INFO` text catalogues and `DOD` catalogue/index data (41 text/index files total), including the professional-software catalogue. Zero target hits. Its numbered `PC_SIGCD/00`–`28` data directories were not individually unpacked. |
| Lion-Share CD-ROM Vol. 1, 1992 (IBM-PC) | [item and CDR](https://archive.org/details/LionShare) | No external file inventory. The archived `.cdr` does not expose an ISO9660 `CD001` volume descriptor in the first megabyte, so no internal index was recovered in this pass. |
| Walnut Creek Source Code CD-ROM, March 1992 | [item](https://archive.org/details/CDROM_March92); [ls listing](https://archive.org/download/CDROM_March92/file_listing-ls.txt); [printed listing](https://archive.org/download/CDROM_March92/file_listing-printed.txt) | The period developer/source-code collection's two full text inventories: zero target hits. |
| Simtel 20 MS-DOS archive, September 1992 | [item and CDR](https://archive.org/details/Simtel20_Sept92) | Searched embedded `INDEX.TXT` (616,005 bytes) and `DIRS.TXT` (8,970 bytes): zero target hits. |
| Simtel 20 MS-DOS archive, December 1992 | [item and ISO](https://archive.org/details/simtel-20-msdos-dec-1992) | Searched embedded `INDEX.TXT` (624,167 bytes) and `DIRS.TXT` (9,017 bytes): zero target hits. |
| Night Owl Shareware Volume 6, 1992 | [item and ISO](https://archive.org/details/cdrom-nopv6) | Searched all 51 embedded `TEXT/DIR*` catalogues and all 51 numbered root directories: zero target hits. |
| 640 Meg Shareware Studio CD-ROM, November 1992 | [item and ISO](https://archive.org/details/The640SharewareStudio) | Searched all 45 split master-list text files under `TEXT` plus `CLANG/FILES.BBS`. No RTLink/Pocket Soft/version-name hit. Generic matches were unrelated QuickBBS/Over_LAZ/Turbo-Pascal overlays. `DLINK.ZIP` is described as Turbo C linked-list functions, not a linker. |
| Powersource PD Shareware, 14,000 programs, 1992 | [item and ISO](https://archive.org/details/PDShareware14000ProgramsPowersource1992) | Searched all 57 `LISTS/*.LIS` file inventories. No RTLink/Pocket Soft/version-name hit. Generic false positives: `MRLINK.ZIP` is a QBBS message reply linker; `BLI151.ZIP` is a Clipper linker update; other lines describe generic overlays. |
| The California Collection (Alpha and Omega), 1992 | [item and CDR](https://archive.org/details/TheCaliforniaCollection) | Searched root `CATEGORI.ES` and `DISKINFO.TXT`, then the 149 text lists inside `DIRS/FILESBBS.ZIP`. No RTLink/Pocket Soft/version-name hit. The generic matches were QuickBBS/Qmodem overlays and `PRTPLUS.ZIP`, a printer utility. |
| Powerpak Gold, 1992 | [item](https://archive.org/details/cdrom-powerpakgold); [ls listing](https://archive.org/download/cdrom-powerpakgold/file_listing-ls.txt); [printed listing](https://archive.org/download/cdrom-powerpakgold/file_listing-printed.txt) | Both text inventories: zero target hits. |
| Gigabyte Shareware, September 1992 | [item](https://archive.org/details/GigabyteShareware); [ls listing](https://archive.org/download/GigabyteShareware/file_listing-ls.txt); [printed listing](https://archive.org/download/GigabyteShareware/file_listing-printed.txt) | Both text inventories: zero. |
| The Ultimate Shareware Collection, 1992 | [item](https://archive.org/details/TheUltimateSharewareCollect); [ls listing](https://archive.org/download/TheUltimateSharewareCollect/file_listing-ls.txt); [printed listing](https://archive.org/download/TheUltimateSharewareCollect/file_listing-printed.txt) | Both text inventories: zero. |
| Shareware Overload, August 1992 | [item](https://archive.org/details/ShartewareOverload); [ls listing](https://archive.org/download/ShartewareOverload/file_listing-ls.txt); [printed listing](https://archive.org/download/ShartewareOverload/file_listing-printed.txt) | Both text inventories: zero. |
| Garbo Software Collection, April 1992 | [item](https://archive.org/details/Garbo); [ls listing](https://archive.org/download/Garbo/file_listing-ls.txt); [printed listing](https://archive.org/download/Garbo/file_listing-printed.txt) | Both text inventories: zero. |
| The Internet Connection, December 1992 | [item](https://archive.org/details/TheInterNetConnection); [ls listing](https://archive.org/download/TheInterNetConnection/file_listing-ls.txt); [printed listing](https://archive.org/download/TheInterNetConnection/file_listing-printed.txt) | Both text inventories: zero. |
| Wildcat! Gold: The Optical BBS, June 1992 | [item](https://archive.org/details/WILDCATGOLD); [ls listing](https://archive.org/download/WILDCATGOLD/file_listing-ls.txt); [printed listing](https://archive.org/download/WILDCATGOLD/file_listing-printed.txt) | Both text inventories: zero. |
| MegaROM-1 Shareware Spectacular, January 1992 | [item](https://archive.org/details/MEGA_ROM_1); [ls listing](https://archive.org/download/MEGA_ROM_1/file_listing-ls.txt); [printed listing](https://archive.org/download/MEGA_ROM_1/file_listing-printed.txt) | Both text inventories: zero. |
| PSL Monthly Shareware CD-ROM, September 1993 | [item and ISO](https://archive.org/details/cdrom-pslmonthly199309) | Read root `FILES.BBS` (205,109 bytes) by range: zero target hits. |
| PC-SIG Library, 13th edition, 1994 | [item and ISO](https://archive.org/details/cdrom-pcsig13) | Searched the professional-category `PRO/DIRPRO.;1` catalogue (55,317 bytes): no RTLink/Pocket Soft/RTL4xx/RTL5xx/RTUTILS entry. The text has generic references to compiling/linking only. |
| Power Programming CD, 1994 | [item and ISO](https://archive.org/details/Power_Programming_1994) | Checked directory names and `00_INDEX.TXT` contents in C, Clipper, assembler tools, compiler management, Microsoft tools, programming utilities, and Turbo C/Pascal sections. No target. `VAL_LINK.ARC` is a third-party experimental C-source linker, not RTLink/Plus. This was a selected-section check, not a full CD catalogue scan. |

## Exclusions and false positives

* The Apple Developer CD series is outside the IBM-PC search scope and remains excluded as directed.
* The Clipper-derived `RTLINKST.COM` found in the previously inspected 1992 shareware collection is a Clipper linker startup stub, not the Pocket Soft linker or manager library. The prior note records its source and exclusion.
* The installed RTLink/Plus 6.10 archives (`RTL610_1`–`RTL610_5`) are the already-known 1993 BBS set and are not a match for the target version.
* Microsoft Programmer's Library, [CDRM-549700](https://archive.org/details/CDRM-549700), is a July 1991 DOS/OS/2 programming-reference database, not a software distribution; its metadata does not expose a file listing. It was not treated as a candidate package.

## DiscMaster BBS archive candidates

DiscMaster's public file index exposed two useful BBS records not returned by the earlier Archive.org/Vetusware catalogue searches.

| Item | Inventory evidence | Outcome |
|---|---|---|
| [Piper's Pit BBS/FTP, `RTLINK40.ZIP`](https://discmaster.textfiles.com/browse/33120/ibm0010-0019/ibm0011.tar/ibm0011/RTLINK40.ZIP) | Item 33120; indexed size 1,660,592 bytes, timestamp 1990-10-01. The archive listing contains `RTLINK1.ZIP` through `RTLINK6.ZIP`. The first part's file comment says RTLink/Plus 4.00, part 1 of 6; the six parts contain `DISK1.DAT` through `DISK6.DAT`, and part 1 also contains `INSTALL.EXE`. | Strong 4.00 full-package candidate. The six-part outer ZIP was downloaded intact to `C:\tools\RTLink-Plus-4.00-DiscMaster\RTLINK40.ZIP`; the sidecar `provenance.txt` records source and SHA-256 `065CC748274ADDD3AC6F4ACA314E67305E5F9A05758DEE9B9CF76A19DE5C69D5`. The disk images remain unmounted; manager-library presence is therefore not yet confirmed. |
| [WaREZ HouZE BBS, duplicate `RTLINK40.ZIP` record](https://discmaster.textfiles.com/browse/29990/wbiz0060-0069/wbiz0068.tar/wbiz0068/RTLINK40.ZIP) | Item 29990; indexed size 1,661,684 bytes, timestamp 1990-09-30. | Independent listing for a same-named 4.00-era archive; not downloaded. |
| [WaREZ HouZE BBS, `RTLINK.ZIP`](https://discmaster.textfiles.com/browse/29989/wbiz0050-0059/wbiz0056.tar/wbiz0056/RTLINK.ZIP) | Item 29989; indexed size 376,966 bytes, timestamp 1990-07-24. Its two nested archives contain 11 and 60 files. The first includes `RTLINK.EXE` dated 1989-08-08 and `OVLMGR.ASM` dated 1989-08-04; the README refers to the 2.0 manual and features from 2.03 onward. | Useful but nonmatching 2.0-era package; preserved at `C:\tools\RTLink-Older-2.x-DiscMaster\RTLINK.ZIP` with provenance and SHA-256 `D2FBDE3E948C366217ADA48EC4A46200C37E82B4E73DE8C1B18712C6CF35CE96`. |

The 4.00 candidate was enumerated in memory only: the outer ZIP contains six nested part ZIPs, each with one `DISK#.DAT`, and part 1 also has `INSTALL.EXE`. The `DISK#.DAT` entries use a compression method unsupported by the built-in .NET ZIP reader, so this pass did not list files inside the disk images. No code or binary was added to the Git tree.

## Remaining concrete leads and limits

The 4.00 BBS distribution is the best concrete result, but the manager library inside its disk images still needs inventory confirmation before it can be called a complete match for the requested toolchain. The user's late-1991 build may instead require a later 4.01 or 5.0 release; the exact original SimAnt linker version remains unconfirmed. The PC-SIG 1991 numbered ZIP member-name catalogs are now scanned, though their payloads were not extracted. The 1992 Lion-Share CD remains an unresolved inventory gap. No vendor, collector, or other person was contacted.

The only downloaded payloads are the two intact candidate ZIP archives listed above in `C:\tools`, outside Git; each has a provenance and SHA-256 sidecar. The search helper scripts used for range-only ISO inventory inspection are in `build/workers/linker_hunt/`; they contain no recovered software payloads.

## PC-SIG 1991 numbered ZIP catalog pass (2026-10-01)

The previously uninspected numbered-data-directory gap on the [PC-SIG 1991 CD image](https://archive.org/details/pc-sig-library-1991-cd) is now closed at the archive-catalog level. PCjs identifies its 10th Edition as September 1991, covering disks 1–2804, and documents that the 9th and later editions stored diskette contents as ZIP files ([PC-SIG ZIP history](https://www.pcjs.org/blog/2023/04/06/)). Its collection notes identify disks 2486–2804 as coming from the 10th Edition and also warn that the online description database is incomplete ([PC-SIG collection notes](https://www.pcjs.org/software/pcx86/sw/misc/pcsig/)).

Using HTTP range reads against `PC_SIG_10TH.iso` (414,232,576 bytes), the directory walk found 321 directories, 2,910 files and 2,804 numbered disk ZIPs under `PC_SIGCD/00`–`PC_SIGCD/28`. The names were exactly `DISK0001.ZIP` through `DISK2804.ZIP`, with no gap or duplicate. The scan read only each ZIP's trailing central-directory area (up to 65,557 bytes) and matched member names; it did not download or extract complete packages. All 2,804 catalogs parsed successfully after retrying one transient HTTP reset for `DISK2402.ZIP`; its 13 entries were unrelated drawing/shareware files.

The broad member-name pass looked for RTLink, RTL, RTUTILS, Pocket Soft, overlay, and linker strings. Its substring-only collisions were ordinary names such as `TURTLE.LSP`, `SRTLAB.EXE`, `STARTLOG.COM`, `PARTLIST`, and `PRTLABEL.*`. A second full pass added short manager-library/source forms such as `OVL*.LIB`, `OVL*.ASM`, `OVL*.OBJ`, `OVL*.INC`, and `OVL*.H`; it found only `OVERLAY.EXE` in `PC_SIGCD/08/9/DISK0897.ZIP`. That generic filename is not a Pocket Soft/RTLink identifier or an overlay-manager library/source match, and the package was not downloaded. No RTLINK/Plus 4.x/5.0 archive, `RTUTILS`/`RTLUTILS` library, `OVLMGR` source, or other matching manager-library filename was found in this CD inventory.

Reproducible scratch records (no software payloads):

| File | SHA-256 |
|---|---|
| `work/linker_hunt/pc-sig-1991-archive-scan.txt` (ISO directory names and numbered ZIPs) | `DE1DC0D812A3AF4A66CC3CD498C3061961EBECDFFC9E6F334C740F188E0AA5C2` |
| `work/linker_hunt/pc-sig-1991-zip-catalog-scan.txt` (first central-directory pass; one transient request reset) | `CE9067F2BC3E38B5D745FD0C1ABB0EDEBFAD433657BCFEC369C59C026F356DD3` |
| `work/linker_hunt/pc-sig-disk2402-retry.txt` (recovered catalog for the reset request) | `BE82E592D93A50CBA7B96D34E13891E4994834388B0383891FDA026108C50777` |
| `work/linker_hunt/pc-sig-1991-zip-catalog-expanded.txt` (expanded full pass; zero catalog errors) | `4A4EFEAC617BCBC50C4373AFF3DCBB1301CBBB439257BEF7F252C5494238D43D` |
| `build/workers/linker_hunt/scan_pcsig_zip_catalogs.py` and `build/workers/linker_hunt/probe_pcsig_disk2402.py` (read-only range scan helpers) | scratch scripts; no payloads |

This rules out a straightforward product/member-name listing on the 1991 PC-SIG CD, including its 1991-added disks. It cannot rule out a tool hidden under unrelated filenames or absent from the disc; the prior DOD/INFO catalogue keyword scan also returned no target entry. No new downloads or external contacts were made.

## Follow-up checks: alternate release names and 4.00 payload evidence (2026-09-30)

The DiscMaster archive-family search was extended beyond ZIP to the filename variants
`RTLP* | RTLINK5* | RTLINKPLUS*`; it returned zero results. A ZIP-only filename search
for `RTLP* | RTLINK5* | RTLINKPLUS* | RTLINKP*` also returned zero. These checks do
not establish that every historical archive is indexed, but they found no 4.01/5.0
archive in the indexed BBS/CD/FTP set. The older wildcard checks `RTLINK*` and
`RTL4* | RTL5*` are recorded in the task handoff; the 4.00 duplicate and older 2.x
package remain the only relevant standalone archive families found there.

Static inspection of the preserved 4.00 files (no execution) adds limited package
inventory evidence. The part-1 ZIP stores `INSTALL.EXE` (32,641 bytes, DOS timestamp
1990-09-14) and `DISK1.DAT`. A scratch extraction of the installer is at
`build/workers/linker_hunt/static-analysis/INSTALL.EXE`, SHA-256
`AE1508859BFD83F3EE97E175699501D39E470F2BCFA98117D9B13F92C43742D8`. Its strings
identify “Pocket Soft Installation Utility Version 4.00,” use `%c:disk%d.dat` image
files, perform header/checksum checks, and mention files spanning distribution disks.
The raw `DISK1.DAT` is not recognized as a standard archive by 7-Zip; its SHA-256 is
`2FA153089E80B70373D729ED64B9C1D890E6E98DB771A74D4506F25D25AB97C6`.

ASCII strings in the six `DISK#.DAT` payloads include linker-support-looking names
`RTLINK.HLP`, `RTLINKST.COM`, `RTLUTILS.LIB`, and `OVLMGR.ASM`, plus utilities, source,
link scripts and examples. These are raw string observations rather than a decoded
file manifest: several have leading non-filename bytes in the image, so exact path,
spelling and contents remain unverified. `RTLUTILS.LIB` has separate Clipper
references as an automatically loaded reserved RTLink library, but that alone does
not identify it as the overlay manager library needed here. `OVLMGR.ASM` might be
manager source or a sample; no source was extracted. No public document found in this
pass explains the `.DAT` image format or confirms the 4.00 manager library contents.

A 1991 Clipper help copy named `RTLINK.HLP` is a Clipper 5.0 bundled help file and was
excluded: its adjacent files are Clipper `RTLINK.EXE` and `RTLINKST.COM`, not a
standalone Pocket Soft RTLink/Plus 4.01 or 5.0 package. Exact-version public searches
again surfaced 1992 5.0 sale and 1993 4.01-to-5.0 upgrade references, not a download.
The 4.00 archive and provenance sidecar remain unchanged; no newer candidate was
identified or downloaded.

Extracted DAT inspection-copy hashes (the outer archive and provenance remain untouched):

| Payload | SHA-256 |
|---|---|
| `C:\tools\RTLink-Plus-4.00-DiscMaster\disks\DISK1.DAT` | `2FA153089E80B70373D729ED64B9C1D890E6E98DB771A74D4506F25D25AB97C6` |
| `C:\tools\RTLink-Plus-4.00-DiscMaster\disks\DISK2.DAT` | `D261910D501C29CD6BEE148CC92E287F1704D4075AAA14FFFADFADC36D009E8B` |
| `C:\tools\RTLink-Plus-4.00-DiscMaster\disks\DISK3.DAT` | `CCCBD43D49BC5843C5D701C712FE97B7A2BA62391319B522363B123049FA9176` |
| `C:\tools\RTLink-Plus-4.00-DiscMaster\disks\DISK4.DAT` | `1D5BCE0482E7D8A1A8A393477A0AE36134D94B58DE90D89AE8725BB04BECB293` |
| `C:\tools\RTLink-Plus-4.00-DiscMaster\disks\DISK5.DAT` | `8CC6366B13E9121730DDA452F2AAAA195BE95BF66CA44AF4786A28DFC3AA5A1C` |
| `C:\tools\RTLink-Plus-4.00-DiscMaster\disks\DISK6.DAT` | `750B1B79489404D163F0B2762F0C2822521D42A7A2DD7EB14947556D2D845843` |

## Installer and linker follow-up (2026-10-01)

The previous untested-payload blocker is resolved. The vendor installer extracted
all six disks under headless DOSBox-X with only a fresh scratch directory mounted;
all installer file checksums passed and installation completed. The clean DOS,
source, documentation and examples payload contains 181 files. The installed,
hash-pinned rtlink400 profile successfully links the current diagnostic collection.

The stock 4.00 RELOAD manager uses 16-byte section records, whereas SimAnt uses
18-byte records. Its intercept offset is 033A rather than 0529. It is an experimental
instrument, not the matching original manager. Both 4.00 and the 6.10 control link
99 real objects plus 67 code stubs; 13 of 14 unstubbed-overlay relocation sets match,
but only S21's order matches and all raw images differ. No exact-version conclusion
follows beyond excluding this stock 4.00 manager format.

Reproducers, installer transcript, payload hashes, library-public inventory and
paired trial summaries: [work/takeover/rtlink400/README.md](../takeover/rtlink400/README.md).
No tool binaries or vendor sources are committed. The exact historical linker and
independent whole executable remain open.
