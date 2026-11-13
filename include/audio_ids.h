/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_AUDIO_IDS_H
#define SIMANT_AUDIO_IDS_H

/* Configured effect used by CheatKeys, DoAntMoveY, ExchangeLives, ExpDig, GotoMyAnt. Evidence:
 * src/sound/game_interface.c:72 (myBeginSound); src/simulation/life_tiles.c:564 (ExchangeLives);
 * src/simulation/yellow_ant.c:100 (DoAntMoveY). */
#define SND_REJECT 0x1

/* Configured effect used by CheatKeys, EditToolsMenu, MapToolsMenu, MysteryButton, YellowCommand. Evidence:
 * src/sound/game_interface.c:72 (myBeginSound); src/ui/cheats.c:49 (CheatKeys); src/ui/cheats.c:49
 * (CheatKeys). */
#define SND_ACCEPT 0x2

/* Configured effect used by ExpKillAnts. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/experiment_tools.c:429 (ExpKillAnts); src/ui/experiment_tools.c:429 (ExpKillAnts). */
#define SND_EXPERIMENT_KILL 0x9

/* Configured effect used by CheatKeys, DropWall, EatMyFood, MoveSpider. Evidence:
 * src/sound/game_interface.c:72 (myBeginSound); src/simulation/life_tiles.c:1068 (EatMyFood);
 * src/simulation/spider.c:94 (MoveSpider). */
#define SND_FOOD_OR_WALL_ACTION 0xa

/* Configured effect used by ExchangeLives, SetAlarmDropState, YellowCommandKey, processSpider. Evidence:
 * src/sound/game_interface.c:72 (myBeginSound); src/simulation/life_tiles.c:564 (ExchangeLives);
 * src/simulation/life_tiles.c:564 (ExchangeLives). */
#define SND_COMMAND_ACK 0xf

/* Configured effect used by DoDigInR, ExpDig. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/simulation/red_nest.c:753 (DoDigInR); src/ui/experiment_tools.c:213 (ExpDig). */
#define SND_NEST_ENTRANCE 0x12

/* Configured effect used by ExpDig, SetLife. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/simulation/life_tiles.c:328 (SetLife); src/simulation/life_tiles.c:328 (SetLife). */
#define SND_DIG 0x13

/* Configured effect used by ExpIncSmell. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/experiment_tools.c:393 (ExpIncSmell). */
#define SND_SCENT_TOOL 0x1b

/* Configured effect used by DropMyEgg, ExpAddAnt, PickupMyEgg, YellowBirth. Evidence:
 * src/sound/game_interface.c:72 (myBeginSound); src/simulation/life_tiles.c:893 (DropMyEgg);
 * src/simulation/life_tiles.c:1103 (PickupMyEgg). */
#define SND_EGG_ACTION 0x1c

/* Configured effect used by DropMyFood, ExpAddFood, PickupMyFood. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/simulation/life_tiles.c:739 (DropMyFood); src/simulation/life_tiles.c:1127
 * (PickupMyFood). */
#define SND_FOOD_ACTION 0x1d

/* Configured effect used by DoAntLions, DropMyRock, PickupMyRock. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/simulation/life_tiles.c:829 (DropMyRock); src/simulation/life_tiles.c:946
 * (PickupMyRock). */
#define SND_ROCK_ACTION 0x1e

/* Configured effect used by AddFood, ExpAddFood, MapToYellowAnt. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/simulation/world_generation.c:653 (AddFood); src/ui/experiment_tools.c:369
 * (ExpAddFood). */
#define SND_ADD_FOOD 0x20

/* Configured effect used by DrawMower. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/yard_window.c:438 (DrawMower). */
#define SND_MOWER 0x24

/* Configured effect used by AnimYellowFight, LionDialog. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/simulation/yellow_ant.c:335 (AnimYellowFight); src/ui/yellow_commands.c:747
 * (LionDialog). */
#define SND_FIGHT 0x25

/* Configured effect used by LionDialog. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/yellow_commands.c:747 (LionDialog). */
#define SND_ANT_LION_DIALOG 0x26

/* Configured effect used by DropWall. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/experiment_tools.c:164 (DropWall). */
#define SND_WALL_REMOVE 0x28

/* Configured effect used by CheatKeys, DoWater, YellowCommand. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/simulation/food_water_counts.c:179 (DoWater); src/ui/cheats.c:49 (CheatKeys). */
#define SND_RAIN 0x29

/* Configured effect used by YellowDialog. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/yellow_commands.c:800 (YellowDialog). */
#define SND_YELLOW_DIALOG_FIRST_EFFECT 0x2a

/* Configured effect used by EatMyFood, MoveSpider. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/simulation/life_tiles.c:1068 (EatMyFood); src/simulation/life_tiles.c:1068 (EatMyFood). */
#define SND_EAT 0x2c

/* Configured effect used by SpiderDialog, YellowDialog. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/ui/scenario_dialogs.c:558 (SpiderDialog); src/ui/scenario_dialogs.c:558
 * (SpiderDialog). */
#define SND_SPIDER_DIALOG_EFFECT 0x2d

/* Configured effect used by MoveSpider. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/simulation/spider.c:94 (MoveSpider); src/simulation/spider.c:94 (MoveSpider). */
#define SND_SPIDER_MOVE 0x2f

/* Configured effect used by AnimYellowFight, YellowBirth. Evidence: src/sound/game_interface.c:72
 * (myBeginSound); src/simulation/yellow_ant.c:335 (AnimYellowFight); src/ui/yellow_commands.c:355
 * (YellowBirth). */
