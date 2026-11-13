/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_EVENTS_IDS_H
#define SIMANT_EVENTS_IDS_H

/* Menu selection: about. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_ABOUT 0x1

/* Menu selection: new. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_NEW 0x3

/* Menu selection: load. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_LOAD 0x4

/* Menu selection: save. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_SAVE 0x5

/* Menu selection: save as. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_SAVE_AS 0x6

/* Menu selection: quit. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_QUIT 0x8

/* Menu selection: edit. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_EDIT 0x11

/* Menu selection: map. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_MAP 0x12

/* Menu selection: behavior. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_BEHAVIOR 0x13

/* Menu selection: caste. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_CASTE 0x14

/* Menu selection: history. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_HISTORY 0x15

/* Menu selection: info. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_INFO 0x16

/* Menu selection: status. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_STATUS 0x17

/* Menu selection: yard. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_YARD 0x21

/* Menu selection: house. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_HOUSE 0x22

/* Menu selection: strategic. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_STRATEGIC 0x23

/* Menu selection: graphic. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_GRAPHIC 0x24

/* Menu selection: surface. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_SURFACE 0x26

/* Menu selection: black nest. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_BLACK_NEST 0x27

/* Menu selection: red nest. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_RED_NEST 0x28

/* Menu selection: autotrack. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_AUTOTRACK 0x31

/* Menu selection: music. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_MUSIC 0x32

/* Menu selection: sound effects. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_SOUND_EFFECTS 0x33

/* Menu selection: events. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_EVENTS 0x34

/* Menu selection: messages. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_MESSAGES 0x35

/* Menu selection: silly. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_SILLY 0x36

/* Menu selection: pause. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_PAUSE 0x41

/* Menu selection: slow. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_SLOW 0x43

/* Menu selection: normal. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_NORMAL 0x44

/* Menu selection: fast. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_FAST 0x45

/* Menu selection: ultra. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88 (ProcMenu). */
#define MENU_CMD_ULTRA 0x46

/* Second BIOS byte after a zero prefix is encoded by adding 0x800. Evidence: src/window/text_entry.c:64
 * (ui_edit_text_field). */
#define KEY_EXTENDED_BIT 0x800

/* Moves text cursor to position zero. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_HOME 0x847

/* Moves cursor left without deleting. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_LEFT 0x84b

/* Moves cursor right. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_RIGHT 0x84d

/* Moves text cursor to the string end. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_END 0x84f

/* Inserts a blank character at the cursor. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_INSERT 0x852

/* Deletes character under the cursor. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_DELETE 0x853

/* Clears text from cursor to end in this editor. Evidence: src/window/text_entry.c:64 (ui_edit_text_field). */
#define KEY_EXT_CLEAR_TO_END 0x893

/* Synthetic Continue/choice hit IDs; unrelated to WIN_EXPERIMENT_TOOLS_MENU. Evidence:
 * src/window/alerts.c:128 (ui_show_alert); src/window/alerts.c:268 (ui_choice_prompt). */
#define EVENT_ALERT_BUTTON_BASE 0x900

/* Calls win_track_move. Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_WINDOW_MOVE 0xf081

/* Calls win_lower_or_dismiss. Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_WINDOW_LOWER 0xf082

/* Calls win_Close. Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_WINDOW_CLOSE 0xf083

/* Calls win_track_resize. Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_WINDOW_RESIZE 0xf084

/* Calls win_toggle_zoom. Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_WINDOW_ZOOM 0xf085

/* Calls win_step_object_focus(1). Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_FOCUS_NEXT 0xf086

/* Calls win_step_object_focus(-1). Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_FOCUS_PREVIOUS 0xf087

/* High byte FA dispatches input_translate_special_key; keyboard hook sets BH=FA. Evidence:
 * src/ui/game_events.c:60 (DoEvent). */
#define EVENT_KEY_SCAN_BASE 0xfa00

/* With alternate modifier, calls YellowCommand(3). Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_RECRUIT_THOUSAND_SHORTCUT 0xfa03

/* With control modifier, calls YardToMap. Evidence: src/ui/game_events.c:227 (input_translate_special_key). */
#define EVENT_SCAN_PATCH_SHORTCUT 0xfa05

/* With control modifier, synthesizes house command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_HOUSE_SHORTCUT 0xfa06

/* With control modifier, synthesizes strategic-view command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_STRATEGIC_SHORTCUT 0xfa07

/* With control modifier, synthesizes graphic-view command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_GRAPHIC_SHORTCUT 0xfa08

/* With control modifier, synthesizes surface-view command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_SURFACE_SHORTCUT 0xfa09

/* With control modifier, synthesizes black-nest command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_BLACK_NEST_SHORTCUT 0xfa0a

/* With control modifier, synthesizes red-nest command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_RED_NEST_SHORTCUT 0xfa0b

/* Without control/alternate modifier, calls DoTab. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_TAB_SHORTCUT 0xfa0f

/* With control modifier, synthesizes info-window command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_INFO_SHORTCUT 0xfa17

/* With control modifier, synthesizes history-window command. Evidence: src/ui/game_events.c:227
 * (input_translate_special_key). */
