# Canonical keyboard and mouse interrupt contract

Authority: `src/root/m1B73.asm` at 44de644, SHA-256
`eaf458343b1b00b0dc3ceda81975ce5cb1f8f126c77ff7bfdcc6d150cce492c3`.
Line references below refer to that unchanged file. `W` and `H` mean g_3DB2
and g_3DB4, x/y mean g_9122/g_9124. Arithmetic and shifts have 8086 word/byte
widths; coordinate containment comparisons are signed unless stated otherwise.
PROVEN means an instruction consequence; OBSERVED means a bounded canonical
DOS execution. No whole-program or cycle/interleaving equality is asserted.

## Installation and BIOS relationship (PROVEN)

- 0235, lines 483–525, saves BDA 40:17 NumLock bit20h in g_433E, selects
  INT33 function1Ch BX=2, installs a mouse callback for mask7Fh, then saves
  and replaces INT15, INT09 and INT08. It increments g_53BC. Initial source
  keyboard hook/count enable bytes are 1 (lines218–233); all 128 g_53CD cells
  initially contain80h (line116).
- 02A9, lines528–566, restores the saved NumLock bit without changing other
  BDA17 bits, conditionally restores keyboard vectors if their saved vectors
  are nonzero and depth is nonzero, restores INT08, unregisters INT33 callbacks,
  and clears g_435A. This is a hardware/vector boundary, not a scan-table reset.
- IRQ09, lines1038–1080: disabled or busy paths chain directly. Otherwise
  it sets kbd_busy, reads the raw Set-1 byte from port60h, sets DS and DX to
  DGROUP, switches to the private stack, sets g_432B=1 and calls0747. It
  restores the foreground stack/registers, calls the old IRQ09 with the
  processor's carry flag, then, **if old IRQ returns carry clear**, writes
  BDA40:1C (tail) from40:1A (head): the entire unread BIOS key buffer is cleared.
  Carry set retains the old BIOS result. The hook still processes a scan before
  BIOS updates its modifiers/key buffer. kbd_busy remains set during the old
  handler, preventing a nested INT15 from processing the same scan twice.
- INT15 hook, lines976–1036: CF=0 immediately chains untouched. With CF=1,
  AH other than4Fh, disabled hook or busy hook restores the tested flags and
  chains untouched. An admitted AH=4Fh call takes AL as the raw scan, saves
  AX/DX/DS/flags, sets DS/DX to DGROUP and switches stacks. `mov dl,g_432B;
  xor dl,dl; jne` makes the IRQ-removal branch1019–1032 **unreachable** and
  narrows DX to `DGROUP & FF00h`. It calls0747, discards its saved flag word
  into AX, restores DS/DX/AX, decrements busy (DEC preserves carry) and chains
  old INT15 with the scan processor's carry. It neither directly empties the
  BIOS buffer nor changes the original AX passed onward. The old BIOS/hook
  determines the final return. This is not an AL=0/CF-clear swallowing hook.
- 0A6C, lines1493–1505, resets every table cell to80h and enables kbd_hook_on
  and g_53BD. 0A40, lines1476–1491, calls that reset, disables both flags,
  reads physical mouse buttons with INT33/3, clears shift_state, g_4362/3 and
  g_4368/9. It does **not** reset last_shift, kbd_last_scan, tick_phase or4364.
- 0A30, lines1465–1474, returns `g_53CD[scan] XOR80h` as an unsigned byte in
  AX (nominal down80h/up0). It does not query physical BIOS/SDL state. Native
  retains the logo fix: service host input before reading this canonical table.
  0EEE, lines2047–2054, returns only BDA17 ScrollLock bit10h. The source BIOS
  poll in `src/root/m1F58.asm:68–84` clears NumLock when g_53BD is enabled.

The ordinary hook does not maintain BIOS modifiers itself: oldIRQ09/BIOS owns
BDA17 (bits01/02 right/leftShift,04 Ctrl,08 Alt; lock bits in the high nibble).
The source's separate shift_state bits01/02/80 are not the BIOS flags.036E reads
the complete BDA17/18 word unchanged except its independent bit80 latch ORs
message bit01. Modifier makes therefore enqueue against the **previous** BIOS
flags; later makes/mouse callbacks see the BIOS-updated flags. The observed
Ctrl/P word0104 demonstrates the adjacent byte's significance.

