; Sample-playback timer interrupt handler (root module, code frame 28BC;
; linear 0x28BC0-0x290DD) and its DGROUP data (55B3:693E-74C0).
;
; Genuine assembly (sound driver library).  The INT 8 handlers mix up to four
; 8-bit sample channels through per-channel volume tables (xlat) and send the
; result through an output routine selected by a near vector (speaker, LPT DAC,
; AdLib, Sound Blaster DSP, ports 200h/222h).  Every 16th tick the old INT 8
; vector is chained; the MIDI sequencer (f_284A_067F) runs on a private stack.
; The code segment holds its own data (old vector, saved SS:SP, the private
; stack pointer, a re-entry counter), the handlers end in iret, and the C
; entry points address their arguments through "add bp,6".  MSC 6.00 produces
; none of this (rule ASM-1).

DGROUP          group   _DATA

                extrn   _f_284A_067F:far


                public  _g_693C
                public  _fd_55B3_6B42
                public  _fd_55B3_6B4A
                public  _fd_55B3_6B9C
                public  _fd_55B3_6BA0
                public  _fd_55B3_74AD
                public  _fd_55B3_74AF
                public  _fd_55B3_74B1
                public  _fd_55B3_74B3
                public  _fd_55B3_74B5
                public  _fd_55B3_74B7
                public  _fd_55B3_74B9

CHANNELS        equ     4
CHAN_SIZE       equ     14h             ; channel record (see f_290D_0098)

_DATA           segment word public 'DATA'
_g_693C         dw      3BCh            ; LPT DAC port (set by f_277E_0760 from the BIOS)
isr_stack       db      200h dup (0)    ; private stack of the sequencer tick
isr_stack_top   label   word
g_6B3E          dw      10h             ; ticks to the next sequencer call
g_6B40          dw      10h             ; reload of g_6B3E
_fd_55B3_6B42   dw      2               ; sequencer delay (returned by f_284A_067F)
g_6B44          dw      1               ; channel 0 sample (4-channel mixer)
                dw      1
g_6B48          dw      3               ; speaker output state (0, 1, 2)
_fd_55B3_6B4A   dw      10h             ; DAC port base (out to port + 1)
_fd_55B3_6B4C label byte
g_6B4C          db      CHAN_SIZE dup (0)
_fd_55B3_6B4E equ g_6B4C+2
                public _fd_55B3_6B4C, _fd_55B3_6B4E
g_6B60          db      CHAN_SIZE dup (0)
g_6B74          db      CHAN_SIZE dup (0)
g_6B88          db      CHAN_SIZE dup (0)
_fd_55B3_6B9C   dw      offset out_speaker      ; current output routine
                public _fd_55B3_6B9E
_fd_55B3_6B9E label word
g_6B9E          dw      offset DGROUP:vol_tab   ; volume table base
_fd_55B3_6BA0   dw      0               ; Sound Blaster DSP write port
                dw      0
; AdLib output level table (indexed by sample value, read by f_2815_0165 in steps of 2)
                public _fd_55B3_6BA4
_fd_55B3_6BA4 label byte
g_6BA4          label   byte
                db      40h, 38h, 33h, 30h, 2Dh, 2Bh, 29h, 28h, 26h, 25h, 24h, 23h, 22h, 21h, 20h, 20h
                db      1Fh, 1Eh, 1Eh, 1Dh, 1Ch, 1Ch, 1Bh, 1Bh, 1Ah, 1Ah, 1Ah, 19h, 19h, 18h, 18h, 18h
                db      17h, 17h, 16h, 16h, 16h, 16h, 15h, 15h, 15h, 14h, 14h, 14h, 14h, 13h, 13h, 13h
                db      13h, 12h, 12h, 12h, 12h, 11h, 11h, 11h, 11h, 11h, 10h, 10h, 10h, 10h, 10h, 10h
                db      0Fh, 0Fh, 0Fh, 0Fh, 0Fh, 0Eh, 0Eh, 0Eh, 0Eh, 0Eh, 0Eh, 0Eh, 0Dh, 0Dh, 0Dh, 0Dh
                db      0Dh, 0Dh, 0Ch, 0Ch, 0Ch, 0Ch, 0Ch, 0Ch, 0Ch, 0Ch, 0Bh, 0Bh, 0Bh, 0Bh, 0Bh, 0Bh
                db      0Bh, 0Bh, 0Ah, 0Ah, 0Ah, 0Ah, 0Ah, 0Ah, 0Ah, 0Ah, 0Ah, 09h, 09h, 09h, 09h, 09h
                db      09h, 09h, 09h, 09h, 09h, 08h, 08h, 08h, 08h, 08h, 08h, 08h, 08h, 08h, 08h, 07h
                db      07h, 07h, 07h, 07h, 07h, 07h, 07h, 07h, 07h, 07h, 07h, 06h, 06h, 06h, 06h, 06h
                db      06h, 06h, 06h, 06h, 06h, 06h, 06h, 05h, 05h, 05h, 05h, 05h, 05h, 05h, 05h, 05h
                db      05h, 05h, 05h, 05h, 05h, 04h, 04h, 04h, 04h, 04h, 04h, 04h, 04h, 04h, 04h, 04h
                db      04h, 04h, 04h, 04h, 03h, 03h, 03h, 03h, 03h, 03h, 03h, 03h, 03h, 03h, 03h, 03h
                db      03h, 03h, 03h, 03h, 02h, 02h, 02h, 02h, 02h, 02h, 02h, 02h, 02h, 02h, 02h, 02h
                db      02h, 02h, 02h, 02h, 02h, 02h, 01h, 01h, 01h, 01h, 01h, 01h, 01h, 01h, 01h, 01h
                db      01h, 01h, 01h, 01h, 01h, 01h, 01h, 01h, 01h, 00h, 00h, 00h, 00h, 00h, 00h, 00h
                db      00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h, 00h
