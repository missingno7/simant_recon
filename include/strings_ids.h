/* Descriptive constants; names and header grouping are ours, not recovered.
 * No original macro names are claimed. Constants never change the compiled code
 * (docs/codegen-rules.md, "Which names count toward declaration numbers").
 */
#ifndef SIMANT_STRINGS_IDS_H
#define SIMANT_STRINGS_IDS_H

/* Do you want to save your current game before quitting SimAnt\xac?  If you do not save now, any changes
 * made since Evidence: SHARED kind 10 ID 0x80. */
#define TEXT_SAVE_BEFORE_QUITTING 0x80

/* Do you want to save your current game before loading a new SimAnt\xac game?  If you do not save now, any
 * changes  Evidence: SHARED kind 10 ID 0x82. */
#define TEXT_SAVE_BEFORE_LOADING 0x82

/* This copy of SimAnt\xac is registered to:  Evidence: SHARED kind 10 ID 0x83. */
#define TEXT_REGISTERED_TO 0x83

/* Customer ID: Evidence: SHARED kind 10 ID 0x84. */
#define TEXT_CUSTOMER_ID 0x84

/* BackYard View / Surface View / Black Nest View / Red Nest View / Black Nest Marker Pheromone / Black
 * Trail Marker Phe... Evidence: SHARED kind 4 ID 0x3e8; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_WINDOW_TITLES 0x3e8

/* Tutorial Game / Quick Game / Full Game / Experimental Evidence: SHARED kind 4 ID 0x3e9;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_SCENARIO_NAMES 0x3e9

/* Pause / UnPause / Game Paused / Click on another ant to exchange bodies / You have entered the red nest /
 * You need to... Evidence: SHARED kind 4 ID 0x3f2; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_WINDOW_PROMPTS 0x3f2

/* Your health is critical - You must eat / Your health is low - Find some food / Your colony needs food /
 * You need to d... Evidence: SHARED kind 4 ID 0x3fc; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_ADVICE 0x3fc

/* Welcome to the SimAnt Tutorial. / Just follow the on-screen instructions and / you will learn how to
 * play. / In SimAn... Evidence: SHARED kind 4 ID 0x406; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_LEGACY 0x406

/* BPop / BFood / BHealth / SFood / Expired / RPop / RFood / RHealth / Eaten / Killed Evidence: SHARED kind
 * 4 ID 0x41a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_HISTORY_GRAPH_LABELS 0x41a

/* Weird Egg / New Egg / Egg / 1st-Instar / 2nd-Instar / 3rd-Instar / Pupae / Hatching Pupae Evidence:
 * SHARED kind 4 ID 0x44c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_EGG_STAGES 0x44c

/* Egg Tender / Worker / Worker / Worker / Male / Worker / Soldier / Soldier / New Queen / Soldier / Replete
 * / ? / Queen... Evidence: SHARED kind 4 ID 0x44d; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_CASTE_NAMES 0x44d

/* Bored / Nesting / Foraging / Got Food / Dig In / Dig Out / Defense / Attack / Hatching / Egg Laying /
 * Fighting / Alar... Evidence: SHARED kind 4 ID 0x44e; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_ACTIVITY_NAMES 0x44e

/* Nothing / Egg / Nothing / Food / Nothing / Dirt / Nothing / Food / Nothing / Dirt / Nothing / Nothing /
 * Nothing / Not... Evidence: SHARED kind 4 ID 0x44f; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_CARRIED_LOAD_NAMES 0x44f

/* Looks like a\nbit of rain! / This yard\nneeds mowing. / I'm getting hungry\nfrom all this walking. /
 * Gosh, I really\n... Evidence: SHARED kind 4 ID 0x4b0; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_HUMAN_BALLOONS 0x4b0

/* I'm so cool I can\nhardly believe it! / Ants are very stupid!\nThat's why I like em! / This sure
 * beats\nspinning webs... Evidence: SHARED kind 4 ID 0x4ba; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_SPIDER_BALLOONS 0x4ba

/* Take that\nyou fiend! / Eat poison! / Spartan dog! / Termite brain! / Better dead\nthan red! / Wood
 * pulp\nsucker! / S... Evidence: SHARED kind 4 ID 0x4c4; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_BLACK_FIGHT_BALLOONS 0x4c4

/* Your queen mates\nwith termites! / Egg eater! / Spider face! / Human lover! / Up your\nmandibles! / Aphid
 * licker! / B... Evidence: SHARED kind 4 ID 0x4ce; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_RED_FIGHT_BALLOONS 0x4ce

/* Where am I? / Sure is dark\nin here! / Who turned off\nthe lights? / I'm cold! / I wonder\nwhat I am? /
 * Maybe I'll be... Evidence: SHARED kind 4 ID 0x4d8; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_EGG_BALLOONS 0x4d8

/* Being a queen is\nterribly overrated! / Sometimes I think all I\ndo is lay eggs! / Laying eggs
 * is\nincredibly boring!... Evidence: SHARED kind 4 ID 0x4e2; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_QUEEN_BALLOONS 0x4e2

/* Whew! I'm\nexhausted! / I've worked my\nmandibles to the chitin! / Time for a\nvomit break! / I wonder
 * what's\nfor di... Evidence: SHARED kind 4 ID 0x4ec; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_REST_BALLOONS 0x4ec

/* Additional IBM Programming / Lars Norpchen & Rodney Lai /  / Additional Macintosh Programming / Mick
 * Foley & Fred Has... Evidence: SHARED kind 4 ID 0x6a4; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_CREDITS 0x6a4

/* Tutorial.Ant /  /  / SimAnt\xac File Error # / Please refer to the SimAnt\xac Manual for more
 * information. / You can contac... Evidence: SHARED kind 4 ID 0x708; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_MISCELLANEOUS 0x708

/* Big Yellow Hero / Spider Slayer / SimCity\xac Biohazard / Fire Ant / On a mission from Elvis / Aardvark
 * Fodder / Weak Li... Evidence: SHARED kind 4 ID 0x76c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_END_GAME_RATINGS 0x76c

/* You can only transfer to a / new patch in a Full Game. Evidence: SHARED kind 4 ID 0x2710;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TRANSFER_FULL_GAME_ONLY 0x2710

/* It would be suicide to transfer / to another patch now!  You should / increase your population first.
 * Evidence: SHARED kind 4 ID 0x2712; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TRANSFER_POPULATION_TOO_LOW 0x2712

/* Sorry, there is not a / black colony at this location. Evidence: SHARED kind 4 ID 0x2714;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_NO_BLACK_COLONY 0x2714

/* You are transferring to this / place in the yard. Evidence: SHARED kind 4 ID 0x2716;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TRANSFER_TO_YARD 0x2716

/* You are transferring to this / place in the house. Evidence: SHARED kind 4 ID 0x2717;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TRANSFER_TO_HOUSE 0x2717

/* The black queen in this patch has died. Evidence: SHARED kind 4 ID 0x271a;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_BLACK_QUEEN_DIED 0x271a

/* Sorry, you have been defeated by / the reds. Better luck next time. Evidence: SHARED kind 4 ID 0x271b;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEFEATED_BY_REDS 0x271b

/* The red queen in this patch has died. Evidence: SHARED kind 4 ID 0x271c; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_RED_QUEEN_DIED 0x271c

/* Congratulations!  You have defeated / the red menace and won this game. Evidence: SHARED kind 4 ID
 * 0x271d; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEFEATED_REDS 0x271d

/* The black queen in this patch starves  / from lack of nourishment. Evidence: SHARED kind 4 ID 0x271f;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_BLACK_QUEEN_STARVED 0x271f

/* The red queen in this patch starves  / from lack of nourishment. Evidence: SHARED kind 4 ID 0x2720;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_RED_QUEEN_STARVED 0x2720

/* You are now $10,000 richer! / Unfortunately, money is worthless / in this game. Evidence: SHARED kind 4
 * ID 0x2724; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_MONEY_IS_WORTHLESS 0x2724

/* How many Glen Campbells does / it take to eat a llama? Evidence: SHARED kind 4 ID 0x2726;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_GLEN_CAMPBELL_RIDDLE 0x2726

/* GCs = EPs - 2 (or, Elvis Minus Two) Evidence: SHARED kind 4 ID 0x2728; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_ELVIS_MINUS_TWO 0x2728

/* You have been overcome by the / massive onslaught of ants! Your / body is picked clean in seconds.
 * Evidence: SHARED kind 4 ID 0x272a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_ANTS 0x272a

/* Due to a latent fear of being eaten by / ants, you go insane and kill yourself. / You will be
 * reincarnated as an ant. Evidence: SHARED kind 4 ID 0x272c; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_DEATH_MADNESS 0x272c

/* Your brave attack against the / enemy ant is thwarted!  Your head is / amputated by its cruel mandibles.
 * Evidence: SHARED kind 4 ID 0x272e; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_ATTACK_FAILED 0x272e

/* The enemy ant has attacked you! / After an intense wrestling match, / the fiend bites your limbs off.
 * Evidence: SHARED kind 4 ID 0x2730; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_ENEMY_ATTACK 0x2730

/* The inconsiderate human has / stepped on you!  Your tiny body / is crushed to a lifeless pulp. Evidence:
 * SHARED kind 4 ID 0x2732; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_FOOT 0x2732

/* The evil lawn mower has sucked you / into its giant whirling blades! / Your body is reduced to a thin
 * slime. Evidence: SHARED kind 4 ID 0x2734; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_MOWER 0x2734

/* You swim for your life, but are / overcome by the powerful current. / You finally drown in the mud.
 * Evidence: SHARED kind 4 ID 0x2736; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_DROWNED 0x2736

/* After going berserk with hunger, / your starved and tortured body / reaches the limits of endurance.
 * Evidence: SHARED kind 4 ID 0x2738; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_STARVED 0x2738

/* You are covered with insecticide! / You convulse and die as the deadly / nerve toxin destroys your body.
 * Evidence: SHARED kind 4 ID 0x273a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_INSECTICIDE 0x273a

/* You fell into an ant lion trap! / The ugly brute toys with your puny / body before sucking your guts out.
 * Evidence: SHARED kind 4 ID 0x273c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_ANT_LION 0x273c

/* You have been electrocuted. Evidence: SHARED kind 4 ID 0x273d; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_DEATH_ELECTROCUTED 0x273d

/* Congratulations! / The spider has been killed / by the ants. Evidence: SHARED kind 4 ID 0x273e;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_SPIDER_KILLED 0x273e

/* Your guts are dissolved and / then drained away as you / are desiccated by the spider. Evidence: SHARED
 * kind 4 ID 0x273f; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_SPIDER_DRAINED 0x273f

/* You writhe in burning agony / as the spider\u2552s deadly venom / flows through your body. Evidence:
 * SHARED kind 4 ID 0x2740; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_DEATH_SPIDER_VENOM 0x2740

/* The ants have surrounded and / killed an ant lion! They tear / its pulpy body apart and eat it. Evidence:
 * SHARED kind 4 ID 0x2742; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_ANT_LION_KILLED 0x2742

/* Congratulations, the red / ants have been eliminated / from the yard. Evidence: SHARED kind 4 ID 0x2744;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_REDS_ELIMINATED_FROM_YARD 0x2744

/* Now you just have to eliminate the red ants / from the yard to win the Full Game. Evidence: SHARED kind 4
 * ID 0x2745; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_ELIMINATE_REDS_TO_WIN 0x2745

/* Congratulations, the humans have / been driven out of the house. Evidence: SHARED kind 4 ID 0x2746;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_HUMANS_DRIVEN_OUT 0x2746

/* Now if you can take over the  / house you will win the Full Game. Evidence: SHARED kind 4 ID 0x2747;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TAKE_HOUSE_TO_WIN 0x2747

/* The black ants have no queens, / breeders or eggs remaining.  / There is no way to reproduce now. /
 * Sorry, you have l... Evidence: SHARED kind 4 ID 0x2748; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_NO_BLACK_BREEDERS 0x2748

/* Congratulations!  By defeating the / red ants and invading the house / you have won the Full Game.
 * Evidence: SHARED kind 4 ID 0x2749; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_FULL_GAME_WON 0x2749

/* There are no more ants in this colony. / You must select a new black colony / in the yard or house to
 * continue. Evidence: SHARED kind 4 ID 0x274a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_SELECT_ANOTHER_COLONY 0x274a

/* You have been transferred to an / existing ant. Evidence: SHARED kind 4 ID 0x274b;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TRANSFERRED_TO_EXISTING_ANT 0x274b

/* Welcome to the SimAnt Tutorial. / Just follow the on-screen instructions and / you will learn how to play
 * the game. Evidence: SHARED kind 4 ID 0x2af8; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_WELCOME 0x2af8

/* In SimAnt you are the yellow ant that / you see in the window before you. / First, you will learn to
 * control your ant. Evidence: HCEGANT kind 4 ID 0x2afa; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_YOU_ARE_YELLOW_ANT 0x2afa

/* Try double-clicking somewhere / in the brown dirt near the / yellow ant. Evidence: HCEGANT kind 4 ID
 * 0x2afc; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_TRY_DIGGING 0x2afc

/* Good, you have just learned / how to dig a tunnel. Try digging / some more to get the hang of it.
 * Evidence: SHARED kind 4 ID 0x2afe; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_LEARNED_DIGGING 0x2afe

/* Now go outside and explore the surface. / Double-click in the blue area at the top of / the window to dig
 * a tunnel to... Evidence: HCEGANT kind 4 ID 0x2b00; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_GO_OUTSIDE 0x2b00

/* Now you're outside! / This is called the Surface View. / Note: You can die up here. Evidence: SHARED kind
 * 4 ID 0x2b02; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_SURFACE_VIEW 0x2b02

/* To move on the surface, just click / on the ground and you will move there. / Try it! Evidence: SHARED
 * kind 4 ID 0x2b04; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_MOVE_ON_SURFACE 0x2b04

/* That's right.  Now click on your ant  / to re-center it in the window. Evidence: SHARED kind 4 ID 0x2b06;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RECENTER_ON_ANT 0x2b06

/* Good.  Now here's another way to scroll the screen. / Move the mouse cursor to the far edge of the
 * screen, /  in the ... Evidence: SHARED kind 4 ID 0x2b08; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_TUTORIAL_SCROLL_SCREEN 0x2b08

/* Now it's about time to find some  / food for your colony. Under the / Window Menu, select MAP. Evidence:
 * SHARED kind 4 ID 0x2b0a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_OPEN_MAP 0x2b0a

/* This window is a view of the whole patch. The green / dots in this window are food.  The yellow dot is /
 * your ant.  Y... Evidence: HCEGANT kind 4 ID 0x2b0c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_MAP_OVERVIEW 0x2b0c

/* Get a bearing on which way the food is located in / the patch.  Then select EDIT under the Window Menu /
 * to bring up ... Evidence: SHARED kind 4 ID 0x2b0e; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_EDIT 0x2b0e

/* Now try to get to the food. When you  / get to the food, move onto a piece. Evidence: SHARED kind 4 ID
 * 0x2b10; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_REACH_FOOD 0x2b10

/* Very good, you made it. You are / probably hungry by now, so / double-click on a piece of food. Evidence:
 * SHARED kind 4 ID 0x2b12; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_EAT_FOOD 0x2b12

/* That tasted good, didn't it? / Now you feel like a new ant. Evidence: SHARED kind 4 ID 0x2b14;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_HEALTH_RESTORED 0x2b14

/* Now it's time to bring a piece of the food / back to your colony.  Double-click on / another piece to
 * pick it up. Evidence: SHARED kind 4 ID 0x2b16; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_PICK_UP_FOOD 0x2b16

/* Notice how this time you picked up the food instead / of eating it.  Your ant only eats when its health
 * is / below th... Evidence: SHARED kind 4 ID 0x2b18; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_FOOD_HEALTH_SETPOINT 0x2b18

/* Now try to get back into your nest. / It should be somewhere to the left / of your current position.
 * Evidence: SHARED kind 4 ID 0x2b1a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_NEST 0x2b1a

/* Good, you made it.  Now double-click / in the tunnel to drop the food. Evidence: SHARED kind 4 ID 0x2b1c;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_DROP_FOOD 0x2b1c

/* OK, now let's go back to the / surface and try a few more things. Evidence: SHARED kind 4 ID 0x2b1e;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_SURFACE 0x2b1e

/* Look for a small rock on the surface / that looks like this. Then double- / click on it to pick it up.
 * Evidence: SHARED kind 4 ID 0x2b20; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_PICK_UP_ROCK 0x2b20

/* Good.  Now double-click somewhere / to move there and drop the rock. Evidence: SHARED kind 4 ID 0x2b22;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_DROP_ROCK 0x2b22

/* That's right.  You can move these / pebbles to build crude walls / and barriers for colony defense.
 * Evidence: SHARED kind 4 ID 0x2b24; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_PEBBLE_WALLS 0x2b24

/* Now click and hold on your ant. / Then select RECRUIT 10 from / the pop-up menu that appears. Evidence:
 * SHARED kind 4 ID 0x2b26; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RECRUIT_TEN 0x2b26

/* Good.  You have just recruited / a few black ants to follow / your ant. Evidence: SHARED kind 4 ID
 * 0x2b28; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RECRUITED_ANTS 0x2b28

/* Move around on the surface and notice / how the recruited ants follow you. Evidence: SHARED kind 4 ID
 * 0x2b2a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_FOLLOWERS 0x2b2a

/* Now, tap the ZERO key / and move your ant back / and forth over an area. Evidence: SHARED kind 4 ID
 * 0x2b2c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_MOVE_WITH_ALARM 0x2b2c

/* That's it.  You are dropping an alarm scent that / makes your ants defend an area. Now, tap the / ZERO
 * key again to s... Evidence: SHARED kind 4 ID 0x2b2e; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_ALARM_SCENT 0x2b2e

/* Next you will learn how to use / the EXCHANGE command to control / a different ant. Evidence: SHARED kind
 * 4 ID 0x2b30; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_EXCHANGE_INTRO 0x2b30

/* Click and hold on your ant and select / EXCHANGE from the pop-up menu, then click / on a nearby black
 * ant. Evidence: SHARED kind 4 ID 0x2b32; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_SELECT_EXCHANGE 0x2b32

/* Good.  The ant you have selected is now  / your ant. You can control any / black ant with this command.
 * Evidence: SHARED kind 4 ID 0x2b34; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_NOW_CONTROL_OTHER_ANT 0x2b34

/* Now go back to the MAP / Window.  Select MAP from / the Window Menu. Evidence: SHARED kind 4 ID 0x2b36;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_MAP 0x2b36

/* Now let's see where you are in the world of SimAnt. / Click on the YARD icon at the lower / left of the
 * MAP Window. Evidence: SHARED kind 4 ID 0x2b38; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_OPEN_YARD 0x2b38

/* The flashing area on the right / side of the yard is where your / current colony is located. Evidence:
 * SHARED kind 4 ID 0x2b3a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_CURRENT_PATCH 0x2b3a

/* This screen is where you will / reproduce and spread new colonies / across the yard in the Full Game.
 * Evidence: SHARED kind 4 ID 0x2b3c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_YARD_REPRODUCTION 0x2b3c

/* Now click on the button labeled / HOUSE at the lower left. Evidence: SHARED kind 4 ID 0x2b3e;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_OPEN_HOUSE 0x2b3e

/* In the Full Game, in addition to eliminating / the red ants, your objective will be to  / invade and take
 * over the in... Evidence: SHARED kind 4 ID 0x2b40; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_HOUSE_OBJECTIVE 0x2b40

/* Now, click on the button at the lower  / left labeled PATCH to return to the / Surface View of your
 * colony. Evidence: SHARED kind 4 ID 0x2b42; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_PATCH 0x2b42

/* Now click on the small icon at the lower / center of the MAP Window that looks / like a triangle
 * containing the lette... Evidence: SHARED kind 4 ID 0x2b44; src/resources/game_strings.c:102
 * (LoadStringAnt). */
