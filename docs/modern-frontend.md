# Modern Windows frontend: semantic map and boundaries

The modern frontend (`--windows`) presents the canonical game through native
windows. Classic (no `--windows`) stays the DOS presentation and gains no modern
features. This page records what the canonical source establishes about the
Game Window (logical window 0, the DOS "edit" view), its camera and the windows
that depend on it, and the boundaries the modern code is built on. Win16 names
are used where the shared formulas prove the pairing (simantw_recon
`tu_antedit_*`, `ToggleMapCursor`, `ScrollEditWindow`); DOS addresses stay the
source of truth.

## Canonical state the Game Window shows

| State | DOS owner | Win16 name | Meaning |
|---|---|---|---|
| camera origin | `fd_50F6_0508` | `MapPnt` | edit view's top-left tile; also saved in games (S09 SaveRec) |
| view size | `fd_50F6_10E0` / `10DE` | `editWidth` / `editHeight` | tiles; `f_0250_0E15`: width floor, height `+1` partial row |
| view rect | `fd_50F6_110C` | `editTileRect` | window 0 object 4, logical screen pixels |
| plane | `MapPlane` | `MapPlane` | 0 yard (edit view shows the surface), 1 surface, 2 black nest, 3 red nest |
| world | `MapA/LifeA [128][64]`, `MapB/R`, `LifeB/R [64][64]`, `PherMap* [64][32]` | same | `[x][y]`; scent overlay `fd_3D57_07BE` |
| tile size | `g_19BE` / `g_19C0` | `tileWidth/Height` | 16 in the supported EGA/VGA modes |
| terrain set | `TERRAINset` | same | `OverlayTileSet`, reloads the resident tiles |
| overview | `fd_50F6_10D2`, `3856/3858`, `38C0`, `fd_3D57_07C8` | `mapTileRect`, `mapXsize/Ysize`, `just`, `MapMode` | map window 0x0100 thumbnail transform and content |
| status message | `g_19C6` / `g_19CA` | | text box over the edit view until a tick |

`MapPnt` is the single game camera. Its readers: the edit draw
(`f_0250_13A6`), the overview cursor (S12 `DrawMapCursor`), edge scrolling
(`f_00F8_01BE`), event-to-tile conversion (S22 `processEdit`, m39C7:98,
m3BBD:61), prox-menu placement (S05:174), the player-ant follow (S05:238),
`TileIsVisible` (only the edit cache, m00F8:248), an idle test (m0E2E:126) and
saved games. Its writers: `f_0250_0D10` (scroll by, Bresenham steps with an
XOR error that under-steps diagonals, then clamp `f_0250_0F2C` and
`UpdateEdit`), `CenterEdit`, edge and Ctrl+arrow scrolling, `SetMapPlane` /
`Goto*` (m015B, including the spider simulation calling `GotoMyAnt`), new game
and load.

## Draw path and cadence

`UpdateEdit` runs after `DoAntSim` in the main loop (every 4th loop at the
fastest speed), on every scroll step and plane change. `f_0250_13A6` draws the
status message, then the spider and balloons (`PreDrawSpider`, `DrawSpider`,
`DrawBalloons`), then each cell through a 40x30 cache (`fd_50F6_15C4` life
codes, `fd_50F6_1114` ground tiles). **It is not pure:** `DrawSpider`,
`DrawPalps` and `DrawCurBalloons` consume the simulation RNG and arm balloon
timers. So the canonical edit view keeps drawing at game cadence into its
hosted planes, and modern rendering never calls it.

Cell decoding is `f_0250_1018` (ground tile `g_94E4`, life code `g_9126`); it
writes only that scratch pair. `f_0250_0721` interprets the life code (bank
object 14 surface / 13 nest, record `code & 0x7f` of 0xC0 bytes, recolour mode
`{0,3,1}[code>>7]`) and the S00 compositor merges the record over the resident
terrain tile (plane `t>>6`, `0xC000 + (t&63)*128`). Ants and objects are part
of the cell; the spider (surface only) and balloons are composites over a
7x7 / balloon cell block.