; eight 256-byte volume tables: row 0 is the identity, row k compresses
; the sample towards 80h
vol_tab         label   byte
sample          =       0
                rept    256
                db      sample
sample          =       sample + 1
                endm
                db      10h, 11h, 12h, 12h, 13h, 14h, 15h, 16h, 17h, 18h, 19h, 1Ah, 1Ah, 1Bh, 1Ch, 1Dh
                db      1Eh, 1Fh, 20h, 21h, 21h, 22h, 23h, 24h, 25h, 26h, 27h, 28h, 28h, 29h, 2Ah, 2Bh
                db      2Ch, 2Dh, 2Eh, 2Fh, 30h, 30h, 31h, 32h, 33h, 34h, 35h, 36h, 37h, 37h, 38h, 39h
                db      3Ah, 3Bh, 3Ch, 3Dh, 3Eh, 3Eh, 3Fh, 40h, 41h, 42h, 43h, 44h, 45h, 46h, 46h, 47h
                db      48h, 49h, 4Ah, 4Bh, 4Ch, 4Dh, 4Dh, 4Eh, 4Fh, 50h, 51h, 52h, 53h, 54h, 54h, 55h
                db      56h, 57h, 58h, 59h, 5Ah, 5Bh, 5Ch, 5Ch, 5Dh, 5Eh, 5Fh, 60h, 61h, 62h, 63h, 63h
                db      64h, 65h, 66h, 67h, 68h, 69h, 6Ah, 6Ah, 6Bh, 6Ch, 6Dh, 6Eh, 6Fh, 70h, 71h, 72h
                db      72h, 73h, 74h, 75h, 76h, 77h, 78h, 79h, 79h, 7Ah, 7Bh, 7Ch, 7Dh, 7Eh, 7Fh, 80h
                db      80h, 80h, 81h, 82h, 83h, 84h, 85h, 86h, 87h, 87h, 88h, 89h, 8Ah, 8Bh, 8Ch, 8Dh
                db      8Eh, 8Eh, 8Fh, 90h, 91h, 92h, 93h, 94h, 95h, 96h, 96h, 97h, 98h, 99h, 9Ah, 9Bh
                db      9Ch, 9Dh, 9Dh, 9Eh, 9Fh, 0A0h, 0A1h, 0A2h, 0A3h, 0A4h, 0A4h, 0A5h, 0A6h, 0A7h, 0A8h, 0A9h
                db      0AAh, 0ABh, 0ACh, 0ACh, 0ADh, 0AEh, 0AFh, 0B0h, 0B1h, 0B2h, 0B3h, 0B3h, 0B4h, 0B5h, 0B6h, 0B7h
                db      0B8h, 0B9h, 0BAh, 0BAh, 0BBh, 0BCh, 0BDh, 0BEh, 0BFh, 0C0h, 0C1h, 0C2h, 0C2h, 0C3h, 0C4h, 0C5h
                db      0C6h, 0C7h, 0C8h, 0C9h, 0C9h, 0CAh, 0CBh, 0CCh, 0CDh, 0CEh, 0CFh, 0D0h, 0D0h, 0D1h, 0D2h, 0D3h
                db      0D4h, 0D5h, 0D6h, 0D7h, 0D8h, 0D8h, 0D9h, 0DAh, 0DBh, 0DCh, 0DDh, 0DEh, 0DFh, 0DFh, 0E0h, 0E1h
                db      0E2h, 0E3h, 0E4h, 0E5h, 0E6h, 0E6h, 0E7h, 0E8h, 0E9h, 0EAh, 0EBh, 0ECh, 0EDh, 0EEh, 0EEh, 0EFh
                db      20h, 21h, 22h, 23h, 23h, 24h, 25h, 26h, 26h, 27h, 28h, 29h, 29h, 2Ah, 2Bh, 2Ch
                db      2Ch, 2Dh, 2Eh, 2Fh, 2Fh, 30h, 31h, 32h, 32h, 33h, 34h, 35h, 35h, 36h, 37h, 38h
                db      38h, 39h, 3Ah, 3Bh, 3Bh, 3Ch, 3Dh, 3Eh, 3Eh, 3Fh, 40h, 41h, 41h, 42h, 43h, 44h
                db      44h, 45h, 46h, 47h, 47h, 48h, 49h, 4Ah, 4Ah, 4Bh, 4Ch, 4Dh, 4Dh, 4Eh, 4Fh, 50h
                db      50h, 51h, 52h, 53h, 53h, 54h, 55h, 56h, 56h, 57h, 58h, 59h, 59h, 5Ah, 5Bh, 5Ch
                db      5Ch, 5Dh, 5Eh, 5Fh, 5Fh, 60h, 61h, 62h, 62h, 63h, 64h, 65h, 65h, 66h, 67h, 68h
                db      68h, 69h, 6Ah, 6Bh, 6Bh, 6Ch, 6Dh, 6Eh, 6Eh, 6Fh, 70h, 71h, 71h, 72h, 73h, 74h
                db      74h, 75h, 76h, 77h, 77h, 78h, 79h, 7Ah, 7Ah, 7Bh, 7Ch, 7Dh, 7Dh, 7Eh, 7Fh, 80h
                db      80h, 80h, 81h, 82h, 83h, 83h, 84h, 85h, 86h, 86h, 87h, 88h, 89h, 89h, 8Ah, 8Bh
                db      8Ch, 8Ch, 8Dh, 8Eh, 8Fh, 8Fh, 90h, 91h, 92h, 92h, 93h, 94h, 95h, 95h, 96h, 97h
                db      98h, 98h, 99h, 9Ah, 9Bh, 9Bh, 9Ch, 9Dh, 9Eh, 9Eh, 9Fh, 0A0h, 0A1h, 0A1h, 0A2h, 0A3h
                db      0A4h, 0A4h, 0A5h, 0A6h, 0A7h, 0A7h, 0A8h, 0A9h, 0AAh, 0AAh, 0ABh, 0ACh, 0ADh, 0ADh, 0AEh, 0AFh
                db      0B0h, 0B0h, 0B1h, 0B2h, 0B3h, 0B3h, 0B4h, 0B5h, 0B6h, 0B6h, 0B7h, 0B8h, 0B9h, 0B9h, 0BAh, 0BBh
                db      0BCh, 0BCh, 0BDh, 0BEh, 0BFh, 0BFh, 0C0h, 0C1h, 0C2h, 0C2h, 0C3h, 0C4h, 0C5h, 0C5h, 0C6h, 0C7h
                db      0C8h, 0C8h, 0C9h, 0CAh, 0CBh, 0CBh, 0CCh, 0CDh, 0CEh, 0CEh, 0CFh, 0D0h, 0D1h, 0D1h, 0D2h, 0D3h
                db      0D4h, 0D4h, 0D5h, 0D6h, 0D7h, 0D7h, 0D8h, 0D9h, 0DAh, 0DAh, 0DBh, 0DCh, 0DDh, 0DDh, 0DEh, 0DFh
                db      30h, 30h, 31h, 32h, 32h, 33h, 34h, 34h, 35h, 36h, 36h, 37h, 37h, 38h, 39h, 39h
                db      3Ah, 3Bh, 3Bh, 3Ch, 3Ch, 3Dh, 3Eh, 3Eh, 3Fh, 40h, 40h, 41h, 41h, 42h, 43h, 43h
                db      44h, 45h, 45h, 46h, 47h, 47h, 48h, 48h, 49h, 4Ah, 4Ah, 4Bh, 4Ch, 4Ch, 4Dh, 4Dh
                db      4Eh, 4Fh, 4Fh, 50h, 51h, 51h, 52h, 53h, 53h, 54h, 54h, 55h, 56h, 56h, 57h, 58h
                db      58h, 59h, 59h, 5Ah, 5Bh, 5Bh, 5Ch, 5Dh, 5Dh, 5Eh, 5Eh, 5Fh, 60h, 60h, 61h, 62h
                db      62h, 63h, 64h, 64h, 65h, 65h, 66h, 67h, 67h, 68h, 69h, 69h, 6Ah, 6Ah, 6Bh, 6Ch
                db      6Ch, 6Dh, 6Eh, 6Eh, 6Fh, 6Fh, 70h, 71h, 71h, 72h, 73h, 73h, 74h, 75h, 75h, 76h
                db      76h, 77h, 78h, 78h, 79h, 7Ah, 7Ah, 7Bh, 7Bh, 7Ch, 7Dh, 7Dh, 7Eh, 7Fh, 7Fh, 80h
                db      80h, 80h, 81h, 81h, 82h, 83h, 83h, 84h, 85h, 85h, 86h, 86h, 87h, 88h, 88h, 89h
                db      8Ah, 8Ah, 8Bh, 8Bh, 8Ch, 8Dh, 8Dh, 8Eh, 8Fh, 8Fh, 90h, 91h, 91h, 92h, 92h, 93h
                db      94h, 94h, 95h, 96h, 96h, 97h, 97h, 98h, 99h, 99h, 9Ah, 9Bh, 9Bh, 9Ch, 9Ch, 9Dh
                db      9Eh, 9Eh, 9Fh, 0A0h, 0A0h, 0A1h, 0A2h, 0A2h, 0A3h, 0A3h, 0A4h, 0A5h, 0A5h, 0A6h, 0A7h, 0A7h
                db      0A8h, 0A8h, 0A9h, 0AAh, 0AAh, 0ABh, 0ACh, 0ACh, 0ADh, 0ADh, 0AEh, 0AFh, 0AFh, 0B0h, 0B1h, 0B1h
                db      0B2h, 0B3h, 0B3h, 0B4h, 0B4h, 0B5h, 0B6h, 0B6h, 0B7h, 0B8h, 0B8h, 0B9h, 0B9h, 0BAh, 0BBh, 0BBh
                db      0BCh, 0BDh, 0BDh, 0BEh, 0BFh, 0BFh, 0C0h, 0C0h, 0C1h, 0C2h, 0C2h, 0C3h, 0C4h, 0C4h, 0C5h, 0C5h
                db      0C6h, 0C7h, 0C7h, 0C8h, 0C9h, 0C9h, 0CAh, 0CAh, 0CBh, 0CCh, 0CCh, 0CDh, 0CEh, 0CEh, 0CFh, 0D0h
                db      40h, 41h, 41h, 42h, 42h, 43h, 43h, 44h, 44h, 45h, 45h, 46h, 46h, 47h, 47h, 48h
                db      48h, 49h, 49h, 4Ah, 4Ah, 4Bh, 4Bh, 4Ch, 4Ch, 4Dh, 4Dh, 4Eh, 4Eh, 4Fh, 4Fh, 50h
                db      50h, 51h, 51h, 52h, 52h, 53h, 53h, 54h, 54h, 55h, 55h, 56h, 56h, 57h, 57h, 58h
                db      58h, 59h, 59h, 5Ah, 5Ah, 5Bh, 5Bh, 5Ch, 5Ch, 5Dh, 5Dh, 5Eh, 5Eh, 5Fh, 5Fh, 60h
                db      60h, 61h, 61h, 62h, 62h, 63h, 63h, 64h, 64h, 65h, 65h, 66h, 66h, 67h, 67h, 68h
                db      68h, 69h, 69h, 6Ah, 6Ah, 6Bh, 6Bh, 6Ch, 6Ch, 6Dh, 6Dh, 6Eh, 6Eh, 6Fh, 6Fh, 70h
                db      70h, 71h, 71h, 72h, 72h, 73h, 73h, 74h, 74h, 75h, 75h, 76h, 76h, 77h, 77h, 78h
                db      78h, 79h, 79h, 7Ah, 7Ah, 7Bh, 7Bh, 7Ch, 7Ch, 7Dh, 7Dh, 7Eh, 7Eh, 7Fh, 7Fh, 80h
                db      80h, 80h, 81h, 81h, 82h, 82h, 83h, 83h, 84h, 84h, 85h, 85h, 86h, 86h, 87h, 87h
                db      88h, 88h, 89h, 89h, 8Ah, 8Ah, 8Bh, 8Bh, 8Ch, 8Ch, 8Dh, 8Dh, 8Eh, 8Eh, 8Fh, 8Fh
                db      90h, 90h, 91h, 91h, 92h, 92h, 93h, 93h, 94h, 94h, 95h, 95h, 96h, 96h, 97h, 97h
                db      98h, 98h, 99h, 99h, 9Ah, 9Ah, 9Bh, 9Bh, 9Ch, 9Ch, 9Dh, 9Dh, 9Eh, 9Eh, 9Fh, 9Fh
                db      0A0h, 0A0h, 0A1h, 0A1h, 0A2h, 0A2h, 0A3h, 0A3h, 0A4h, 0A4h, 0A5h, 0A5h, 0A6h, 0A6h, 0A7h, 0A7h
                db      0A8h, 0A8h, 0A9h, 0A9h, 0AAh, 0AAh, 0ABh, 0ABh, 0ACh, 0ACh, 0ADh, 0ADh, 0AEh, 0AEh, 0AFh, 0AFh
                db      0B0h, 0B0h, 0B1h, 0B1h, 0B2h, 0B2h, 0B3h, 0B3h, 0B4h, 0B4h, 0B5h, 0B5h, 0B6h, 0B6h, 0B7h, 0B7h
                db      0B8h, 0B8h, 0B9h, 0B9h, 0BAh, 0BAh, 0BBh, 0BBh, 0BCh, 0BCh, 0BDh, 0BDh, 0BEh, 0BEh, 0BFh, 0BFh
                db      50h, 50h, 51h, 51h, 51h, 52h, 52h, 53h, 53h, 53h, 54h, 54h, 54h, 55h, 55h, 56h
                db      56h, 56h, 57h, 57h, 57h, 58h, 58h, 59h, 59h, 59h, 5Ah, 5Ah, 5Ah, 5Bh, 5Bh, 5Ch
                db      5Ch, 5Ch, 5Dh, 5Dh, 5Eh, 5Eh, 5Eh, 5Fh, 5Fh, 5Fh, 60h, 60h, 61h, 61h, 61h, 62h
                db      62h, 62h, 63h, 63h, 64h, 64h, 64h, 65h, 65h, 66h, 66h, 66h, 67h, 67h, 67h, 68h
                db      68h, 69h, 69h, 69h, 6Ah, 6Ah, 6Ah, 6Bh, 6Bh, 6Ch, 6Ch, 6Ch, 6Dh, 6Dh, 6Dh, 6Eh
                db      6Eh, 6Fh, 6Fh, 6Fh, 70h, 70h, 71h, 71h, 71h, 72h, 72h, 72h, 73h, 73h, 74h, 74h
                db      74h, 75h, 75h, 75h, 76h, 76h, 77h, 77h, 77h, 78h, 78h, 79h, 79h, 79h, 7Ah, 7Ah
                db      7Ah, 7Bh, 7Bh, 7Ch, 7Ch, 7Ch, 7Dh, 7Dh, 7Dh, 7Eh, 7Eh, 7Fh, 7Fh, 7Fh, 80h, 80h
                db      80h, 80h, 80h, 81h, 81h, 81h, 82h, 82h, 83h, 83h, 83h, 84h, 84h, 84h, 85h, 85h
                db      86h, 86h, 86h, 87h, 87h, 87h, 88h, 88h, 89h, 89h, 89h, 8Ah, 8Ah, 8Bh, 8Bh, 8Bh
                db      8Ch, 8Ch, 8Ch, 8Dh, 8Dh, 8Eh, 8Eh, 8Eh, 8Fh, 8Fh, 8Fh, 90h, 90h, 91h, 91h, 91h
                db      92h, 92h, 93h, 93h, 93h, 94h, 94h, 94h, 95h, 95h, 96h, 96h, 96h, 97h, 97h, 97h
                db      98h, 98h, 99h, 99h, 99h, 9Ah, 9Ah, 9Ah, 9Bh, 9Bh, 9Ch, 9Ch, 9Ch, 9Dh, 9Dh, 9Eh
                db      9Eh, 9Eh, 9Fh, 9Fh, 9Fh, 0A0h, 0A0h, 0A1h, 0A1h, 0A1h, 0A2h, 0A2h, 0A2h, 0A3h, 0A3h, 0A4h
                db      0A4h, 0A4h, 0A5h, 0A5h, 0A6h, 0A6h, 0A6h, 0A7h, 0A7h, 0A7h, 0A8h, 0A8h, 0A9h, 0A9h, 0A9h, 0AAh
                db      0AAh, 0AAh, 0ABh, 0ABh, 0ACh, 0ACh, 0ACh, 0ADh, 0ADh, 0ADh, 0AEh, 0AEh, 0AFh, 0AFh, 0AFh, 0B0h
                db      60h, 61h, 61h, 61h, 61h, 62h, 62h, 62h, 62h, 63h, 63h, 63h, 63h, 64h, 64h, 64h
                db      64h, 65h, 65h, 65h, 65h, 66h, 66h, 66h, 66h, 67h, 67h, 67h, 67h, 68h, 68h, 68h
                db      68h, 69h, 69h, 69h, 69h, 6Ah, 6Ah, 6Ah, 6Ah, 6Bh, 6Bh, 6Bh, 6Bh, 6Ch, 6Ch, 6Ch
                db      6Ch, 6Dh, 6Dh, 6Dh, 6Dh, 6Eh, 6Eh, 6Eh, 6Eh, 6Fh, 6Fh, 6Fh, 6Fh, 70h, 70h, 70h
                db      70h, 71h, 71h, 71h, 71h, 72h, 72h, 72h, 72h, 73h, 73h, 73h, 73h, 74h, 74h, 74h
                db      74h, 75h, 75h, 75h, 75h, 76h, 76h, 76h, 76h, 77h, 77h, 77h, 77h, 78h, 78h, 78h
                db      78h, 79h, 79h, 79h, 79h, 7Ah, 7Ah, 7Ah, 7Ah, 7Bh, 7Bh, 7Bh, 7Bh, 7Ch, 7Ch, 7Ch
                db      7Ch, 7Dh, 7Dh, 7Dh, 7Dh, 7Eh, 7Eh, 7Eh, 7Eh, 7Fh, 7Fh, 7Fh, 7Fh, 80h, 80h, 80h
                db      80h, 80h, 80h, 80h, 81h, 81h, 81h, 81h, 82h, 82h, 82h, 82h, 83h, 83h, 83h, 83h
                db      84h, 84h, 84h, 84h, 85h, 85h, 85h, 85h, 86h, 86h, 86h, 86h, 87h, 87h, 87h, 87h
                db      88h, 88h, 88h, 88h, 89h, 89h, 89h, 89h, 8Ah, 8Ah, 8Ah, 8Ah, 8Bh, 8Bh, 8Bh, 8Bh
                db      8Ch, 8Ch, 8Ch, 8Ch, 8Dh, 8Dh, 8Dh, 8Dh, 8Eh, 8Eh, 8Eh, 8Eh, 8Fh, 8Fh, 8Fh, 8Fh
                db      90h, 90h, 90h, 90h, 91h, 91h, 91h, 91h, 92h, 92h, 92h, 92h, 93h, 93h, 93h, 93h
                db      94h, 94h, 94h, 94h, 95h, 95h, 95h, 95h, 96h, 96h, 96h, 96h, 97h, 97h, 97h, 97h
                db      98h, 98h, 98h, 98h, 99h, 99h, 99h, 99h, 9Ah, 9Ah, 9Ah, 9Ah, 9Bh, 9Bh, 9Bh, 9Bh
                db      9Ch, 9Ch, 9Ch, 9Ch, 9Dh, 9Dh, 9Dh, 9Dh, 9Eh, 9Eh, 9Eh, 9Eh, 9Fh, 9Fh, 9Fh, 9Fh
                db      70h, 70h, 70h, 70h, 70h, 71h, 71h, 71h, 71h, 71h, 71h, 71h, 71h, 72h, 72h, 72h
                db      72h, 72h, 72h, 72h, 72h, 73h, 73h, 73h, 73h, 73h, 73h, 73h, 73h, 74h, 74h, 74h
                db      74h, 74h, 74h, 74h, 75h, 75h, 75h, 75h, 75h, 75h, 75h, 75h, 76h, 76h, 76h, 76h
                db      76h, 76h, 76h, 76h, 77h, 77h, 77h, 77h, 77h, 77h, 77h, 78h, 78h, 78h, 78h, 78h
                db      78h, 78h, 78h, 79h, 79h, 79h, 79h, 79h, 79h, 79h, 79h, 7Ah, 7Ah, 7Ah, 7Ah, 7Ah
                db      7Ah, 7Ah, 7Bh, 7Bh, 7Bh, 7Bh, 7Bh, 7Bh, 7Bh, 7Bh, 7Ch, 7Ch, 7Ch, 7Ch, 7Ch, 7Ch
                db      7Ch, 7Ch, 7Dh, 7Dh, 7Dh, 7Dh, 7Dh, 7Dh, 7Dh, 7Eh, 7Eh, 7Eh, 7Eh, 7Eh, 7Eh, 7Eh
                db      7Eh, 7Fh, 7Fh, 7Fh, 7Fh, 7Fh, 7Fh, 7Fh, 7Fh, 80h, 80h, 80h, 80h, 80h, 80h, 80h
                db      80h, 80h, 80h, 80h, 80h, 80h, 80h, 80h, 81h, 81h, 81h, 81h, 81h, 81h, 81h, 81h
                db      82h, 82h, 82h, 82h, 82h, 82h, 82h, 82h, 83h, 83h, 83h, 83h, 83h, 83h, 83h, 84h
                db      84h, 84h, 84h, 84h, 84h, 84h, 84h, 85h, 85h, 85h, 85h, 85h, 85h, 85h, 85h, 86h
                db      86h, 86h, 86h, 86h, 86h, 86h, 87h, 87h, 87h, 87h, 87h, 87h, 87h, 87h, 88h, 88h
                db      88h, 88h, 88h, 88h, 88h, 88h, 89h, 89h, 89h, 89h, 89h, 89h, 89h, 8Ah, 8Ah, 8Ah
                db      8Ah, 8Ah, 8Ah, 8Ah, 8Ah, 8Bh, 8Bh, 8Bh, 8Bh, 8Bh, 8Bh, 8Bh, 8Bh, 8Ch, 8Ch, 8Ch
                db      8Ch, 8Ch, 8Ch, 8Ch, 8Dh, 8Dh, 8Dh, 8Dh, 8Dh, 8Dh, 8Dh, 8Dh, 8Eh, 8Eh, 8Eh, 8Eh
                db      8Eh, 8Eh, 8Eh, 8Eh, 8Fh, 8Fh, 8Fh, 8Fh, 8Fh, 8Fh, 8Fh, 8Fh, 90h, 90h, 90h, 90h
