/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_PICTURES_IDS_H
#define SIMANT_PICTURES_IDS_H

/* PictureDialog receives no picture when this argument is zero. Evidence: src/ui/scenario_dialogs.c:438
 * (PictureDialog). */
#define PIC_NONE 0x0

/* Bitmap used by DrawSpider; frame bases are additive, not window IDs. Evidence: src/ui/edit_view.c:1135
 * (DrawSpider); HCEGANT kind 2 ID 0x3e8. */
#define PIC_SPIDER_DIRECTION_FRAME_BASE 0x3e8

/* Terrain tile-set selector used by MakeYardPatch; not a kind-2 bitmap ID. Evidence: SHARED kind 9 ID
 * 0x3e8; src/simulation/map_patches.c:397 (MakeYardPatch); src/ui/edit_view.c:177 (OverlayTileSet). */
#define TILESET_YARD 0x3e8

/* Terrain tile-set selector used by MakeHousePatch; not a kind-2 bitmap ID. Evidence: SHARED kind 9 ID
 * 0x3e9; src/simulation/map_patches.c:61 (MakeHousePatch); src/ui/edit_view.c:177 (OverlayTileSet). */
#define TILESET_HOUSE 0x3e9

/* Bitmap used by DrawSpider; frame bases are additive, not window IDs. Evidence: src/ui/edit_view.c:1135
 * (DrawSpider); HCEGANT kind 2 ID 0x41a. */
#define PIC_SPIDER_CYCLE_FRAME_BASE 0x41a

/* Bitmap used by DrawMapSpider; frame bases are additive, not window IDs. Evidence: src/ui/map_window.c:605
 * (DrawMapSpider); HCEGANT kind 2 ID 0x44c. */
#define PIC_MAP_SPIDER_FRAME_BASE 0x44c

/* Bitmap used by DrawMapFoot; frame bases are additive, not window IDs. Evidence: src/ui/map_window.c:633
 * (DrawMapFoot); HCEGANT kind 2 ID 0x4b0. */
#define PIC_MAP_FOOT_FRAME_BASE 0x4b0

/* Bitmap used by DrawMapFoot; frame bases are additive, not window IDs. Evidence: src/ui/map_window.c:633
 * (DrawMapFoot); HCEGANT kind 2 ID 0x4ba. */
#define PIC_MAP_FOOT_ALTERNATE_BASE 0x4ba

/* Bitmap used by DrawSimBird; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:363
 * (DrawSimBird); HCEGANT kind 2 ID 0x4e2. */
#define PIC_YARD_BIRD_FRAME_BASE 0x4e2

/* Bitmap used by DrawForSale; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:416
 * (DrawForSale); HCEGANT kind 2 ID 0x4ec. */
#define PIC_YARD_FOR_SALE 0x4ec

/* Bitmap used by DrawSimCat; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:389
 * (DrawSimCat); HCEGANT kind 2 ID 0x514. */
#define PIC_YARD_CAT_FRAME_BASE 0x514

/* Bitmap used by initControls; frame bases are additive, not window IDs. Evidence:
 * src/ui/colony_controls.c:518 (initControls); HCEGANT kind 2 ID 0x578. */
#define PIC_TRIANGLE_KNOB 0x578

/* Bitmap used by YellowHelp; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:1037 (YellowHelp); HCEGANT kind 2 ID 0x1195. */
#define PIC_YELLOW_ANT_HELP 0x1195

/* Bitmap used by YellowHelp; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:1037 (YellowHelp); HCEGANT kind 2 ID 0x1197. */
#define PIC_YELLOW_QUEEN_HELP 0x1197

/* Bitmap used by YellowHelp; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:1037 (YellowHelp); HCEGANT kind 2 ID 0x1199. */
#define PIC_SPIDER_HELP 0x1199

/* Bitmap used by EditToolsMenu; frame bases are additive, not window IDs. Evidence:
 * src/ui/editor_menus.c:63 (EditToolsMenu); HCEGANT kind 2 ID 0x13ec. */
#define PIC_EXPERIMENT_TOOL_ICON_BASE 0x13ec

/* Bitmap used by win_DrawMapWindow; frame bases are additive, not window IDs. Evidence:
 * src/ui/map_window.c:585 (win_DrawMapWindow); HCEGANT kind 2 ID 0x13f3. */
#define PIC_NORMAL_TOOL_ICON 0x13f3

/* Bitmap used by SetYardMode; frame bases are additive, not window IDs. Evidence:
 * src/ui/view_commands.c:158 (SetYardMode); HCEGANT kind 2 ID 0x1b58. */
#define PIC_YARD_MODE_BACKGROUND_BASE 0x1b58

/* Bitmap used by win_DrawYardWindow; frame bases are additive, not window IDs. Evidence:
 * src/ui/yard_window.c:187 (win_DrawYardWindow). */
#define PIC_YARD_DRAW_BACKGROUND 0x1b5a

/* Bitmap used by DrawRain; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:599
 * (DrawRain); HCEGANT kind 2 ID 0x1b5d. */
#define PIC_YARD_RAIN 0x1b5d

/* Bitmap used by DrawSwarm; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:633
 * (DrawSwarm); HCEGANT kind 2 ID 0x1b5e. */
#define PIC_YARD_BLACK_SWARM 0x1b5e

/* Bitmap used by DrawSwarm; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:633
 * (DrawSwarm); HCEGANT kind 2 ID 0x1b5f. */
#define PIC_YARD_RED_SWARM 0x1b5f

/* Bitmap used by DrawSimKid; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:272
 * (DrawSimKid); HCEGANT kind 2 ID 0x1f40. */
