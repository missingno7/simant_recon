/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_WINDOWS_IDS_H
#define SIMANT_WINDOWS_IDS_H

/* Packed window ID; resource 0. Evidence: HCEGANT kind 0 ID 0x0; src/ui/edit_view.c:621 (OpenEditWindow). */
#define WIN_EDIT 0x0

/* Low byte indexes the window object-pointer table. Evidence: src/window/object_geometry.c:166
 * (win_ObjAddr). */
#define OBJ_INDEX_MASK 0xff

/* Packed window ID; resource 1. Evidence: HCEGANT kind 0 ID 0x1; src/ui/map_window.c:147 (OpenMapWindow). */
#define WIN_MAP 0x100

/* Title string set from MwinTitle[MapMode]. Evidence: HCEGANT kind 0 ID 0x1 obj 0x1;
 * src/ui/view_dialog_helpers.c:65 (SetMapTitle). */
#define OBJ_MAP_TITLE (WIN_MAP | 0x1)

/* Receives MapAreaEvent. Evidence: HCEGANT kind 0 ID 0x1 obj 0x2; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_VIEWPORT (WIN_MAP | 0x2)

/* Picture passed to DoWinHelp for the map controls. Evidence: HCEGANT kind 0 ID 0x1 obj 0x3;
 * src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_HELP_PICTURE (WIN_MAP | 0x3)

/* Switches to the yard. Evidence: HCEGANT kind 0 ID 0x1 obj 0x5; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_YARD (WIN_MAP | 0x5)

/* Selects MapPlane 1. Evidence: HCEGANT kind 0 ID 0x1 obj 0x6; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_SURFACE (WIN_MAP | 0x6)

/* Selects MapPlane 2. Evidence: HCEGANT kind 0 ID 0x1 obj 0x7; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_BLACK_NEST (WIN_MAP | 0x7)

/* Selects MapPlane 3. Evidence: HCEGANT kind 0 ID 0x1 obj 0x8; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_RED_NEST (WIN_MAP | 0x8)

/* Selects PherMapBN through MapMode 4. Evidence: HCEGANT kind 0 ID 0x1 obj 0x9; src/ui/view_commands.c:110
 * (SetMapModeAnt). */
#define OBJ_MAP_BLACK_NEST_SCENT (WIN_MAP | 0x9)

/* Selects PherMapBT through MapMode 5. Evidence: HCEGANT kind 0 ID 0x1 obj 0xa; src/ui/view_commands.c:110
 * (SetMapModeAnt). */
#define OBJ_MAP_BLACK_TRAIL_SCENT (WIN_MAP | 0xa)

/* Selects PherMapA through MapMode 8. Evidence: HCEGANT kind 0 ID 0x1 obj 0xb; src/ui/view_commands.c:110
 * (SetMapModeAnt). */
#define OBJ_MAP_ALARM_SCENT (WIN_MAP | 0xb)

/* Selects PherMapRN through MapMode 6. Evidence: HCEGANT kind 0 ID 0x1 obj 0xc; src/ui/view_commands.c:110
 * (SetMapModeAnt). */
#define OBJ_MAP_RED_NEST_SCENT (WIN_MAP | 0xc)

/* Selects PherMapRT through MapMode 7. Evidence: HCEGANT kind 0 ID 0x1 obj 0xd; src/ui/view_commands.c:110
 * (SetMapModeAnt). */
#define OBJ_MAP_RED_TRAIL_SCENT (WIN_MAP | 0xd)

/* Opens behavior control. Evidence: HCEGANT kind 0 ID 0x1 obj 0xf; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_BEHAVIOR (WIN_MAP | 0xf)

/* Centers on the yellow ant; modifiers also invoke cheats. Evidence: HCEGANT kind 0 ID 0x1 obj 0x10;
 * src/ui/map_window.c:672 (MapToYellowAnt). */
#define OBJ_MAP_YELLOW_ANT (WIN_MAP | 0x10)

/* Opens caste control. Evidence: HCEGANT kind 0 ID 0x1 obj 0x11; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_CASTE (WIN_MAP | 0x11)

/* Invokes MysteryButton. Evidence: HCEGANT kind 0 ID 0x1 obj 0x12; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_MYSTERY (WIN_MAP | 0x12)

/* Opens history. Evidence: HCEGANT kind 0 ID 0x1 obj 0x13; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_HISTORY (WIN_MAP | 0x13)

/* Opens score dialog. Evidence: HCEGANT kind 0 ID 0x1 obj 0x14; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_SCORE (WIN_MAP | 0x14)

/* Opens information cards. Evidence: HCEGANT kind 0 ID 0x1 obj 0x15; src/ui/map_window.c:118
 * (ProcMapEvent). */