g_74A3          dw      1               ; ticks to the next chain to the old INT 8
g_74A5          dw      1               ; reload of g_74A3
g_74A7          dw      1               ; reload of g_74A3 (fast timer)
g_74A9          dw      64h             ; PIT divisor (sample rate)
g_74AB          dw      64h             ; PIT divisor for the fast timer
; output routines by device
_fd_55B3_74AD   dw      offset out_speaker
_fd_55B3_74AF   dw      offset out_adlib
_fd_55B3_74B1   dw      offset out_lpt
_fd_55B3_74B3   dw      offset out_200
_fd_55B3_74B5   dw      offset out_sb
_fd_55B3_74B7   dw      offset out_222
_fd_55B3_74B9   dw      offset out_6B4A
                db      0
g_74BC          dw      0               ; handler to install (offset, segment)
g_74BE          dw      0
_DATA           ends

TIMER_TEXT      segment word public 'CODE'
                assume  cs:TIMER_TEXT, ds:DGROUP

                public  _f_28BC_0000
                public  _f_28BC_000E
                public  _f_28BC_0015
                public  _f_28BC_020E
                public  _f_28BC_0354
                public  _f_28BC_03CC
                public  _f_28BC_040C
                public  _f_28BC_0422
                public  _f_28BC_046B
                public  _f_28BC_0488
                public  _f_28BC_04E0

