/* Readable native views of two original ASM-owned display DATA objects.
 * Source anchors and consumers are pinned by tests/whole_program/asm_display_data_owner_v1.
 */
#ifndef SIMANT_ASM_DISPLAY_DATA_V1_H
#define SIMANT_ASM_DISPLAY_DATA_V1_H

#include <stdint.h>

typedef union {
    uint16_t word;
    struct {
        uint8_t low;
        uint8_t high;
    } byte;
} SimAsmDisplayWord;

typedef union {
    uint8_t bytes[128];
    uint16_t words[64];
} SimAsmBitmapRowBuffer;

extern SimAsmDisplayWord sim_asm_g21a4;
extern SimAsmBitmapRowBuffer sim_asm_g3d20;
extern char g_21A4;
extern char g_3D20[128];

/* Word access models S01 assembly PUSH/POP/MOV WORD PTR uses. */
uint16_t sim_asm_g21a4_read_word(void);
void sim_asm_g21a4_write_word(uint16_t value);

#endif