#define OBJ_MAP_INFO (WIN_MAP | 0x15)

/* Invokes map help. Evidence: HCEGANT kind 0 ID 0x1 obj 0x16; src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_HELP (WIN_MAP | 0x16)

/* Anchor and drawing target for the tools popup. Evidence: HCEGANT kind 0 ID 0x1 obj 0x17;
 * src/ui/minimap.c:112 (MapToolsMenu). */
#define OBJ_MAP_TOOLS (WIN_MAP | 0x17)

/* Displays the colony caste population popup. Evidence: HCEGANT kind 0 ID 0x1 obj 0x18;
 * src/ui/map_window.c:118 (ProcMapEvent). */
#define OBJ_MAP_CASTE_POPULATION (WIN_MAP | 0x18)

/* Prints BpopT. Evidence: HCEGANT kind 0 ID 0x1 obj 0x19; src/ui/map_window.c:442 (DrawMapData). */
#define OBJ_MAP_BLACK_POPULATION_TEXT (WIN_MAP | 0x19)

/* Prints RpopT. Evidence: HCEGANT kind 0 ID 0x1 obj 0x1a; src/ui/map_window.c:442 (DrawMapData). */
#define OBJ_MAP_RED_POPULATION_TEXT (WIN_MAP | 0x1a)

/* Displays HealthB / 100. Evidence: HCEGANT kind 0 ID 0x1 obj 0x1b; src/ui/map_window.c:442 (DrawMapData). */
#define OBJ_MAP_BLACK_HEALTH_BAR (WIN_MAP | 0x1b)

/* Displays redHealth / 100. Evidence: HCEGANT kind 0 ID 0x1 obj 0x1c; src/ui/map_window.c:442
 * (DrawMapData). */
#define OBJ_MAP_RED_HEALTH_BAR (WIN_MAP | 0x1c)

/* Displays BpopT / maxPop. Evidence: HCEGANT kind 0 ID 0x1 obj 0x1d; src/ui/map_window.c:442 (DrawMapData). */
#define OBJ_MAP_BLACK_POPULATION_BAR (WIN_MAP | 0x1d)

/* Displays RpopT / maxPop. Evidence: HCEGANT kind 0 ID 0x1 obj 0x1e; src/ui/map_window.c:442 (DrawMapData). */
#define OBJ_MAP_RED_POPULATION_BAR (WIN_MAP | 0x1e)

/* Packed window ID; resource 2. Evidence: HCEGANT kind 0 ID 0x2; src/ui/scenario_dialogs.c:175
 * (DoScenario). */
#define WIN_SCENARIO 0x200

/* Scenario event becomes CurGameType 1; ScenarioNameStrs[1] is Quick Game. Evidence: HCEGANT kind 0 ID 0x2
 * obj 0x2; src/startup/game_session.c:267 (NewGame). */
#define OBJ_SCENARIO_QUICK_GAME (WIN_SCENARIO | 0x2)

/* Scenario event becomes CurGameType 2; ScenarioNameStrs[2] is Full Game. Evidence: HCEGANT kind 0 ID 0x2
 * obj 0x3; src/startup/game_session.c:267 (NewGame). */
#define OBJ_SCENARIO_FULL_GAME (WIN_SCENARIO | 0x3)

/* Scenario event becomes CurGameType 3; ScenarioNameStrs[3] is Experimental. Evidence: HCEGANT kind 0 ID
 * 0x2 obj 0x4; src/startup/game_session.c:267 (NewGame). */
#define OBJ_SCENARIO_EXPERIMENTAL (WIN_SCENARIO | 0x4)

/* Scenario event returns -1 instead of starting a game. Evidence: HCEGANT kind 0 ID 0x2 obj 0x5;
 * src/startup/game_session.c:267 (NewGame). */
#define OBJ_SCENARIO_CANCEL (WIN_SCENARIO | 0x5)

/* Scenario event becomes CurGameType 0; ScenarioNameStrs[0] is Tutorial Game. Evidence: HCEGANT kind 0 ID
 * 0x2 obj 0x6; src/startup/game_session.c:267 (NewGame). */
#define OBJ_SCENARIO_TUTORIAL (WIN_SCENARIO | 0x6)

/* Scenario event invokes LoadGame. Evidence: HCEGANT kind 0 ID 0x2 obj 0x7; src/startup/game_session.c:267
 * (NewGame). */
#define OBJ_SCENARIO_LOAD_GAME (WIN_SCENARIO | 0x7)

/* Packed window ID; resource 3. Evidence: HCEGANT kind 0 ID 0x3; src/ui/intro_credits.c:235 (ShowIntro). */
#define WIN_INTRO 0x300