; data in the code segment (reachable from the handlers without DS)
_f_28BC_0000    label   byte
old_int8        dd      0               ; previous INT 8 handler
save_sp         dw      0
save_ss         dw      0
isr_sp          dw      offset DGROUP:isr_stack_top
isr_ss          dw      DGROUP
busy            db      0               ; handler nesting count
                even

_f_28BC_000E    label   near
                pop     ax
                dec     byte ptr cs:busy
                iret
_f_28BC_0015:
                push    ax
                mov     al, 20h
                out     20h, al
                inc     byte ptr cs:busy
                cmp     byte ptr cs:busy, 1
                jne     _f_28BC_000E
                sti
                push    bx
                push    dx
                push    si
                push    ds
                push    es
                mov     ax, DGROUP
                mov     ds, ax
                cld
                mov     si, offset DGROUP:g_6B4C
                mov     ax, word ptr [si+2]
                or      ax, word ptr [si+4]
                mov     dl, 80h
                je      L0076
                les     bx, dword ptr [si+2]
                mov     ax, word ptr es:[bx]
                or      ax, word ptr es:[bx+2]
                je      L0076
                les     bx, dword ptr es:[bx]
                les     ax, dword ptr es:[bx]
                std
                xor     ax, ax
                mov     al, byte ptr [si+0Eh]
                add     ax, word ptr [si+0Ah]
                mov     byte ptr [si+0Eh], al
                xchg    ah, al
                xor     ah, ah
                add     word ptr [si], ax
                mov     ax, word ptr [si]
                cmp     ax, word ptr [si+6]
                ja      L00C5
                mov     bx, word ptr [si+0Ch]
                mov     si, ax
                mov     al, byte ptr es:[si]
                xlat
                mov     dl, al
