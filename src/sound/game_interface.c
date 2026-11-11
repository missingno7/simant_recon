/*
 * Provides the game facing sound and song interface. It initializes the sound driver shell and
 * forwards start, reverse, completion and control requests.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 00DF; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory. Some pairs are HIGH
 * confidence, not confirmed.
 */

int g_1926 = 0;

extern int far fd_55B3_610A;
extern int far f_293A_0006(void);
extern int far f_277E_0000(int mode, int flag);
extern void far WinPrintf(char *fmt, ...);
extern int far * far fd_55B3_74FE;

void far snd_init_driver_once(void)
{
    if (g_1926)
        return;
    if (fd_55B3_610A == -1)
        f_277E_0000(f_293A_0006(), 0);
    else if (fd_55B3_610A == 0)
        return;
    else
        f_277E_0000(fd_55B3_610A, 0);
    WinPrintf("Sound Driver Shell (c) 1991  -- LIB link version\n");
    WinPrintf("Sound Driver reports driver: %d\n%d DAC channels\n%d FM channels\n%d TANDY PSG channels\n%d PS1 PSG channels\n%d COVOX PSG channels\nand %d MIDI channels\n",
              fd_55B3_74FE[0], fd_55B3_74FE[1], fd_55B3_74FE[2], fd_55B3_74FE[4],
              fd_55B3_74FE[3], fd_55B3_74FE[5], fd_55B3_74FE[6]);
    g_1926 = 1;
}

void far f_00DF_0089(void)
{
    WinPrintf("MUSIC INIT!");
}

void far f_00DF_009D(void)
{
    WinPrintf("BEEP");
}

extern int far OptionStates[];
extern void far edit_release_life_tiles(void);
extern void far snd_load_and_start_song(int song);

void far myBeginSong(int song)
{
    if (g_1926 && OptionStates[1]) {
        edit_release_life_tiles();
        snd_load_and_start_song(song);
    }
}

void far f_00DF_00E0(void)
{
}

extern void far snd_start_configured_effect(int sound);

void far myBeginSound(int a, int b, int c)
{
    if (g_1926 && OptionStates[2])
        snd_start_configured_effect(a);
}

void far myBeginSoundReverse(int a, int b, int c)
{
    myBeginSound(a, b, c);
}

int far mySoundIsDone(void)
{
    return 1;
}

extern int far snd_service_and_test_stopped(void);

int far mySongIsDone(void)
{
    if (g_1926 && OptionStates[1])
        return snd_service_and_test_stopped();
    return 1;
}

void far f_00DF_015C(void)
{
}

void far f_00DF_0164(void)
{
}

void far f_00DF_016C(void)
{
    if (g_1926 && OptionStates[1])
        snd_start_configured_effect(1);
}