/* Packed window ID; resource 4. Evidence: HCEGANT kind 0 ID 0x4; src/ui/scenario_dialogs.c:500
 * (EndGameDialog). */
#define WIN_END_GAME 0x400

/* Prints ScenarioNameStrs[CurGameType]. Evidence: HCEGANT kind 0 ID 0x4 obj 0x2;
 * src/ui/scenario_dialogs.c:500 (EndGameDialog). */
#define OBJ_END_GAME_GAME_TYPE (WIN_END_GAME | 0x2)

/* Prints final score. Evidence: HCEGANT kind 0 ID 0x4 obj 0x3; src/ui/scenario_dialogs.c:500
 * (EndGameDialog). */
#define OBJ_END_GAME_SCORE (WIN_END_GAME | 0x3)

/* Prints EndGameRatingStrs[level]. Evidence: HCEGANT kind 0 ID 0x4 obj 0x4; src/ui/scenario_dialogs.c:500
 * (EndGameDialog). */
#define OBJ_END_GAME_RATING (WIN_END_GAME | 0x4)

/* Packed window ID; resource 5. Evidence: HCEGANT kind 0 ID 0x5; src/ui/info_cards.c:532 (OpenInfoWindow). */
#define WIN_INFO 0x500

/* Receives the card title resource. Evidence: HCEGANT kind 0 ID 0x5 obj 0x1; src/ui/info_cards.c:372
 * (DisplayCard). */
#define OBJ_INFO_TITLE (WIN_INFO | 0x1)

/* Rectangle used to render and hit-test card contents. Evidence: HCEGANT kind 0 ID 0x5 obj 0x2;
 * src/ui/info_cards.c:646 (ProcInfoEvent). */
#define OBJ_INFO_CONTENT (WIN_INFO | 0x2)

/* Packed window ID; resource 6. Evidence: HCEGANT kind 0 ID 0x6; src/ui/editor_menus.c:23 (EditScentMenu). */
#define WIN_SCENT_MENU 0x600

/* Packed window ID; resource 7. Evidence: HCEGANT kind 0 ID 0x7; src/ui/editor_menus.c:213 (AntMenu). */
#define WIN_ANT_COMMAND_MENU 0x700

/* Packed window ID; resource 8. Evidence: HCEGANT kind 0 ID 0x8; src/ui/editor_menus.c:213 (AntMenu). */
#define WIN_UNNESTED_QUEEN_MENU 0x800

/* Packed window ID; resource 9. Evidence: HCEGANT kind 0 ID 0x9; src/ui/experiment_menu.c:40 (DoExpMenu). */
#define WIN_EXPERIMENT_TOOLS_MENU 0x900

/* First experiment tool item; tool index is added. Evidence: HCEGANT kind 0 ID 0x9 obj 0x2;
 * src/ui/experiment_menu.c:40 (DoExpMenu). */
#define OBJ_EXPERIMENT_TOOLS_MENU_FIRST_TOOL (WIN_EXPERIMENT_TOOLS_MENU | 0x2)

/* Last item in experiment tool rectangle scan. Evidence: HCEGANT kind 0 ID 0x9 obj 0x9;
 * src/ui/experiment_menu.c:40 (DoExpMenu). */
#define OBJ_EXPERIMENT_TOOLS_MENU_LAST_TOOL (WIN_EXPERIMENT_TOOLS_MENU | 0x9)

/* Packed window ID; resource 10. Evidence: HCEGANT kind 0 ID 0xa; src/ui/editor_menus.c:63 (EditToolsMenu). */
#define WIN_QUICK_GAME_TOOLS_MENU 0xa00

/* Packed window ID; resource 11. Evidence: HCEGANT kind 0 ID 0xb; src/ui/editor_menus.c:63 (EditToolsMenu). */
#define WIN_FULL_GAME_TOOLS_MENU 0xb00

/* Packed window ID; resource 12. Evidence: HCEGANT kind 0 ID 0xc; src/ui/editor_menus.c:36 (toolMenus);
 * src/ui/experiment_menu.c:40 (DoExpMenu); src/ui/experiment_tools.c:94 (DoTool). */
#define WIN_WALL_TOOL_MENU 0xc00

/* Packed window ID; resource 13. Evidence: HCEGANT kind 0 ID 0xd; src/ui/editor_menus.c:36 (toolMenus);
 * src/ui/experiment_menu.c:40 (DoExpMenu); src/ui/experiment_tools.c:94 (DoTool). */
#define WIN_SCENT_TOOL_MENU 0xd00

/* Packed window ID; resource 14. Evidence: HCEGANT kind 0 ID 0xe; src/ui/editor_menus.c:36 (toolMenus);
 * src/ui/experiment_menu.c:40 (DoExpMenu); src/ui/experiment_tools.c:94 (DoTool). */