L0076:
                mov     si, offset DGROUP:g_6B60
                mov     ax, word ptr [si+2]
                or      ax, word ptr [si+4]
                mov     al, 80h
                je      L00B9
                les     bx, dword ptr [si+2]
                mov     ax, word ptr es:[bx]
                or      ax, word ptr es:[bx+2]
                mov     al, 80h
                je      L00B9
                les     bx, dword ptr es:[bx]
                les     ax, dword ptr es:[bx]
                std
                xor     ax, ax
                mov     al, byte ptr [si+0Eh]
                add     ax, word ptr [si+0Ah]
                mov     byte ptr [si+0Eh], al
                xchg    ah, al
                xor     ah, ah
                add     word ptr [si], ax
                mov     ax, word ptr [si]
                cmp     ax, word ptr [si+6]
                ja      L00C5
                mov     bx, word ptr [si+0Ch]
                mov     si, ax
                mov     al, byte ptr es:[si]
                xlat
L00B9:
                xor     ah, ah
                xor     dh, dh
                add     ax, dx
                shr     ax, 1
                jmp     word ptr _fd_55B3_6B9C
L00C5:
                test    byte ptr [si+0Fh], 80h
                je      L00D2
                mov     ax, word ptr [si+8]
                mov     word ptr [si], ax
                jmp     short out_done