## Every scan byte: transition, event and carry (PROVEN)

0747, lines1086–1180, preserves ES/DI/BX/CX/SI/AX, uses ES=DS, computes
`scan=AL&7Fh`, `release=AL&80h`, and on every exit saves the **raw** AL as
kbd_last_scan. A preceding E0 affects only Shift special handling and CX residue;
there is no distinct extended-key table. E0 itself follows the same scan60h
break logic. E1 similarly follows scan61h break logic and is not recognized as
a multi-byte prefix. The processor assumes DF=0, supplied by its IRQ wrappers.

For a scan whose previous raw byte is notE0, CL is set to2. Left Shift2Ah and
Right Shift36h bypass the table and all key/mouse events: set/clear shift_state
bit1/bit0 on make/break, mask shift_state to3 (also erasing bit7), copy changes
to last_shift, and return carry set (lines1100–1127). Normal Shift queries thus
remain up even while physically held. Immediately afterE0 these same scans
take the ordinary path, including table writes and FA make records.

All other scans compare the table cell to0(make) or80h(break). Equality returns
with CMP's carry clear, so repeated make/break changes neither table nor events
but can clear the BIOS buffer. A new transition writes the table first. A make
always invokes036E before any special dispatch; a break never emits FA.
The make's five register words are:

| AX | CX | DX | BX | ES |
| --- | --- | --- | --- | --- |
| 0000 | previous raw=E0: incoming CX; otherwise `(incoming CX&FF00h)\|2` | IRQ09: DGROUP; admitted INT15: `DGROUP&FF00h`; direct0747: incoming DX | FA00h\|scan | 0000 |

Lines1128–1142 establish these words; **h/v are register residue**, not cursor
coordinates.036E is a no-op on a full ring; scan writes/actions still execute.
Following the make enqueue, AH becomes1 for make and0 for break. The table
544D/5460 (lines117–122) dispatches the following18 scans. Unlisted scans and
the terminal0 return carry set. Listed actions return carry clear for cursor
and mouse actions, carry set for F1 and commands, including rejected commands.
For the first four scans only, Ctrl/Alt (BDA17&0Ch) suppresses **make** action
and returns carry set after FA; their break still clears the motion axis.

| Scan/key | Make action after FA | Break action | ASM lines |
| --- | --- | --- | --- |
|48h Up/KP8|g_4363=`-((H>>7)+1)` narrowed byte|g_4363=0|1262–1272,1283–1285,1327–1329|
|50h Down/KP2|g_4363=`(H>>7)+1` narrowed byte|g_4363=0|1273–1285,1327–1329|
|4Bh Left/KP4|g_4362=`-((W>>7)\|1)` narrowed byte|g_4362=0|1302–1329|
|4Dh Right/KP6|g_4362=`(W>>7)\|1` narrowed byte|g_4362=0|1289–1301,1315–1329|
|47h Home/KP7|x=0 if unsigned x<=8, otherwise6; dispatch movement|none|1338–1348|
|4Fh End/KP1|edge=W-1; x=edge if unsigned edge-8<x, else edge-6; dispatch|none|1349–1361|
|49h PgUp/KP9|y=0 if unsigned y<=8, otherwise6; dispatch movement|none|1362–1372|
|51h PgDn/KP3|edge=H-1; y=edge if unsigned edge-8<=y, else edge-6; dispatch|none|1373–1387|
|4Ch KP5|x=W/2,y=H/2; dispatch movement|**same center/dispatch**|1330–1337|
|52h Insert/KP0|preserve other buttons, set left; callback AL=2 BL=new buttons|clear left; callback AL=4|1388–1397,1453–1463|
|53h Delete/KP.|preserve other buttons, set right; callback AL=8 BL=new buttons|clear right; callback AL=10h|1398–1409,1453–1463|
|39h Space|same left button make as Insert|same left release as Insert|117–122,1388–1397|
|3Bh F1|BDA17&0Fh: shift_state=0; otherwise toggle shift_state bit7; dispatch movement|with modifiers clear shift_state; otherwise no toggle; dispatch|1181–1194|
|19h P|only Ctrl alone: command1|none|1195–1203|
|4Eh KP+|no Shift/Alt: command2 with Ctrl, command6 without|none|1204–1215|
|4Ah KP-|no Shift/Alt: command3 with Ctrl, command7 without|none|1216–1227|
|13h R|only Ctrl alone: command4|none|1228–1236|
|2Ch Z|only Ctrl alone: command5|none|1237–1247|