#define WIN_KILL_TOOL_MENU 0xe00

/* Packed window ID; resource 15. Evidence: HCEGANT kind 0 ID 0xf; src/ui/editor_menus.c:36 (toolMenus);
 * src/ui/experiment_menu.c:40 (DoExpMenu); src/ui/experiment_tools.c:94 (DoTool). */
#define WIN_DIG_TOOL_MENU 0xf00

/* Packed window ID; resource 16. Evidence: HCEGANT kind 0 ID 0x10; src/ui/editor_menus.c:36 (toolMenus);
 * src/ui/experiment_menu.c:40 (DoExpMenu); src/ui/experiment_tools.c:94 (DoTool). */
#define WIN_ANT_TOOL_MENU 0x1000

/* Packed window ID; resource 17. Evidence: HCEGANT kind 0 ID 0x11; src/ui/editor_menus.c:36 (toolMenus);
 * src/ui/experiment_menu.c:40 (DoExpMenu); src/ui/experiment_tools.c:94 (DoTool). */
#define WIN_FOOD_TOOL_MENU 0x1100

/* Packed window ID; resource 18. Evidence: HCEGANT kind 0 ID 0x12; src/ui/colony_controls.c:104
 * (OpenModeWindow). */
#define WIN_BEHAVIOR 0x1200

/* Dispatch base; case zero invokes help. Evidence: HCEGANT kind 0 ID 0x12 obj 0x3;
 * src/ui/colony_controls.c:197 (ProcModeEvent). */
#define OBJ_BEHAVIOR_HELP (WIN_BEHAVIOR | 0x3)

/* Selected when automatic control is disabled. Evidence: HCEGANT kind 0 ID 0x12 obj 0x5;
 * src/ui/colony_controls.c:197 (ProcModeEvent). */
#define OBJ_BEHAVIOR_MANUAL (WIN_BEHAVIOR | 0x5)

/* Preset index is message code minus this base. Evidence: HCEGANT kind 0 ID 0x12 obj 0x6;
 * src/ui/colony_controls.c:197 (ProcModeEvent). */
#define OBJ_BEHAVIOR_FIRST_PRESET (WIN_BEHAVIOR | 0x6)

/* Pointer triangle used for level selection. Evidence: HCEGANT kind 0 ID 0x12 obj 0xd;
 * src/ui/colony_controls.c:197 (ProcModeEvent). */
#define OBJ_BEHAVIOR_TRIANGLE (WIN_BEHAVIOR | 0xd)

/* Picture passed to DoWinHelp. Evidence: HCEGANT kind 0 ID 0x12 obj 0xe; src/ui/colony_controls.c:197
 * (ProcModeEvent). */
#define OBJ_BEHAVIOR_HELP_PICTURE (WIN_BEHAVIOR | 0xe)

/* Packed window ID; resource 19. Evidence: HCEGANT kind 0 ID 0x13; src/ui/colony_controls.c:98
 * (OpenCasteWindow). */
#define WIN_CASTE 0x1300

/* Dispatch base; case zero invokes help. Evidence: HCEGANT kind 0 ID 0x13 obj 0x3;
 * src/ui/colony_controls.c:129 (ProcCasteEvent). */
#define OBJ_CASTE_HELP (WIN_CASTE | 0x3)

/* Selected when automatic control is disabled. Evidence: HCEGANT kind 0 ID 0x13 obj 0x5;
 * src/ui/colony_controls.c:129 (ProcCasteEvent). */
#define OBJ_CASTE_MANUAL (WIN_CASTE | 0x5)

/* Preset index is message code minus this base. Evidence: HCEGANT kind 0 ID 0x13 obj 0x6;
 * src/ui/colony_controls.c:129 (ProcCasteEvent). */
#define OBJ_CASTE_FIRST_PRESET (WIN_CASTE | 0x6)

/* Pointer triangle used for level selection. Evidence: HCEGANT kind 0 ID 0x13 obj 0xd;
 * src/ui/colony_controls.c:129 (ProcCasteEvent). */
#define OBJ_CASTE_TRIANGLE (WIN_CASTE | 0xd)

/* Picture passed to DoWinHelp. Evidence: HCEGANT kind 0 ID 0x13 obj 0xe; src/ui/colony_controls.c:129
 * (ProcCasteEvent). */
#define OBJ_CASTE_HELP_PICTURE (WIN_CASTE | 0xe)

/* Packed window ID; resource 20. Evidence: HCEGANT kind 0 ID 0x14; src/ui/minimap.c:299 (OpenMiniMapWin). */
#define WIN_MINIMAP 0x1400

