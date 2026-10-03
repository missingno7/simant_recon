#ifndef SIMANT_WHOLE_PROGRAM_ASM_UTILITIES_H
#define SIMANT_WHOLE_PROGRAM_ASM_UTILITIES_H

#include <stdint.h>

/* Whole-program link adapters use these original symbol spellings and DOS
 * scalar widths. Pointer values are native pointers; DOS segment/offset
 * aliasing and 64 KiB wrap are not part of this adapter ABI. */
uint16_t f_1959_0002(uint16_t value);
uint32_t f_1959_000C(uint32_t value);
uint8_t *f_24FA_0004(uint8_t *start, uint8_t value, uint16_t count);
void f_24FA_0029(uint8_t *dst, const uint8_t *src, int16_t width, int16_t height);
void f_24FA_00A0(uint8_t *bytes, int16_t count);
/* Original entry is INT 3 with no normal return. Native invariant failure. */
_Noreturn void f_24FA_00B5(void);
void f_2650_0107(uint8_t *bytes, int16_t count);

/* Scalar contracts recovered from the original root assembly modules. */
uint16_t simant_dos_swap_word(uint16_t value);
uint32_t simant_dos_swap_dword(uint32_t value);

/* Search starts at start and proceeds toward lower addresses for count bytes.
 * The caller must provide a live object covering start[-(count-1)..0].
 * count==0 is excluded: the original REPNE SCASB leaves its result dependent
 * on incoming ZF when CX is initially zero. */
const uint8_t *simant_dos_reverse_find_byte(const uint8_t *start,
                                             uint8_t value,
                                             uint16_t count);

/* In-place bytewise NOT. The original LOOP instruction executes 65,536
 * iterations for a zero 16-bit count; count==0 therefore requires a writable
 * 65,536-byte span. */
void simant_dos_invert_bytes(uint8_t *bytes, uint16_t count);

/* Expand ceil(width/2) bytes per row from 2-bit source groups. Each source
 * byte contributes four successive table-mapped output bytes; the final
 * source byte's unused low groups are ignored. width/height must be positive.
 * The supplied spans must cover output=(ceil(width/2)*height) and input=
 * (ceil(ceil(width/2)/4)*height) bytes respectively. This captures the
 * original byte transform only; it does not assert a visual pixel geometry. */
void simant_dos_expand_2bit_bytes(uint8_t *dst,
                                  const uint8_t *src,
                                  int16_t width,
                                  int16_t height);

/* Source m2650's clear helper has a one-byte-before-pointer write when the
 * 16-bit count is zero. This portable entry admits positive sizes only. */
void simant_dos_clear_bytes(uint8_t *bytes, uint16_t count);

#endif