## Dependent windows

* **Overview (0x0100, shares its place with the yard 0x1900 via `win_Swap`).**
  Its cursor is a 2-pixel XOR outline of `MapPnt x editWidth/editHeight`
  through `mapXsize/mapYsize` plus `just` (nest pad). The map refresh
  (`o12_384C_0B76`, from the main loop) erases and redraws it; a click/drag
  (`MapAreaEvent`) converts the point to a tile and calls `CenterEdit`.
* **Minimap (0x1400)** has its own cursor from the same camera.
* **Plane change** (`SetMapPlane`): edit buttons 8/9/10, map buttons
  0x105..0x108; sets `MapPlane`, `MapMode` (`SetMapModeAnt`, retitles the map),
  re-centres on the plane's saved centre and redraws both views.
* **Geometry change** (`g_62EC` = `f_00BA_01C3` after move/grow/zoom):
  recompute the edit view size (`f_0250_0E15`), invalidate, clamp; re-sync the
  map/yard origin; refresh the mode/caste controls.

## Modern boundaries

```
canonical state ── read-only views (portable/whole_program/modern) ──┐
  world_view: plane, world size, cell codes and pixels, edit view,   │
              overview transform, spider cells, status message       │
  camera:     world <-> view transforms, clamp, zoom at a point,     │
              canonical centre/origin relation                       │
                                                                     ▼
platform/sdl3/modern_game_view: world texture, camera follow, input mapping
platform/sdl3/native_windows:   Game Window = hosted controls + modern map area
platform/window_hosting:        map cursor XOR left to the presentation
```

* **Read-only rendering.** Cells come from `f_0250_1018` with its scratch pair
  restored, pixels from the resident tile cache and the loaded sprite bank
  through the S00 compositor's pure merge (`sim_graphics_tile_compose`, shared
  with the canonical compositor). A cell whose bank is not resident draws its
  ground only. Nothing in the modern path draws into game memory, scrolls or
  touches the RNG; `run_modern.py` checks that the deterministic game state is
  identical with and without the modern Game Window.
* **Not yet modern overlays** come from the hosted canonical view: the spider
  composite's cells (world-anchored) and the status message box
  (view-anchored). Balloons and the lawnmower outline are not shown yet.
* **Camera ownership.** The modern camera (centre, zoom, size) is presentation
  state; `MapPnt` stays the game's. Rules, applied in this order:
  1. a plane change re-centres the camera on the edit view;
  2. any other `MapPnt` change not requested by the modern view (goto, edge or
     key scroll, overview click, follow) moves the camera by the same amount;
  3. a user pan or zoom re-centres the edit view on the camera through
     `f_0250_0D10`, one axis per call, in the game's event pump.
  The overview indicator is drawn from the modern visible area through the
  overview's own transform while the canonical cursor is "shown"
  (`GRectInvOutline(&mapCursorRect)` is mirrored, not drawn).
* **Input.** A map-area point maps to the world through the camera, then to
  the logical point where the edit view shows that world point, so the game's
  own conversion yields the same tile. A click on a tile the edit view does not
  show is held, the pump scrolls the edit view to include it, and the click is
  delivered in order; while the button is held the edit view keeps the pointer
  tile. Points the edit view does not show stay inside its rectangle, so only
  the native client edges reach the DOS screen-edge scroll zone.
* **Size.** The Game Window's native client is the user's (Win16 `WM_SIZE`
  updates the record); the record follows, clamped by the game to the logical
  screen; the map area fills the native client.

## Known gaps

* Balloons, the lawnmower outline and the spider outside the edit view are not
  drawn in the modern map; the minimap (0x1400) cursor still shows the edit
  view; the overview thumbnail and every other window are still hosted VGA.
* An overview click centres the edit view (`CenterEdit`, clamped to the edit
  view's size); a larger modern view follows it by the same delta, so near the
  world edge the clicked point is visible but not centred.
* Held drags that the game services in its own loop without pumping events
  (no `win_Events`) do not get the edit view moved to the pointer.