/* Rectangle used to draw the minimap. Evidence: HCEGANT kind 0 ID 0x14 obj 0x1; src/ui/minimap.c:239
 * (Mini_DrawMapI). */
#define OBJ_MINIMAP_VIEWPORT (WIN_MINIMAP | 0x1)

/* Packed window ID; resource 21. Evidence: HCEGANT kind 0 ID 0x15; src/ui/history_window.c:16
 * (OpenHistoryWindow). */
#define WIN_HISTORY 0x1500

/* Graph index is event ID minus this base. Evidence: HCEGANT kind 0 ID 0x15 obj 0x3;
 * src/ui/history_window.c:66 (ToggleHistButton). */
#define OBJ_HISTORY_FIRST_GRAPH_BUTTON (WIN_HISTORY | 0x3)

/* End of ten graph buttons. Evidence: HCEGANT kind 0 ID 0x15 obj 0xc; src/ui/history_window.c:37
 * (ProcHistoryEvent). */
#define OBJ_HISTORY_LAST_GRAPH_BUTTON (WIN_HISTORY | 0xc)

/* Invokes history help. Evidence: HCEGANT kind 0 ID 0x15 obj 0xd; src/ui/history_window.c:37
 * (ProcHistoryEvent). */
#define OBJ_HISTORY_HELP (WIN_HISTORY | 0xd)

/* Graph drawing and click rectangle. Evidence: HCEGANT kind 0 ID 0x15 obj 0xe; src/ui/history_window.c:37
 * (ProcHistoryEvent). */
#define OBJ_HISTORY_GRAPH (WIN_HISTORY | 0xe)

/* History help picture object. Evidence: HCEGANT kind 0 ID 0x15 obj 0xf; src/ui/history_window.c:37
 * (ProcHistoryEvent). */
#define OBJ_HISTORY_HELP_PICTURE (WIN_HISTORY | 0xf)

/* ASCII drive letter plus this gives the matching drive button. Evidence: src/ui/save_load.c:260
 * (o09_35F5_03C6); HCEGANT kind 0 ID 0x16 obj 0xb. */
#define FILE_DRIVE_LETTER_OBJECT_BIAS (OBJ_FILE_SELECT_DRIVE_A - 'A')

/* Packed window ID; resource 22. Evidence: HCEGANT kind 0 ID 0x16; src/ui/save_load.c:260 (o09_35F5_03C6). */
#define WIN_FILE_SELECT 0x1600

/* Receives selector title. Evidence: HCEGANT kind 0 ID 0x16 obj 0x1; src/ui/save_load.c:260
 * (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_TITLE (WIN_FILE_SELECT | 0x1)

/* Layout rectangle collapsed when filename input is disabled. Evidence: HCEGANT kind 0 ID 0x16 obj 0x2;
 * src/ui/save_load.c:260 (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_NAME_GROUP_LAYOUT (WIN_FILE_SELECT | 0x2)

/* Drawn frame and rectangle surrounding the filename input. Evidence: HCEGANT kind 0 ID 0x16 obj 0x3;
 * src/ui/save_load.c:260 (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_NAME_FRAME (WIN_FILE_SELECT | 0x3)

/* Click enters filename editing. Evidence: HCEGANT kind 0 ID 0x16 obj 0x4; src/ui/save_load.c:260
 * (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_NAME_INPUT (WIN_FILE_SELECT | 0x4)

/* Receives current directory path; resource label Path:. Evidence: HCEGANT kind 0 ID 0x16 obj 0x6;
 * src/ui/save_load.c:260 (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_PATH (WIN_FILE_SELECT | 0x6)

/* Type-8 scrollbar next to type-4 file list in resource. Evidence: HCEGANT kind 0 ID 0x16 obj 0x8;
 * src/ui/save_load.c:260 (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_SCROLLBAR (WIN_FILE_SELECT | 0x8)

/* File and directory list populated by list_replace_text. Evidence: HCEGANT kind 0 ID 0x16 obj 0x9;
 * src/ui/save_load.c:260 (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_LIST (WIN_FILE_SELECT | 0x9)

/* Resource button A:; first drive event. Evidence: HCEGANT kind 0 ID 0x16 obj 0xb; src/ui/save_load.c:260
 * (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_DRIVE_A (WIN_FILE_SELECT | 0xb)

/* Resource button H:; last drive event. Evidence: HCEGANT kind 0 ID 0x16 obj 0x12; src/ui/save_load.c:260
 * (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_DRIVE_H (WIN_FILE_SELECT | 0x12)

/* Accepts selection; text comes from verb. Evidence: HCEGANT kind 0 ID 0x16 obj 0x13;
 * src/ui/save_load.c:260 (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_ACCEPT (WIN_FILE_SELECT | 0x13)

/* Cancels selector; resource CANCEL. Evidence: HCEGANT kind 0 ID 0x16 obj 0x14; src/ui/save_load.c:260
 * (o09_35F5_03C6). */
