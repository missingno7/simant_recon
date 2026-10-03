/* Original ASM DATA objects, not zero-filled guesses:
 *   S02:m3126 _DATA starts at DGROUP:219C; the unlabeled `dw 0` at +8 is 21A4.
 *   root:m1B4E defines _g_3D20 db 128 dup (0).
 * Byte symbols preserve the original C/ASM external names. The same storage
 * has the wider typed views used by original word operations.
 */
#include "asm_display_data_v1.h"

#if !defined(__GNUC__)
#error "This native alias provider requires GCC-compatible symbol aliases"
#endif

_Static_assert(sizeof(SimAsmDisplayWord) == 2, "DGROUP word object");
_Static_assert(sizeof(SimAsmBitmapRowBuffer) == 128, "ASM row buffer extent");

SimAsmDisplayWord sim_asm_g21a4 = { .word = 0 };
SimAsmBitmapRowBuffer sim_asm_g3d20 = { .bytes = { 0 } };

/* The real C consumers declare these source symbols as char / char[]. */
extern char g_21A4 __attribute__((alias("sim_asm_g21a4")));
extern char g_3D20[128] __attribute__((alias("sim_asm_g3d20")));

uint16_t sim_asm_g21a4_read_word(void)
{
    return sim_asm_g21a4.word;
}

void sim_asm_g21a4_write_word(uint16_t value)
{
    sim_asm_g21a4.word = value;
}
