# Language string-list pointer storage review (candidate)

This audit covers five FAR_BSS globals assigned by PrepareStrings in
src/root/m075B.c: AdviceStrs, fd_50F6_02BA, fd_50F6_0324,
fd_50F6_0328, and fd_50F6_0368. The probe derives its source set from the
canonical manifest plus the strict 29-source behavioral index (127 canonical
modules, 156 unique source paths). It does not use the DOS build report, an
original executable, or original objects.

## Grounded pointer shape

The owner declares typedef char far * far *StrList and each of these names as
StrList far. PrepareStrings assigns the results of LoadStringAnt for resource
IDs 1020, 1050, 1001, 1900, and 1800 respectively. This establishes a
far-stored far pointer to a row of far string pointers. The four-byte storage
shape is independently confirmed by MSC 6.00AX OMF: exactly five far COMDEFs,
each count 4, element size 1, total length 4, with no initialized data,
functions, public symbols, or fixups. This is a source-functional data provider
proposal only; it does not claim the historical COMDEF translation unit,
member order, or link order.

Registered symbols place the objects at 50F6:0360, 02BA, 0324, 0328,
and 0368. The registry has no same-base alias or interior name within any
four-byte object. Across the complete scan there is no direct address-of
escape, no write outside PrepareStrings, and no SaveRec view. Consumers read
indexed row entries. AdviceStrs additionally has void far * far * far
consumer declarations in src/root/m0E2E.c, src/root/m1383.c, and the
registered LessonDone behavior source; this is a pointer element base-type
view, not a separate registered object alias.

Observed index expressions are examples only: AdviceStrs[0..5],
fd_50F6_02BA[graph], fd_50F6_0324[fd_50F6_0EAC],
fd_50F6_0328[level], and fd_50F6_0368[13..18]. The actual resource count
bytes and all consumer index domains remain unresolved. No fixed table extent
is inferred from these pointers or observed indices.

## Setup and lifetime limits

PrepareStrings is called directly from initStuff (m075B.c:27) and writes
the five globals at lines 73, 75-76, and 88-89. For each resource,
LoadStringAnt (m075B.c:111 onward) calls db_LoadObject(object, 4). A
missing object returns null after a warning; PrepareStrings stores it without
a null check. Otherwise the loader skips a leading byte, reads the raw count,
allocates (count + 1) * 4 bytes for the row pointers, points each row entry
into the loaded resource payload, and writes a null sentinel. The table
allocation handle is not retained, and this path has no matching unlock or
free. A repeated PrepareStrings call would replace the globals without
releasing prior tables; the scan found one direct call site but does not prove
the routine cannot be called again indirectly.

The row pointers refer into database resource payloads rather than copied
strings. The source scan found no direct purge call for these five literal
resource IDs, but db_CloseDataBase in src/root/m1A53.c:159 closes handles
and purges the cache; the sources do not establish payload validity across
database/cache invalidation. Indexed consumers do not provide a universal null
guard. These are explicit lifetime and failure-path limits.

## Guarded controls

language-pointer-owner-probe.py builds the candidate and independent
typed-word and BYTE-view consumers with MSC 6.00AX, then runs actual MSC
startup under RTLink 4.00 and 6.10. The fixture contains no game functions,
stubs, resource blocks, or oracle inputs. It checks the candidate pointer
representation using addresses of test-owned pointer rows; it never
dereferences production table contents.

Both linkers produced the expected outcomes (16/16): typed far-pointer
zero/word-half/write and independent BYTE round trips passed. The initialized
nonzero owner failed each zero-startup check. Near outer-pointer, near row
pointer, direct-pointer-depth, and eight-byte-array views each failed the
candidate type/extent predicate. The wrong-array owner was separately checked
as five eight-byte far commons; the initialized contrast contains data and
fixups. The contract is limited to candidate test storage representation and
source pointer type, not the contents or fixed extent of loaded language rows.

## Reproduction and evidence

Run python build/workers/dos_language_pointer_owners/language-pointer-owner-probe.py.
The source pins, all 16 linker/case results, generated objects, fixture files,
and compiler/linker/runtime pins are in
build/workers/dos_language_pointer_owners/run-v1/report.json. The source set
and every identifier hit are recorded there. Historical COMDEF ownership,
resource table counts, index bounds, and guaranteed resource-payload lifetime
remain unclaimed.