#define EVENT_SCAN_HISTORY_SHORTCUT 0xfa23

/* High byte FD dispatches ProcMenu. Evidence: src/ui/game_events.c:60 (DoEvent). */
#define EVENT_MENU_COMMAND_BASE 0xfd00

/* Encoded menu command; low byte is MENU_CMD_ABOUT. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_ABOUT 0xfd01

/* Encoded menu command; low byte is MENU_CMD_NEW. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_NEW 0xfd03

/* Encoded menu command; low byte is MENU_CMD_LOAD. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_LOAD 0xfd04

/* Encoded menu command; low byte is MENU_CMD_SAVE. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_SAVE 0xfd05

/* Encoded menu command; low byte is MENU_CMD_SAVE_AS. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_SAVE_AS 0xfd06

/* Encoded menu command; low byte is MENU_CMD_QUIT. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_QUIT 0xfd08

/* Encoded menu command; low byte is MENU_CMD_EDIT. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_EDIT 0xfd11

/* Encoded menu command; low byte is MENU_CMD_MAP. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_MAP 0xfd12

/* Encoded menu command; low byte is MENU_CMD_BEHAVIOR. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_BEHAVIOR 0xfd13

/* Encoded menu command; low byte is MENU_CMD_CASTE. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_CASTE 0xfd14

/* Encoded menu command; low byte is MENU_CMD_HISTORY. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_HISTORY 0xfd15

/* Encoded menu command; low byte is MENU_CMD_INFO. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_INFO 0xfd16

/* Encoded menu command; low byte is MENU_CMD_STATUS. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_STATUS 0xfd17

/* Encoded menu command; low byte is MENU_CMD_YARD. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_YARD 0xfd21

/* Encoded menu command; low byte is MENU_CMD_HOUSE. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_HOUSE 0xfd22

/* Encoded menu command; low byte is MENU_CMD_STRATEGIC. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_STRATEGIC 0xfd23

/* Encoded menu command; low byte is MENU_CMD_GRAPHIC. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_GRAPHIC 0xfd24

/* Encoded menu command; low byte is MENU_CMD_SURFACE. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_SURFACE 0xfd26

/* Encoded menu command; low byte is MENU_CMD_BLACK_NEST. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_BLACK_NEST 0xfd27

/* Encoded menu command; low byte is MENU_CMD_RED_NEST. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_RED_NEST 0xfd28

/* Encoded menu command; low byte is MENU_CMD_AUTOTRACK. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_AUTOTRACK 0xfd31

/* Encoded menu command; low byte is MENU_CMD_MUSIC. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_MUSIC 0xfd32

/* Encoded menu command; low byte is MENU_CMD_SOUND_EFFECTS. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_SOUND_EFFECTS 0xfd33

/* Encoded menu command; low byte is MENU_CMD_EVENTS. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_EVENTS 0xfd34

/* Encoded menu command; low byte is MENU_CMD_MESSAGES. Evidence: SHARED kind 6 ID 0x0;
 * src/ui/game_menu.c:88 (ProcMenu). */
#define EVENT_MENU_MESSAGES 0xfd35

/* Encoded menu command; low byte is MENU_CMD_SILLY. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_SILLY 0xfd36

/* Encoded menu command; low byte is MENU_CMD_PAUSE. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_PAUSE 0xfd41

/* Encoded menu command; low byte is MENU_CMD_SLOW. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_SLOW 0xfd43

/* Encoded menu command; low byte is MENU_CMD_NORMAL. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_NORMAL 0xfd44

/* Encoded menu command; low byte is MENU_CMD_FAST. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_FAST 0xfd45

/* Encoded menu command; low byte is MENU_CMD_ULTRA. Evidence: SHARED kind 6 ID 0x0; src/ui/game_menu.c:88
 * (ProcMenu). */
#define EVENT_MENU_ULTRA 0xfd46

/* High byte FE tracks a menu-bar selection. Evidence: src/ui/game_events.c:60 (DoEvent). */
#define EVENT_MENU_BAR_BASE 0xfe00

/* Second menu title; resource menu order File, Window, View, Options, Speed. Evidence:
 * src/ui/game_events.c:21 (g_2CBE). */
#define EVENT_MENU_BAR_WINDOW 0xfe01

/* Third menu title. Evidence: src/ui/game_events.c:21 (g_2CBE). */
#define EVENT_MENU_BAR_VIEW 0xfe02

/* Fourth menu title. Evidence: src/ui/game_events.c:21 (g_2CBE). */
#define EVENT_MENU_BAR_OPTIONS 0xfe03

/* Fifth menu title. Evidence: src/ui/game_events.c:21 (g_2CBE). */
#define EVENT_MENU_BAR_SPEED 0xfe04

/* Calls win_dispatch_desktop_click. Evidence: src/window/events.c:149 (win_translate_pending_event). */
#define EVENT_DESKTOP_CLICK 0xff00

#endif