L00D2:
                mov     word ptr [si+2], 0
                mov     word ptr [si+4], 0
                jmp     short out_done
L00DE:
                mov     ax, word ptr g_6B40
                mov     word ptr g_6B3E, ax
                dec     word ptr _fd_55B3_6B42
                jne     L0136
                mov     word ptr cs:save_ss, ss
                mov     word ptr cs:save_sp, sp
                mov     ss, word ptr cs:isr_ss
                mov     sp, word ptr cs:isr_sp
                push    cx
                push    di
                cld
                mov     ax, DGROUP
                mov     ds, ax
                call    _f_284A_067F
                mov     bx, ax
                mov     ax, DGROUP
                mov     ds, ax
                mov     word ptr _fd_55B3_6B42, bx
                pop     di
                pop     cx
                mov     ss, word ptr cs:save_ss
                mov     sp, word ptr cs:save_sp
                jmp     short L0136
out_done:
                mov     ax, DGROUP
                mov     ds, ax
                dec     word ptr g_6B3E
                je      L00DE
                pushf
                pop     ax
                and     ah, 4
                je      L0148
L0136:
                dec     word ptr g_74A3
                jle     L014C
                pop     es
                pop     ds
                pop     si
                pop     dx
                pop     bx
                pop     ax
                dec     byte ptr cs:busy
                iret
L0148:
                cli
                jmp     L0428
L014C:
                mov     ax, word ptr g_74A5
                mov     word ptr g_74A3, ax
                pop     es
                pop     ds
                pop     si
                pop     dx
                pop     bx
                pop     ax
                cli
                dec     byte ptr cs:busy
                jmp     dword ptr cs:old_int8
                even