Arrow make/break resets tick_phase and g_4364 to0; it does not move immediately.
Home/End/PgUp/PgDn break is a consumed carry-clear no-op. F1/commands use the
low BDA17 byte sampled before BIOS handles the current scan. Each accepted
command1–7 enqueues `(AX=8080h|command,CX=BDA17,DX=incomingDX,
BX=F080h|command,ES=0)` (lines1248–1255) after its FA record. The `ror ah,1`
is why AX is8081 etc, not simply command1. Unreachable instructions after
unconditional jumps1193 and1256 are not extra command producers.

Movement dispatch09F7/09FF (lines1430–1451) loads x/y, takes BL from current
g_9120, optionally uses INT33/4 to set driver position when g_4DA4!=0, then
invokes0445 with movement mask1. Button dispatch0A1B (lines1453–1463) invokes
0445 at current x/y without a driver warp. Thus emulated buttons change source
g_9120 but do not change the physical mouse driver's BL. A subsequent real
mouse callback replaces those bits with physical driver buttons.

## Timer-driven cursor and redraw (PROVEN)

INT08 lines852–975 floors countdown after subtracting5, increments private
TickCount only when enabled, always increments16-bit tick_phase, and guards
timer reentry. It switches stacks, allows interrupts, and skips cursor work
while mouse_busy. It chains the old timer after restoring registers/flags.
Redraw (lines888–911) respects display g_3DD4/cursor g_4333 guards: with positive
signed show-level, shift g_4331 right and call04BB if old bit0 was1. Otherwise
shift g_4332 right; if now0, set it1 and call00D9 when g_4331!=0 or4366==0.
00D9 increments4352, clears4332, and only when show-level0 performs aFFFFh
hot-box lookup/show, increments level and clears4331 (lines316–348).

For movement (lines913–962), sum g_4362+4368 and g_4363+4369 as bytes; if both
zero skip. `and bx,bx` clears CF, so its following `jb L0600` is unreachable.
At phases4,10,28 increment byte4364, shift each summed byte left by4364, sign
extend the resulting bytes, add to16-bit coordinates, clamp each signed result
to[0,W-1]/[0,H-1], and call09F7. Since timer_busy is set,0445 marks redraw
pending and still dispatches queue callbacks. There is no repeat-event FA
producer in this path. Phases do not reset after28; only arrow actions reset
them, and the16-bit phase wraps naturally. Countdown's existing native clock
boundary remains in place; this repair adds the omitted cursor half.

## Mouse input and all record words (PROVEN)

INT33 invokes03EE with AX mask, BX current driver buttons, CX/DX absolute
coordinates and SI/DI cumulative mickeys. In normal mode it falls directly into
0445. In mickey mode (lines692–733), arithmetic-shift SI/DI right1, subtract
their previous halved values (432C/432E), save them, add the deltas to x/y, and
clamp x; on negative y the actual instruction is **`xor dx,bx`**, not zeroing
DX. It then compares y to H and clamps only the high side. This odd instruction
must not be silently corrected. Init chooses mickey mode for driver version
0700h or g_432A `/b`/BUG policy, sets driver max rangesW-4/H-4, obtains mouse
button count and initially centers **x=H/2,y=W/2** (lines256–314). Other explicit
center KP5 uses x=W/2,y=H/2.
0218 (lines460–470) forwards CX/DX ratios to INT33/0Fh;0228 (lines472–480)
forwards DX to INT33/13h's double-speed threshold. Those affect driver hardware
motion before03EE, not the source queue masks. Native absolute-coordinate input
does not establish these driver domains equivalent.

0445 lines736–786 checks mouse_busy atomically before any state write, ignores
reentry, writes `g_9120=(mask_low_byte<<8)|buttons_low_byte`, x/y, and switches
to its private stack. A nonpositive signed show-level, busy display, timer or
cursor renderer sets4331=1. Otherwise04BB increments32-bit4356 and, for positive
show-level, hides cursor, finds the cursor hot-box using status/coordinates,
shows it and clears4331 (lines788–820). After this, if `(g_5FF9 & mask)!=0`,
0445 calls the installed near callback g_5FFA. It restores stack/registers and
clears mouse_busy. The source does not unconditionally enqueue a mouse event.