#define STR_TUTORIAL_OPEN_BEHAVIOR 0x2b44

/* That's it.  This is the Behavior / Control Window.  You control the / activity of your black ants here.
 * Evidence: SHARED kind 4 ID 0x2b46; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_BEHAVIOR_WINDOW 0x2b46

/* Click and drag the small circle inside the triangle. This is how you set / a new ratio.  This ratio is
 * the percentage... Evidence: SHARED kind 4 ID 0x2b48; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_DRAG_BEHAVIOR_KNOB 0x2b48

/* Good.  Now let's return to the MAP / Window.  Either click on it or select / MAP from the Window Menu.
 * Evidence: SHARED kind 4 ID 0x2b4a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_MAP_AGAIN 0x2b4a

/* Now click and hold on the icon with / the question mark ("?"), below. Release  / the button after viewing
 * this pop-up. Evidence: SHARED kind 4 ID 0x2b4c; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_OPEN_HELP 0x2b4c

/* These icons in SimAnt are HELP buttons. / They also appear in most of the other windows.  / The Help
 * pop-ups describe... Evidence: SHARED kind 4 ID 0x2b4e; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_HELP_BUTTONS 0x2b4e

/* Take a look at the bar graphs at the lower / right.  These show the red and black colony / populations
 * (P) and health... Evidence: SHARED kind 4 ID 0x2b50; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_COLONY_BARS 0x2b50

/* Click and hold in this bar graph / area to see a detailed breakdown / of the population for each colony.
 * Evidence: SHARED kind 4 ID 0x2b52; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_POPULATION_BREAKDOWN 0x2b52

/* Now, look at the caste control. / Click on the triangle containing / the letter "C" below. Evidence:
 * SHARED kind 4 ID 0x2b54; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_OPEN_CASTE 0x2b54

/* This window controls which types of / ants (castes) are produced by your queen. / It works just like the
 * Behavior Win... Evidence: SHARED kind 4 ID 0x2b56; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_CASTE_WINDOW 0x2b56

/* Return to the EDIT window now. / Select EDIT from the Window Menu. Evidence: SHARED kind 4 ID 0x2b58;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RETURN_TO_EDIT_AGAIN 0x2b58

/* Click on the yellow ant icon at the left / to center the window on your ant. Evidence: HCEGANT kind 4 ID
 * 0x2b5a; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_CENTER_ON_YELLOW_ANT 0x2b5a

/* Now it's time to attempt to attack  / the red colony across the map. Evidence: SHARED kind 4 ID 0x2b5c;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_ATTACK_RED_COLONY 0x2b5c

/* Let's get some help.  Click and hold on / the yellow ant and select "RECRUIT 10" / from the menu.  Do
 * this about 5 ti... Evidence: SHARED kind 4 ID 0x2b5e; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_RECRUIT_FIFTY 0x2b5e

/* Good.  Now you have recruited  / about 50 ants for our attack. Evidence: SHARED kind 4 ID 0x2b60;
 * src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_READY_TO_ATTACK 0x2b60

/* Now head to the right and look for  / the red nest entrance.  Try to / avoid the red ants. Evidence:
 * HCEGANT kind 4 ID 0x2b62; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_FIND_RED_NEST 0x2b62

/* Congratulations, you have made it into the red / nest. You must be getting the hang of this. Evidence:
 * SHARED kind 4 ID 0x2b64; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_ENTERED_RED_NEST 0x2b64

/* Too bad.  Your attack on the red ants has / failed.  You just need more practice. Evidence: SHARED kind 4
 * ID 0x2b66; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_ATTACK_FAILED 0x2b66

/* This is the end of the SimAnt tutorial.  There is much more to / discover.  There is also an on-line
 * guide to SimAnt ... Evidence: SHARED kind 4 ID 0x2b68; src/resources/game_strings.c:102 (LoadStringAnt). */
#define STR_TUTORIAL_END 0x2b68

#endif