out_lpt:
                mov     dx, _g_693C
                out     dx, al
                jmp     short $+2
                add     dx, 2
                in      al, dx
                or      al, 8
                out     dx, al
                jmp     short $+2
                in      al, dx
                and     al, 0F7h
                out     dx, al
                jmp     out_done
                even
out_222:
                mov     dx, 222h
                out     dx, al
                jmp     out_done
                even
out_6B4A:
                mov     dx, word ptr _fd_55B3_6B4A
                inc     dx
                out     dx, al
                jmp     out_done
                even
out_200:
                mov     dx, 200h
                out     dx, al
                jmp     out_done
                even
out_sb:
                mov     dx, word ptr _fd_55B3_6BA0
                mov     ah, al
L0194:
                in      al, dx
                test    al, 80h
                jne     L0194
                mov     al, 10h
                out     dx, al
L019C:
                in      al, dx
                test    al, 80h
                jne     L019C
                mov     al, ah
                out     dx, al
                jmp     out_done
                even
out_adlib:
                mov     dx, 388h
                mov     ah, al
                mov     al, 40h
                out     dx, al
                in      al, dx
                in      al, dx
                in      al, dx
                in      al, dx
                mov     al, ah
                xor     ah, ah
                mov     bx, offset DGROUP:g_6BA4
                xlat
                inc     dx
                out     dx, al
                jmp     out_done
                even
out_speaker:
                cmp     al, 80h
                jbe     L01F8
                ja      L01E0
                cmp     word ptr g_6B48, 1
                je      L01DD
                mov     word ptr g_6B48, 1
                in      al, 61h
                and     al, 0FCh
                or      al, 3
                out     61h, al
L01DD:
                jmp     out_done
L01E0:
                cmp     word ptr g_6B48, 0
                je      L01DD
                mov     word ptr g_6B48, 0
                in      al, 61h
                and     al, 0FCh
                or      al, 2
                out     61h, al
                jmp     out_done
L01F8:
                cmp     word ptr g_6B48, 2
                je      L01DD
                mov     word ptr g_6B48, 2
                in      al, 61h
                and     al, 0FCh
                out     61h, al
                jmp     out_done
_f_28BC_020E:
                push    ax
                push    bx
                push    dx
                push    si
                push    ds
                push    es
                mov     al, 20h
                out     20h, al
                sti
                mov     ax, DGROUP
                mov     ds, ax
                cld
                mov     si, offset DGROUP:g_6B4C
                mov     ax, word ptr [si+2]
                or      ax, word ptr [si+4]
                mov     word ptr g_6B44, 80h
                je      L026C
                les     bx, dword ptr [si+2]
                mov     ax, word ptr es:[bx]
                or      ax, word ptr es:[bx+2]
                je      L026C
                les     bx, dword ptr es:[bx]
                les     ax, dword ptr es:[bx]
                std
                xor     ax, ax
                mov     al, byte ptr [si+0Eh]
                add     ax, word ptr [si+0Ah]
                mov     byte ptr [si+0Eh], al
                xchg    ah, al
                xor     ah, ah
                add     word ptr [si], ax
                mov     ax, word ptr [si]
                cmp     ax, word ptr [si+6]
                jbe     L025E
                jmp     L00C5
L025E:
                mov     bx, word ptr [si+0Ch]
                mov     si, ax
                mov     al, byte ptr es:[si]
                xlat
                xor     ah, ah
                mov     word ptr g_6B44, ax
L026C:
                mov     si, offset DGROUP:g_6B60
                mov     ax, word ptr [si+2]
                or      ax, word ptr [si+4]
                mov     dh, 80h
                je      L02B2
                les     bx, dword ptr [si+2]
                mov     ax, word ptr es:[bx]
                or      ax, word ptr es:[bx+2]
                je      L02B2
                les     bx, dword ptr es:[bx]
                les     ax, dword ptr es:[bx]
                std
                xor     ax, ax
                mov     al, byte ptr [si+0Eh]
                add     ax, word ptr [si+0Ah]
                mov     byte ptr [si+0Eh], al
                xchg    ah, al
                xor     ah, ah
                add     word ptr [si], ax
                mov     ax, word ptr [si]
                cmp     ax, word ptr [si+6]
                jbe     L02A7
                jmp     L00C5
L02A7:
                mov     bx, word ptr [si+0Ch]
                mov     si, ax
                mov     al, byte ptr es:[si]
                xlat
                mov     dh, al
L02B2:
                mov     si, offset DGROUP:g_6B74
                mov     ax, word ptr [si+2]
                or      ax, word ptr [si+4]
                mov     dl, 80h
                je      L02F8
                les     bx, dword ptr [si+2]
                mov     ax, word ptr es:[bx]
                or      ax, word ptr es:[bx+2]
                je      L02F8
                les     bx, dword ptr es:[bx]
                les     ax, dword ptr es:[bx]
                std
                xor     ax, ax
                mov     al, byte ptr [si+0Eh]
                add     ax, word ptr [si+0Ah]
                mov     byte ptr [si+0Eh], al
                xchg    ah, al
                xor     ah, ah
                add     word ptr [si], ax
                mov     ax, word ptr [si]
                cmp     ax, word ptr [si+6]
                jbe     L02ED
                jmp     L00C5
L02ED:
                mov     bx, word ptr [si+0Ch]
                mov     si, ax
                mov     al, byte ptr es:[si]
                xlat
                mov     dl, al
L02F8:
                mov     si, offset DGROUP:g_6B88
                mov     ax, word ptr [si+2]
                or      ax, word ptr [si+4]
                mov     al, 80h
                je      L033C
                les     bx, dword ptr [si+2]
                mov     ax, word ptr es:[bx]
                or      ax, word ptr es:[bx+2]
                je      L033C
                les     bx, dword ptr es:[bx]
                les     ax, dword ptr es:[bx]
                std
                xor     ax, ax
                mov     al, byte ptr [si+0Eh]
                add     ax, word ptr [si+0Ah]
                mov     byte ptr [si+0Eh], al
                xchg    ah, al
                xor     ah, ah
                add     word ptr [si], ax
                mov     ax, word ptr [si]
                cmp     ax, word ptr [si+6]
                jbe     L0333
                jmp     L00C5