Normal INT33 masks: move1, left make2/break4, right make8/break10h, middle
make20h/break40h; driver buttons are bits1/2/4 respectively. Registration7Fh
admits all; AA3's native/source queue callback mask1Fh excludes middle callbacks
but **does not prevent g_9120/position/cursor writes**.

AA3 (lines1526–1538) clears counts of queues0 and1, sets5FF8=0, selects0CB3 and
5FF9=1Fh.0CB3 (lines1802–1835) walks the three descriptors5484 in order, with
event masksFFh,FFh,1Eh. It skips a descriptor unless its mask intersectsAH.
Within a queue,0CEF (lines1837–1883) checks `(row.word16 & AX)!=0`, then signed
**inclusive** left/top/right/bottom containment. It passes **all five words**
to the far row callback as `(row.word12,row.word14,AX,CX,DX)`, i.e.036E receives
`BX=id,ES=row flags,AX=status,CX=x,DX=y` through030F (lines568–580).030F always
returnsAX=0, stopping the descriptor walk after a matching event enqueue even
when the ring was full. A nonzero callback return continues and reloads status
and coordinates from globals before the next row. Cursor hot-box queries use
the same predicates withBH=0 and do not invoke the row callback.

036E (lines626–689) increments the write index modulo capacity, rejects a next
index equal to read index, and otherwise increments count and writes exactly:

| Byte offset / source field | Word written |
| --- | --- |
|0 / what|**untouched prior slot word**|
|2 / message|BDA40:17 **word** (includes40:18), OR1 if shift_state bit7 set|
|4 / x4|low word of BDA40:6C BIOS clock, independent of private TickCount|
|6 / modLo+modHi|AX|
|8 / h|CX|
|Ah / v|DX|
|Ch / code|BX|
|Eh / xE|ES|

Only after a successful enqueue, ifAX.AH&0Ah is nonzero, shift_state bit7 is
cleared. Full-ring rejection changes none of the ring, slot or latch fields.
The source capacity7 leaves six usable slots (`src/root/m1FD2.c:50–52`).
Dequeue032E (lines588–623) decrements count if available, advances read index
modulo capacity and copies all8 words without clearing the source slot; empty
dequeue returns-1. The record type is Event16 bytes, distinct from hot-box /
Timer rows18 bytes and their count/capacity prefixes.

## Native path audit: differences and disposition

The path is SDL event → `sdl3/host.c:host_poll_event/dos_key` →
`sdl3/input_time_host.c:ingest_host_events` →
`sdl3/m1b73_application_input.c:dispatch_source_event` → scan projection or
mouse callback → descriptor dispatch →030F/036E → canonical Event owner.
Source BIOS reads use the same retained host FIFO;0A30 refreshes that same
owner and reads g_53CD. Sources in this paragraph are under
`portable/whole_program/platform/` except `portable/platform/host.h`.

