# RTLink distribution search (2026-09-30)

Target: the full circa-1991 Pocket Soft RTLink/Plus distribution that can reproduce
SimAnt's overlay manager and symbol-record ordering. The exact version is unknown;
4.x/5.0 are candidate families. A matching banner or approximate date is not acceptance.
The linker and manager library must have recorded provenance and pinned hashes.

The user authorized searching online and downloading missing historical tools to C:\tools.
No matching new distribution was found or downloaded in this search pass. Existing
RTLink/Plus 6.10 and Clipper 3.11/3.13 remain experimental tools, not a matching toolchain.

## Direct catalogue checks

* Internet Archive advancedsearch API, query `rtlink`: two catalogue hits,
  `msdos_shareware_fb_C501A` (Clipper-related) and `prog21-29` (1993 BBS collection).
  Metadata and the latter's ALLFILES.txt were fetched. The file index identifies only
  RTL610_1.ZIP through RTL610_5.ZIP as RTLink/Plus 6.10: already installed.
  Queries for Pocket Soft, PocketSoft and software titles containing linker provided
  no new period RTLink distribution. A literal slash-containing query was rejected by
  the catalogue parser; it is not counted as a negative result.
* Vetusware's native title search for RTLink returned its empty search form. Native
  manufacturer search for Pocket Soft lists RTPatch 2.12, not the sought linker.
  PocketSoft returned the empty form. This records only the catalogue result, not
  proof that no private or unindexed copy exists.
* Web searches covered RTLink/Plus 4.0/4.01/5.0/5.1, ZIP/disk/download terms,
  RTLINK.EXE, prospective RTL/RTLINK version filenames, WinWorld/Vetusware/Archive,
  Retroarchive/Textfiles/BBS references, and Russian archival queries. No new usable
  full distribution link was located. Some archives were inaccessible to the web tool;
  search-index absence must not be called a complete archive inventory.

Raw read-only search outputs are in ignored `build/workers/takeover/linker-catalogues/`
and linker-catalogues.log. The search script is linker_catalogues.py in the same scratch
directory. Queries/URLs and catalogue outcomes are preserved below in catalogue-search.json.

## Contemporary evidence narrowing the version search

* [Dr. Dobb's January 1991 product notice](https://jacobfilipp.com/DrDobbs/articles/DDJ/1991/9101/9101t/9101t.htm)
  describes RTLink/Plus 4.0 with virtual memory linking and Microsoft C/MASM support;
  4.1 Clipper support is described as forthcoming. This is period evidence for the 4.x
  family, not evidence of the exact SimAnt linker version.
* [April 1992 original sale listing](https://groups.google.com/g/de.markt/c/iGy195InuPI)
  lists RTLink/Plus 5.0 on 3.5-inch disks with Microsoft-language support. It confirms
  that distribution existed by that date, but does not prove December 1991 availability.
* [April 1993 original sale listing](https://groups.google.com/g/cmu.misc.market.computers/c/ufgqdxiqDW4)
  mentions a 4.01-to-5.0 upgrade and retained 3.11 disks. This supports searching 4.01
  and 5.0 separately from Clipper's similarly numbered editions.
* [The developers' 1993 Tekton paper](https://www2.dmst.aueb.gr/dds/pubs/conf/1993-EPY-Tekton/html/tekton.html)
  identifies RTLink Plus 4.01 in its 16-bit Microsoft-compiler builds. It supplies a
  genuine version reference; its executable would not supply a reconstructible linker library.

## Further useful routes

Search file inventories inside older developer/BBS CD collections, using RTL4xx/RTL5xx
and RTLINK variants as filename hypotheses. Avoid downloading large collections without
first finding a relevant index entry. An original disk image collection or retained
vendor distribution would be stronger than extracting runtime bytes from another program.
Contacting vendors/collectors is a separate action requiring explicit user authorization;
no messages were sent during this pass.

## Relevance to matching and SDL3

The missing toolchain blocks the independent final EXE proof: manager/library output and
global ordering remain debt. It does not block exact compiler/module comparisons, and
finding it alone will not solve the remaining game code, declarations or link input order.
SDL3 does not technically depend on the DOS linker. This tree still follows the user's
historical-freeze-before-port rule. Current proof requirements are in docs/level-c-link.md.
