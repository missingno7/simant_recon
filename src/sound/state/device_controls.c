/*
 * Defines sound device selection and channel control words. The common sound layer and device
 * backends read or update these six values.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * Historical COMDEF identity remains unknown.
 */

int far fd_50F6_4A46;
int far snd_sample_channel_count;
int far fd_50F6_4A4A;
int far snd_voice_build_index;
int far snd_device_io_base;
int far snd_opl_volume_bias;