| Difference at44de644 | Repair / remaining limit |
| --- | --- |
|Scan transition ended at table store; noFA, F0 commands, cursor actions, shift/prefix handling|0747 projection now performs the instruction order and carry result with explicitCX/DX; regression checks each known producer's five words|
|Normal Shift cells incorrectly written;0A30 returned physical cache bool, including while disabled|normalShift special handling;0A30 refresh retained, canonical table XOR80h returned|
|Superseded physical scan cache and forwarding APIs duplicated the canonical owner|cache and both unused query APIs removed; logo GDB regression observes canonicalg_53CD directly|
|SDL repeats dropped before processor, so no original duplicate carry-clear BIOS flush|repeats delivered, duplicate scan emits noFA and requests whole FIFO flush|
|Extended prefix information collapsed into shared scan, affecting fake shifts andCX|HostEvent.extended suppliesE0 to0747 before the key byte; direct raw projection also admits arbitrary prefix scans|
|E0 has a separate IRQ09 carry/buffer effect before the final scan|a carry-clear synthetic prefix empties the prior BIOS FIFO immediately, then the final scan's independent carry result controls its BIOS key. Regression queues A then extendedEnter and retains onlyEnter|
|BIOS FIFO accepted modifier and lock makes; consumed keypad keys and old unread keys retained; capacity128/failure on full|modifier/lock words excluded, processor's carry-clear clears whole unread FIFO after BIOS effects; observed16-word BIOS ring admits15 keys and drops overflow|
|Modifier sampling queried current global SDL state, losing per-event/pre-BIOS order; BDA40:18 dropped|flags are maintained in ingestion order after observer; both bytes sampled by036E, leftCtrl/Alt and lock depressed bits modeled|
|KP+/- and lock keys absent from host mapping|mapped as their Set-1 scans; key/modifier producer roles separated|
|No timer cursor motion/acceleration or deferred source redraw|INT08 cursor projection runs once per elapsed always-on BIOS tick before input ingestion; source-owned phase/step/guard cells generated from ASM directives|
|Warp path duplicated mouse handler, with different hit/show/dispatch order and no busy guards|warp, emulated buttons and physical mouse share0445 callback; cursor rendering precedes selected queue dispatch|
|Renderer/display-busy physical callbacks failed to set pending redraw; timer guard absent|all three guards defer with4331=1; reentrant mouse callback ignores state writes|
|Physical mouse buttons derived fromg_9120, retaining emulated button bits|driver BL state tracked independently and replaces source low bits on physical callbacks|
|Mouse initialization only wrote coordinates; its09F7/0445 status/redraw effects absent|0046 now calls the shared movement callback after the original swapped-axis center/warp|
|Native hook reset did not update canonical g_53BD|hook enable/disable updates both canonical cells and BIOS NumLock policy|
|No DOS interrupted register/segment context|SDL calls projection with CX/DX=0, hence normalFA h=2,v=0. Actual DOS FA containsCH/segment residue. This remains an explicit raw-state difference; direct projection tests admit arbitraryCX/DX. No address cast or guessed segment is introduced|
|BIOS translation not a full PC BIOS|Alt-numpad, Ctrl/Alt function/navigation translations, Pause/E1, PrintScreen/fakeShift streams, CtrlBreak/SysReq, layout/text composition and boot lock state are not established equivalent|
|Host mapping lacks some physical scans|F11/F12, KPdivide/multiply, non-US extra keys, GUI keys, Pause and PrintScreen are dropped; F1–F10 modifier-specific BIOS scan translations and NumLock-on keypad ASCII are still absent. The raw0747 projection accepts all128 scan indices; the SDL mapping domain is narrower|
|SDL physical coordinates instead of INT33 hardware driver|current native supports absolute logical coordinates, not original driver ratio/sensitivity/7.00 mickey quirks or max-rangeW-4/H-4 clamping; middle and source masks are preserved|
|Poll-driven host versus real IRQs|no CPU-cycle timing, asynchronous register snapshots, PIC/IVT/private-stack effects or third-party oldINT15 return policy; batched elapsed timer work cannot recreate arbitrary foreground/IRQ interleavings|
|Extra host event staging ring has512 entries|a burst overflowing this transport queue reports host failure; canonical interrupt delivery has no such staging ring. This bounded polling/burst domain remains unproved even though the separate BIOS key ring now drops overflow correctly|
|Host startup/focus and pointer state differ from a physical PC|physical driver buttons are reconstructed from ordered button transitions, starting at0; a button already held before startup, focus-generated SDL releases, host warp feedback and mouse-motion state snapshots are not established equivalent to DOS hardware delivery|
|Four-word source enqueue calls normalize fifth word|existing native-event-omitted-word issue remains separate and unchanged|

The repaired projections use ordinary readable C over canonical owners and
existing platform services. Canonical source code, oracle lock, linker map and
DOS executable are unchanged. Only reviewed inventory metadata was published
through promote.py, which owns its journal. Old duplicated warp dispatch is
removed in the same change. Remaining raw/hardware limits are recorded in
`portable/platform.json:native-input-hardware-context`; they are not inferred
closed from the bounded tests.

## Validation and canonical DOS observation

`python portable/tests/input_irq/run.py --build build/current/portable` compiles
the actual input services and builder-generated ASM owners against deterministic
hardware controls. It asserts scan/make/break/duplicate state, FA and F0 words,
Shift/E0 differences, physical/emulated buttons and masks, ordering, guard
behavior, keypad positions/acceleration, BIOS filtering and full/wrapped ring.
Queue0's source capacity is4 although its storage has5 rows (lines139–141);
the full-count descriptor regression makes only the fourth usable row match.
The extra declared storage row is preserved without expanding that capacity.
Scan queries cover held normalShift, make/break and disabled-hook cells. The
superseded physical scan cache/API is removed. `run_logo.py` observes canonical
scan cells and covers real SDL
startup input and release. An ordinary Full Game VGA replay passed as well.