#define OBJ_FILE_SELECT_CANCEL (WIN_FILE_SELECT | 0x14)

/* Packed window ID; resource 23. Evidence: HCEGANT kind 0 ID 0x17; src/ui/scenario_dialogs.c:316
 * (DrawCastePopUp). */
#define WIN_CASTE_POPULATION 0x1700

/* Bounds for caste population rows. Evidence: HCEGANT kind 0 ID 0x17 obj 0x2; src/ui/scenario_dialogs.c:316
 * (DrawCastePopUp). */
#define OBJ_CASTE_POPULATION_CONTENT (WIN_CASTE_POPULATION | 0x2)

/* Selects color for CastePopB counts and bars. Evidence: HCEGANT kind 0 ID 0x17 obj 0x3;
 * src/ui/scenario_dialogs.c:316 (DrawCastePopUp). */
#define OBJ_CASTE_POPULATION_BLACK_COLOR (WIN_CASTE_POPULATION | 0x3)

/* Selects color for CastePopR counts and bars. Evidence: HCEGANT kind 0 ID 0x17 obj 0x4;
 * src/ui/scenario_dialogs.c:316 (DrawCastePopUp). */
#define OBJ_CASTE_POPULATION_RED_COLOR (WIN_CASTE_POPULATION | 0x4)

/* Packed window ID; resource 24. Evidence: HCEGANT kind 0 ID 0x18; src/ui/scenario_dialogs.c:254
 * (ScoreDialog). */
#define WIN_SCORE 0x1800

/* First score percentage field; i added for eight scores. Evidence: HCEGANT kind 0 ID 0x18 obj 0x2;
 * src/ui/scenario_dialogs.c:254 (ScoreDialog). */
#define OBJ_SCORE_FIRST_PERCENT (WIN_SCORE | 0x2)

/* Overall score title, or experimental-game explanation. Evidence: HCEGANT kind 0 ID 0x18 obj 0xa;
 * src/ui/scenario_dialogs.c:254 (ScoreDialog). */
#define OBJ_SCORE_OVERALL_TITLE (WIN_SCORE | 0xa)

/* Overall score value, or experimental-game explanation. Evidence: HCEGANT kind 0 ID 0x18 obj 0xb;
 * src/ui/scenario_dialogs.c:254 (ScoreDialog). */
#define OBJ_SCORE_OVERALL_VALUE (WIN_SCORE | 0xb)

/* WindPromptStrs[14]: Click here to continue. Evidence: HCEGANT kind 0 ID 0x18 obj 0xc;
 * src/ui/scenario_dialogs.c:254 (ScoreDialog). */
#define OBJ_SCORE_CONTINUE (WIN_SCORE | 0xc)

/* Packed window ID; resource 25. Evidence: HCEGANT kind 0 ID 0x19; src/ui/view_dialog_helpers.c:307
 * (MapToYard). */
#define WIN_YARD 0x1900

/* Title set from MwinTitle[YardMode+9]. Evidence: HCEGANT kind 0 ID 0x19 obj 0x1;
 * src/ui/view_dialog_helpers.c:65 (SetMapTitle). */
#define OBJ_YARD_TITLE (WIN_YARD | 0x1)

/* Receives YardArea events. Evidence: HCEGANT kind 0 ID 0x19 obj 0x2; src/ui/yard_window.c:63
 * (ProcYardEvent). */
#define OBJ_YARD_VIEWPORT (WIN_YARD | 0x2)

/* Yard or house bitmap object switched by mode. Evidence: HCEGANT kind 0 ID 0x19 obj 0x3;
 * src/ui/yard_window.c:187 (win_DrawYardWindow). */
#define OBJ_YARD_BACKGROUND (WIN_YARD | 0x3)

/* Object passed to DoWinHelp. Evidence: HCEGANT kind 0 ID 0x19 obj 0x6; src/ui/yard_window.c:63
 * (ProcYardEvent). */
#define OBJ_YARD_HELP_PICTURE (WIN_YARD | 0x6)

/* Returns from yard to map. Evidence: HCEGANT kind 0 ID 0x19 obj 0x7; src/ui/yard_window.c:63
 * (ProcYardEvent). */
#define OBJ_YARD_PATCH (WIN_YARD | 0x7)

/* Toggles yard/house or returns to YardMode 0. Evidence: HCEGANT kind 0 ID 0x19 obj 0x8;
 * src/ui/yard_window.c:63 (ProcYardEvent). */
