/*
 * Provides the game facing sound and song interface. It initializes the sound driver shell and
 * forwards start, reverse, completion and control requests.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident code; segment 00DF; complete original translation unit.
 * Windows: GR, from recorded function pairs in the Windows symbol inventory. Some pairs are HIGH
 * confidence, not confirmed.
 */

int snd_interface_initialized = 0;

extern int far snd_requested_driver_mode;
extern int far snd_probe_preferred_device(void);
extern int far snd_initialize_device_channels(int mode, int flag);
extern void far WinPrintf(char *fmt, ...);
extern int far * far snd_capabilities_pointer;

void far snd_init_driver_once(void)
{
    if (snd_interface_initialized)
        return;
    if (snd_requested_driver_mode == -1)
        snd_initialize_device_channels(snd_probe_preferred_device(), 0);
    else if (snd_requested_driver_mode == 0)
        return;
    else
        snd_initialize_device_channels(snd_requested_driver_mode, 0);
    WinPrintf("Sound Driver Shell (c) 1991  -- LIB link version\n");
    WinPrintf("Sound Driver reports driver: %d\n%d DAC channels\n%d FM channels\n%d TANDY PSG channels\n%d PS1 PSG channels\n%d COVOX PSG channels\nand %d MIDI channels\n",
              snd_capabilities_pointer[0], snd_capabilities_pointer[1], snd_capabilities_pointer[2], snd_capabilities_pointer[4],
              snd_capabilities_pointer[3], snd_capabilities_pointer[5], snd_capabilities_pointer[6]);
    snd_interface_initialized = 1;
}

void far snd_log_music_init(void)
{
    WinPrintf("MUSIC INIT!");
}

void far snd_log_beep(void)
{
    WinPrintf("BEEP");
}

extern int far OptionStates[];
extern void far edit_release_life_tiles(void);
extern void far snd_load_and_start_song(int song);

void far myBeginSong(int song)
{
    if (snd_interface_initialized && OptionStates[1]) {
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
    if (snd_interface_initialized && OptionStates[2])
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
    if (snd_interface_initialized && OptionStates[1])
        return snd_service_and_test_stopped();
    return 1;
}

void far f_00DF_015C(void)
{
}

void far f_00DF_0164(void)
{
}

void far snd_start_effect_one_if_music(void)
{
    if (snd_interface_initialized && OptionStates[1])
        snd_start_configured_effect(1);
}