#define SND_BIRTH_OR_FIGHT 0x31

/* Configured effect used by DoLaserFire. Evidence: src/sound/game_interface.c:72 (myBeginSound);
 * src/ui/yellow_commands.c:178 (DoLaserFire). */
#define SND_LASER 0x37

/* Played at ProcMenu, ShowIntro. Evidence: SOUND kind 18 ID 0x2711; src/ui/game_menu.c:88 (ProcMenu);
 * src/ui/intro_credits.c:235 (ShowIntro). */
#define SONG_INTRO 0x2711

/* Played at EndGameDialog, TryAntTheme. Evidence: SOUND kind 18 ID 0x2713;
 * src/simulation/food_water_counts.c:635 (TryAntTheme); src/ui/scenario_dialogs.c:500 (EndGameDialog). */
#define SONG_ANT_THEME_BASE 0x2713

/* Played at EndGameDialog. Evidence: SOUND kind 18 ID 0x2718; src/ui/scenario_dialogs.c:500
 * (EndGameDialog); src/ui/scenario_dialogs.c:500 (EndGameDialog). */
#define SONG_END_GAME_WIN 0x2718

/* Played at EndGameDialog. Evidence: SOUND kind 18 ID 0x271a; src/ui/scenario_dialogs.c:500
 * (EndGameDialog). */
#define SONG_END_GAME_LOSS 0x271a

/* Played at XferPatch. Evidence: SOUND kind 18 ID 0x2afa; src/ui/view_commands.c:401 (XferPatch). */
#define SONG_PATCH_TRANSFER 0x2afa

/* Played at EditToolsMenu, MapToolsMenu, PlaceQueenInYard, SpecialXfer. Evidence: SOUND kind 18 ID 0x2afb;
 * src/ui/editor_menus.c:63 (EditToolsMenu); src/ui/minimap.c:112 (MapToolsMenu). */
#define SONG_RETURN_TO_ANT 0x2afb

/* Played at YellowBirth. Evidence: SOUND kind 18 ID 0x2afd; src/ui/yellow_commands.c:355 (YellowBirth). */
#define SONG_YELLOW_BIRTH 0x2afd

/* Played at ExchangeLives. Evidence: SOUND kind 18 ID 0x2afe; src/simulation/life_tiles.c:564
 * (ExchangeLives). */
#define SONG_BODY_EXCHANGE 0x2afe

/* Played at YellowCommand. Evidence: SOUND kind 18 ID 0x2b05; src/ui/yellow_commands.c:967 (YellowCommand). */
#define SONG_RECRUIT_FIVE 0x2b05

/* Played at YellowCommand. Evidence: SOUND kind 18 ID 0x2b06; src/ui/yellow_commands.c:967 (YellowCommand). */
#define SONG_RECRUIT_TEN 0x2b06

/* Played at YellowCommand. Evidence: SOUND kind 18 ID 0x2b07; src/ui/yellow_commands.c:967 (YellowCommand). */
#define SONG_RECRUIT_THOUSAND 0x2b07

/* Played at YellowCommand. Evidence: SOUND kind 18 ID 0x2b08; src/ui/yellow_commands.c:967 (YellowCommand). */
#define SONG_RELEASE_RECRUITS 0x2b08

/* Played at YellowCommand. Evidence: SOUND kind 18 ID 0x2b09; src/ui/yellow_commands.c:967 (YellowCommand). */
#define SONG_RELEASE_ALL_RECRUITS 0x2b09

/* Played at StartAttack. Evidence: SOUND kind 18 ID 0x2b0a; src/simulation/strategy.c:244 (StartAttack). */
#define SONG_START_ATTACK 0x2b0a

/* Played at CountAnts. Evidence: SOUND kind 18 ID 0x2b0c; src/simulation/food_water_counts.c:99
 * (CountAnts). */
#define SONG_BLACK_QUEEN_DIED 0x2b0c

/* Played at CountAnts. Evidence: SOUND kind 18 ID 0x2b0d; src/simulation/food_water_counts.c:99
 * (CountAnts). */
#define SONG_RED_QUEEN_DIED 0x2b0d

/* Played at YellowBirth. Evidence: SOUND kind 18 ID 0x4e20; src/ui/yellow_commands.c:355 (YellowBirth). */
#define SONG_YELLOW_BIRTH_INITIAL 0x4e20

/* Played at YellowBirth. Evidence: SOUND kind 18 ID 0x4e21; src/ui/yellow_commands.c:355 (YellowBirth). */
#define SONG_YELLOW_BIRTH_REPLACEMENT 0x4e21

/* Played at SimColonies. Evidence: SOUND kind 18 ID 0x4e22; src/simulation/yard.c:1126 (SimColonies). */
#define SONG_REDS_ELIMINATED 0x4e22

/* Played at SimColonies. Evidence: SOUND kind 18 ID 0x4e23; src/simulation/yard.c:1126 (SimColonies). */
#define SONG_HUMANS_LEAVE_AND_PAYOFF_BASE 0x4e23

/* Played at SimColonies. Evidence: SOUND kind 18 ID 0x4e25; src/simulation/yard.c:1126 (SimColonies). */
#define SONG_FULL_GAME_WIN 0x4e25

/* Played at YellowDeath. Evidence: SOUND kind 18 ID 0x4e27; src/ui/yellow_commands.c:483 (YellowDeath);
 * src/ui/yellow_commands.c:483 (YellowDeath). */
#define SONG_DEATH_VARIATION_BASE 0x4e27

#endif