#define OBJ_YARD_YARD_HOUSE (WIN_YARD | 0x8)

/* Selects YardMode 2; MwinTitle index 11 is Strategic View. Evidence: HCEGANT kind 0 ID 0x19 obj 0x9;
 * src/ui/yard_window.c:63 (ProcYardEvent). */
#define OBJ_YARD_STRATEGIC (WIN_YARD | 0x9)

/* Selects YardMode 3; MwinTitle index 12 is Graphic View. Evidence: HCEGANT kind 0 ID 0x19 obj 0xa;
 * src/ui/yard_window.c:63 (ProcYardEvent). */
#define OBJ_YARD_GRAPHIC (WIN_YARD | 0xa)

/* Starts FlyAwayB when breeding population permits. Evidence: HCEGANT kind 0 ID 0x19 obj 0xb;
 * src/ui/yard_window.c:63 (ProcYardEvent). */
#define OBJ_YARD_MATING (WIN_YARD | 0xb)

/* Prints QueenStorageB. Evidence: HCEGANT kind 0 ID 0x19 obj 0xc; src/ui/yard_window.c:187
 * (win_DrawYardWindow). */
#define OBJ_YARD_STORED_QUEENS (WIN_YARD | 0xc)

/* Sets LayDownQueenMode to one. Evidence: HCEGANT kind 0 ID 0x19 obj 0xd; src/ui/yard_window.c:63
 * (ProcYardEvent). */
#define OBJ_YARD_DROP_QUEEN_MODE (WIN_YARD | 0xd)

/* Sets LayDownQueenMode to zero. Evidence: HCEGANT kind 0 ID 0x19 obj 0xe; src/ui/yard_window.c:63
 * (ProcYardEvent). */
#define OBJ_YARD_PLACE_QUEEN_MODE (WIN_YARD | 0xe)

/* Bitmap visible for YardMode 0 and 1; hidden for modes 2 and 3. Evidence: HCEGANT kind 0 ID 0x19 obj 0xf;
 * src/ui/view_commands.c:158 (SetYardMode). */
#define OBJ_YARD_AUX_BITMAP (WIN_YARD | 0xf)

/* Invokes PlaceQueenInYard. Evidence: HCEGANT kind 0 ID 0x19 obj 0x10; src/ui/yard_window.c:63
 * (ProcYardEvent). */
#define OBJ_YARD_PLACE_QUEEN (WIN_YARD | 0x10)

/* Invokes yard help. Evidence: HCEGANT kind 0 ID 0x19 obj 0x11; src/ui/yard_window.c:63 (ProcYardEvent). */
#define OBJ_YARD_HELP (WIN_YARD | 0x11)

/* Prints ColonyTotalBlack. Evidence: HCEGANT kind 0 ID 0x19 obj 0x12; src/ui/yard_window.c:187
 * (win_DrawYardWindow). */
#define OBJ_YARD_BLACK_COLONIES (WIN_YARD | 0x12)

/* Prints ColonyTotalRed. Evidence: HCEGANT kind 0 ID 0x19 obj 0x13; src/ui/yard_window.c:187
 * (win_DrawYardWindow). */
#define OBJ_YARD_RED_COLONIES (WIN_YARD | 0x13)

/* Rectangle and object used for yard ribbon messages. Evidence: HCEGANT kind 0 ID 0x19 obj 0x14;
 * src/ui/yard_window.c:187 (win_DrawYardWindow). */
#define OBJ_YARD_MESSAGE (WIN_YARD | 0x14)

/* Drawn with message object; type 19 calls win_RectHOutline in win_DrawObjectI. Evidence: HCEGANT kind 0 ID
 * 0x19 obj 0x15; src/ui/yard_window.c:187 (win_DrawYardWindow). */
#define OBJ_YARD_MESSAGE_HORIZONTAL_FRAME (WIN_YARD | 0x15)

/* Packed window ID; resource 26. Evidence: HCEGANT kind 0 ID 0x1a; src/ui/scenario_dialogs.c:558
 * (SpiderDialog). */
#define WIN_ANIMATION_DIALOG 0x1a00

/* Bitmap target shared by spider, yellow-ant and payoff dialogs. Evidence: HCEGANT kind 0 ID 0x1a obj 0x1;
 * src/ui/scenario_dialogs.c:558 (SpiderDialog). */
#define OBJ_ANIMATION_DIALOG_PICTURE (WIN_ANIMATION_DIALOG | 0x1)

/* Prints WindPromptStrs[promptIndex+23]. Evidence: HCEGANT kind 0 ID 0x1a obj 0x2;
 * src/ui/yellow_commands.c:800 (YellowDialog). */