L0333:
                mov     bx, word ptr [si+0Ch]
                mov     si, ax
                mov     al, byte ptr es:[si]
                xlat
L033C:
                xor     ah, ah
                xor     bx, bx
                mov     bl, dh
                xor     dh, dh
                add     ax, dx
                add     ax, bx
                add     ax, word ptr g_6B44
                shr     ax, 1
                shr     ax, 1
                jmp     word ptr _fd_55B3_6B9C
_f_28BC_0354:
                inc     byte ptr cs:busy
                push    ax
                push    ds
                mov     al, 20h
                out     20h, al
                mov     ax, DGROUP
                mov     ds, ax
                dec     word ptr _fd_55B3_6B42
                je      L038A
L036A:
                dec     word ptr g_74A3
                jle     L0378
                pop     ds
                pop     ax
                dec     byte ptr cs:busy
                iret
L0378:
                mov     ax, word ptr g_74A7
                mov     word ptr g_74A3, ax
                pop     ds
                pop     ax
                dec     byte ptr cs:busy
                jmp     dword ptr cs:old_int8
L038A:
                mov     word ptr cs:save_ss, ss
                mov     word ptr cs:save_sp, sp
                mov     ss, word ptr cs:isr_ss
                mov     sp, word ptr cs:isr_sp
                push    bx
                push    cx
                push    dx
                push    es
                push    si
                push    di
                mov     ax, DGROUP
                mov     ds, ax
                cld
                call    _f_284A_067F
                mov     bx, ax
                mov     ax, DGROUP
                mov     ds, ax
                mov     word ptr _fd_55B3_6B42, bx
                pop     di
                pop     si
                pop     es
                pop     dx
                pop     cx
                pop     bx
                mov     ss, word ptr cs:save_ss
                mov     sp, word ptr cs:save_sp
                jmp     L036A
_f_28BC_03CC    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                cli
                mov     ax, DGROUP
                mov     ds, ax
                mov     al, 36h
                out     43h, al
                mov     ax, word ptr g_74A9
                out     40h, al
                xchg    ah, al
                out     40h, al
                push    es
                xor     ax, ax
                mov     es, ax
                mov     ax, word ptr g_74BE
                mov     word ptr es:[22h], ax
                mov     dx, word ptr g_74BC
                mov     word ptr es:[20h], dx
                mov     word ptr g_74A3, 1
                pop     es
                sti
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_28BC_03CC    endp

_f_28BC_040C    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                cli
                pushf
                call    _f_28BC_0422
                sti
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_28BC_040C    endp

_f_28BC_0422:
                push    ax
                push    bx
                push    dx
                push    si
                push    ds
                push    es
L0428:
                mov     ax, DGROUP
                mov     ds, ax
                mov     al, 36h
                out     43h, al
                mov     ax, word ptr g_74AB
                out     40h, al
                xchg    ah, al
                out     40h, al
                push    es
                push    cx
                xor     ax, ax
                mov     es, ax
                mov     ax, TIMER_TEXT
                mov     word ptr es:[22h], ax
                mov     dx, offset _f_28BC_0354
                mov     word ptr es:[20h], dx
                mov     dx, cx
                mov     cl, 4
                shr     word ptr g_74A3, cl
                inc     word ptr g_74A3
                mov     cx, dx
                pop     cx
                pop     es
                pop     es
                pop     ds
                pop     si
                pop     dx
                pop     bx
                pop     ax
                dec     byte ptr cs:busy
                iret
_f_28BC_046B    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                mov     ax, DGROUP
                mov     ds, ax
                mov     word ptr g_74BE, TIMER_TEXT
                mov     word ptr g_74BC, offset _f_28BC_020E
                jmp     short L04A3
_f_28BC_046B    endp

_f_28BC_0488    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                mov     ax, DGROUP
                mov     ds, ax
                mov     word ptr g_74BE, TIMER_TEXT
                mov     word ptr g_74BC, offset _f_28BC_0015
L04A3:
                mov     ax, 3508h
                int     21h
                cmp     bx, offset _f_28BC_0015
                je      L04BE
                cmp     bx, offset _f_28BC_020E
                je      L04BE
                mov     word ptr cs:old_int8, bx
                mov     word ptr cs:old_int8+2, es
L04BE:
                mov     cx, 4
                mov     ax, word ptr [bp+2]
                mov     word ptr g_74A3, ax
                mov     word ptr g_74A5, ax
                shr     ax, cl
                mov     word ptr g_74A7, ax
                mov     ax, word ptr [bp]
                mov     word ptr g_74A9, ax
                shl     ax, cl
                mov     word ptr g_74AB, ax
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_28BC_0488    endp

_f_28BC_04E0    proc    far
                push    bp
                mov     bp, sp
                add     bp, 6
                push    es
                push    ds
                push    si
                push    di
                cli
                mov     al, 36h
                out     43h, al
                mov     ax, word ptr [bp]
                out     40h, al
                xchg    ah, al
                out     40h, al
                mov     ax, word ptr cs:old_int8+2
                mov     dx, word ptr cs:old_int8
                mov     ds, ax
                mov     ax, 2508h
                int     21h
                cli
                mov     al, 36h
                out     43h, al
                mov     ax, word ptr [bp]
                out     40h, al
                xchg    ah, al
                out     40h, al
                sti
                pop     di
                pop     si
                pop     ds
                pop     es
                pop     bp
                ret
_f_28BC_04E0    endp

TIMER_TEXT      ends
                end
