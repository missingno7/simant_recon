#include "portable/whole_program/platform/audio_state.h"

#include <stdio.h>
#include <string.h>

extern int16_t f_277E_017D(void);
extern PortableWholeAudioInstrumentEntry fd_55B3_0C42[56];
extern int16_t fd_55B3_74C0;

/* These are the source module's externally owned startup scalars. The narrow
 * initializer test provides deterministic values, not host-device detection. */
int16_t fd_55B3_74AD = 9;
int16_t fd_55B3_6B9C;

int main(void)
{
    unsigned i;

    fd_50F6_4A48 = 2;
    fd_50F6_4A4C = 0;
    if (f_277E_017D() != 1) {
        fputs("source mode-1 initializer rejected\n", stderr);
        return 1;
    }
    if (fd_50F6_01F0[1] != 2 || fd_50F6_4A4C != 2 ||
        fd_50F6_4A4E[0].type != 1 || fd_50F6_4A4E[0].num != 0 ||
        fd_50F6_4A4E[1].type != 1 || fd_50F6_4A4E[1].num != 1 ||
        fd_55B3_6B9C != fd_55B3_74AD || fd_55B3_74C0 != 0x40) {
        fputs("source mode-1 channel/provider state mismatch\n", stderr);
        return 2;
    }
    for (i = 0; i < 56; ++i) {
        if (fd_50F6_0000[i].kind != fd_55B3_0C42[i].kind ||
            fd_50F6_0000[i].payload != fd_55B3_0C42[i].payload) {
            fprintf(stderr, "shared bank row %u did not reach canonical state\n", i);
            return 3;
        }
    }
    puts("PASS source f_277E_017D initialized canonical mode/channel state and copied all 56 DATA rows");
    return 0;
}