#define OBJ_ANIMATION_DIALOG_PROMPT (WIN_ANIMATION_DIALOG | 0x2)

/* Packed window ID; resource 27. Evidence: HCEGANT kind 0 ID 0x1b. */
#define WIN_CONTINUE_PROMPT 0x1b00

/* Packed window ID; resource 28. Evidence: HCEGANT kind 0 ID 0x1c. */
#define WIN_DEBUG 0x1c00

/* Packed window ID; resource 29. Evidence: HCEGANT kind 0 ID 0x1d; src/ui/editor_menus.c:146 (MagnifyMenu). */
#define WIN_MAGNIFY 0x1d00

/* Prints EggStr or CasteStr. Evidence: HCEGANT kind 0 ID 0x1d obj 0x2; src/ui/editor_menus.c:146
 * (MagnifyMenu). */
#define OBJ_MAGNIFY_CASTE (WIN_MAGNIFY | 0x2)

/* Prints ModeStr. Evidence: HCEGANT kind 0 ID 0x1d obj 0x3; src/ui/editor_menus.c:146 (MagnifyMenu). */
#define OBJ_MAGNIFY_ACTIVITY (WIN_MAGNIFY | 0x3)

/* Prints LoadStr. Evidence: HCEGANT kind 0 ID 0x1d obj 0x4; src/ui/editor_menus.c:146 (MagnifyMenu). */
#define OBJ_MAGNIFY_LOAD (WIN_MAGNIFY | 0x4)

/* Packed window ID; resource 30. Evidence: HCEGANT kind 0 ID 0x1e; src/ui/scenario_dialogs.c:438
 * (PictureDialog). */
#define WIN_PICTURE_TEXT_DIALOG 0x1e00

/* Selects text color before dialog lines are printed. Evidence: HCEGANT kind 0 ID 0x1e obj 0x1;
 * src/ui/scenario_dialogs.c:438 (PictureDialog). */
#define OBJ_PICTURE_TEXT_DIALOG_TEXT_COLOR (WIN_PICTURE_TEXT_DIALOG | 0x1)

/* Packed window ID; resource 31. Evidence: HCEGANT kind 0 ID 0x1f; src/ui/intro_credits.c:136
 * (AboutDialog). */
#define WIN_CREDITS 0x1f00

/* Redrawn before scrolling credits text. Evidence: HCEGANT kind 0 ID 0x1f obj 0x1;
 * src/ui/intro_credits.c:136 (AboutDialog). */
#define OBJ_CREDITS_BACKGROUND (WIN_CREDITS | 0x1)

/* Credits rectangle, clipping region and text color. Evidence: HCEGANT kind 0 ID 0x1f obj 0x2;
 * src/ui/intro_credits.c:136 (AboutDialog). */
#define OBJ_CREDITS_TEXT (WIN_CREDITS | 0x2)

/* Packed window ID; resource 32. Evidence: HCEGANT kind 0 ID 0x20; src/ui/editor_menus.c:213 (AntMenu). */
#define WIN_SPIDER_COMMAND_MENU 0x2000

/* Packed window ID; resource 33. Evidence: HCEGANT kind 0 ID 0x21; src/startup/game_session.c:192
 * (ui_prompt_save_discard_cancel). */
#define WIN_SAVE_CONFIRM 0x2100

/* Rectangle and color used for save-confirmation text. Evidence: HCEGANT kind 0 ID 0x21 obj 0x1;
 * src/startup/game_session.c:192 (ui_prompt_save_discard_cancel). */
#define OBJ_SAVE_CONFIRM_MESSAGE (WIN_SAVE_CONFIRM | 0x1)

/* Resource DON'T SAVE; returns zero. Evidence: HCEGANT kind 0 ID 0x21 obj 0x3;
 * src/startup/game_session.c:192 (ui_prompt_save_discard_cancel). */
#define OBJ_SAVE_CONFIRM_DISCARD (WIN_SAVE_CONFIRM | 0x3)

/* Resource Save; returns one. Evidence: HCEGANT kind 0 ID 0x21 obj 0x4; src/startup/game_session.c:192
 * (ui_prompt_save_discard_cancel). */
#define OBJ_SAVE_CONFIRM_SAVE (WIN_SAVE_CONFIRM | 0x4)

/* Resource Cancel; returns two. Evidence: HCEGANT kind 0 ID 0x21 obj 0x5; src/startup/game_session.c:192
 * (ui_prompt_save_discard_cancel). */
#define OBJ_SAVE_CONFIRM_CANCEL (WIN_SAVE_CONFIRM | 0x5)

/* High byte of a packed window/object identifier. Evidence: src/window/object_geometry.c:175
 * (win_WinObjAddr). */
#define WIN_ID_MASK 0xff00

#endif