#define PIC_YARD_HUMAN_FRAME_BASE 0x1f40

/* Bitmap used by DrawDog; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:332
 * (DrawDog); HCEGANT kind 2 ID 0x2134. */
#define PIC_YARD_DOG_FRAME_BASE 0x2134

/* Bitmap used by DrawMower; frame bases are additive, not window IDs. Evidence: src/ui/yard_window.c:438
 * (DrawMower); HCEGANT kind 2 ID 0x2260. */
#define PIC_YARD_MOWER_FRAME_BASE 0x2260

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x238c. */
#define PIC_YELLOW_DEATH_DIALOG 0x238c

/* Bitmap used by YellowBirth; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:355 (YellowBirth); HCEGANT kind 2 ID 0x238d. */
#define PIC_YELLOW_BIRTH_DIALOG 0x238d

/* Bitmap used by YellowDialog; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:800 (YellowDialog); HCEGANT kind 2 ID 0x2396. */
#define PIC_YELLOW_DIALOG_EATING 0x2396

/* Bitmap used by YellowDialog; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:800 (YellowDialog); HCEGANT kind 2 ID 0x2397. */
#define PIC_YELLOW_DIALOG_EATING_OVERLAY 0x2397

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x23be. */
#define PIC_DEATH_DROWNED 0x23be

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x23bf. */
#define PIC_DEATH_INSECTICIDE 0x23bf

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x23c0. */
#define PIC_DEATH_MOWER 0x23c0

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x23c2. */
#define PIC_DEATH_STARVED 0x23c2

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x23c3. */
#define PIC_DEATH_FOOT 0x23c3

/* Bitmap used by YellowDeath; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:483 (YellowDeath); HCEGANT kind 2 ID 0x23c4. */
#define PIC_DEATH_FIGHT_OR_ELECTROCUTION 0x23c4

/* Bitmap used by LionDialog; frame bases are additive, not window IDs. Evidence:
 * src/ui/yellow_commands.c:747 (LionDialog); HCEGANT kind 2 ID 0x23f0. */
#define PIC_ANT_LION_DIALOG_FRAME_BASE 0x23f0

/* Bitmap used by SpiderDialog; frame bases are additive, not window IDs. Evidence:
 * src/ui/scenario_dialogs.c:558 (SpiderDialog); HCEGANT kind 2 ID 0x2ee0. */
#define PIC_SPIDER_DIALOG_BACKGROUND 0x2ee0

/* Bitmap used by SpiderDialog; frame bases are additive, not window IDs. Evidence:
 * src/ui/scenario_dialogs.c:558 (SpiderDialog); HCEGANT kind 2 ID 0x2ee1. */
#define PIC_SPIDER_DIALOG_FRAME_BASE 0x2ee1

/* Bitmap used by DrawSimPayoff; frame bases are additive, not window IDs. Evidence:
 * src/ui/intro_credits.c:48 (DrawSimPayoff); HCEGANT kind 2 ID 0x3f48. */
#define PIC_PAYOFF_BACKGROUND 0x3f48

/* Bitmap used by DrawSimPayoff; frame bases are additive, not window IDs. Evidence:
 * src/ui/intro_credits.c:48 (DrawSimPayoff); HCEGANT kind 2 ID 0x3f52. */
#define PIC_PAYOFF_FRAME_BIAS 0x3f52

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4268. */
#define PIC_TUTORIAL_YELLOW_ANT 0x4268

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4269. */
#define PIC_TUTORIAL_GO_OUTSIDE 0x4269

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x426a. */
#define PIC_TUTORIAL_FOOD 0x426a

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x426b. */
#define PIC_TUTORIAL_RETURN_TO_NEST 0x426b

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x426c. */
#define PIC_TUTORIAL_PICK_UP_ROCK 0x426c

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x426d. */
#define PIC_TUTORIAL_OPEN_YARD 0x426d

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x426e. */
#define PIC_TUTORIAL_OPEN_HOUSE 0x426e

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x426f. */
#define PIC_TUTORIAL_RETURN_TO_PATCH 0x426f

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4270. */
#define PIC_TUTORIAL_BEHAVIOR 0x4270

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4271. */
#define PIC_TUTORIAL_HELP 0x4271

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4272. */
#define PIC_TUTORIAL_COLONY_BARS 0x4272

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4273. */
#define PIC_TUTORIAL_CASTE 0x4273

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4274. */
#define PIC_TUTORIAL_CENTER_ON_ANT 0x4274

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson); HCEGANT kind 2 ID 0x4275. */
#define PIC_TUTORIAL_HEALTH_SETPOINT 0x4275

/* Bitmap used by GiveLesson; frame bases are additive, not window IDs. Evidence:
 * src/simulation/tutorial.c:97 (GiveLesson). */
#define PIC_TUTORIAL_MAP_OVERVIEW 0x4276

/* Runtime-generated bitmap cache ID; not a shipped picture resource. Evidence: src/ui/yard_window.c:272
 * (DrawSimKid); src/ui/view_dialog_helpers.c:337 (res_lookup_dynamic_balloon). */
#define PIC_HUMAN_BALLOON_BUFFER 0x7530

/* Runtime-generated bitmap cache ID; not a shipped picture resource. Evidence: src/ui/yard_window.c:577
 * (DrawAnimYardMessage); src/ui/view_dialog_helpers.c:337 (res_lookup_dynamic_balloon). */
#define PIC_YARD_MESSAGE_BUFFER 0x7531

/* hanim_SetObjectPos preserves the current picture for this sentinel. Evidence: src/graphics/anim.c:355
 * (hanim_SetObjectPos). */
#define PIC_KEEP_CURRENT 0x8000

#endif