OBSERVED canonical DOS with `dos/run.py --build-report
build/current/dos/build-report.json`, fixed200000 cycles/guest clock,
`/dV /s1`, source-built SOURCE.EXE. Ignored exploratory receipts are
`build/workers/p2-kbd/dos-map/`; script `build/workers/p2-kbd/input-map.scr`.
MAP-derived load base8240, DGROUP5C2D, input_queue651A5, descriptor61296:

- At13000.302 ms A make enqueued `(0000,0302,5C2D,FA1E,0000)`, message0,
  tick015Ch, with all five words independently visible in execution-register
  receipt4 and queue writes/dump-a-make. Break produced no second FA.
- Mouse press at14200 ms stores0201 immediately; its registered rectangle
  enqueues `(0201,0104,014A,FF00,0101)` at14200.853 ms, message0,tick0176h.
  At14400 ms release stores0400. In this live dialog callback domain release
  did not match an event producer, so the queue was unchanged.
- Space at15000 ms enqueuesFA39 `(0000,0002,5C2D,FA39,0000)` then the
  registered press callback `(0201,0104,014A,FF00,0101)`, both tick018Ah.
  Break stores0400 and IRQ09 clears BIOS tail to head0026h.
- Extended Right make enqueuesFA4D with unmodifiedCX0147h andDX5C2Dh;
  timer callbacks subsequently store movement status0100. Prefix residue is
  thus corroborated by a second independent producer.
- A second canonical run (`dos-controls/`, `control.scr`) observes Ctrl make
  FA1D with message0000, then P make FA19 and command
  `(8081,0004,5C2D,F081,0000)`, both message0104/tick015Eh. This confirms
  the pre-BIOS ordering and retention of BDA40:18 in the queued message.
  Normal Shift makes no scan-table write or event; its following A queues
  message0002/tick0174h. Extended Insert produces FA52 before its0201
  registered mouse press, and both make/break clear the BIOS tail to head.

These are bounded observations, not a claim that all mouse events enqueue,
all Event.what words are zero, or FA coordinates are unobserved everywhere.

The read-only canonical snapshot was also used for an instruction-level matrix:
128 scan indices × six BDA17 words × make/repeat/break =2304 steps. Explicit
CX=0300h,DX=5C2Dh,clock1234h,x260/y330,empty descriptor queues and mouse mode0
isolate0747 plus its actual036E/0445/0CB3 callees. Every return carry, source
Shift/motion/coordinate field and every Event word matches the native projection
without ignored fields. `portable/tests/input_irq/oracle-matrix.json` retains
the complete control description and expected trace identity; the permanent
test reproduces that semantic matrix without consuming the exploratory snapshot.
The completed snapshots and exploratory Unicorn harness were retired with
`tools/workspace.py` into ignored `to_delete/`. They are never test/build inputs.
DOS BDA dump in
`dos-controls/dump-bda` additionally observes keyboard ring start/end001Eh/003Eh.

The new explicit limitation changes only the input-abi closure metadata in
src/program.json, published through promote.py. Five existing proofs pin that
inventory. Their complete fresh collect() results were deeply compared: only
the six documented inventory-hash fields changed, with every semantic output,
source census and positive/negative control identical. `proof-rebase.json`
records that review; the strict replay comparison code remains unchanged.

Final acceptance (2026-10-07): tools/repository.py passes with no issues;
unmodified tools/validate.py passes the canonical claims, all49 codegen controls,
unit suite (two existing skips), runtime/data verification and compiler-measured
FAR_BSS checks. The final native build compiles170/170 C TUs and75/75 services,
links with no undefined symbols, and passes the input fixture/matrix, all seven
SDL logo cases and Full Game VGA replay with unchanged input pins. Its executable
SHA256 is7e0db4f382148fda4e04cc328f18569959ac5a71de0c53bba53120cfe837ab8a;
report SHA256 is5552254b02a77985e38991ad1c5943d7b8104840998cf4ee126eb84952bcb8c6.
These acceptance results retain every open scope stated above.
