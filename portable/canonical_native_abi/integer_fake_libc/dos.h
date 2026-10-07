#ifndef SIMANT_PARSE_DOS
#define SIMANT_PARSE_DOS
union REGS { struct { unsigned short ax,bx,cx,dx,si,di,cflag,flags; } x; struct { unsigned char al,ah,bl,bh,cl,ch,dl,dh; } h; };
struct SREGS { unsigned short es,cs,ss,ds; };
#define _A_NORMAL 0
#define _A_RDONLY 1
#define _A_HIDDEN 2
#define _A_SYSTEM 4
#define _A_SUBDIR 16
#define _A_ARCH 32
#include <stdint.h>
#define FP_SEG(p) ((uint16_t)(((uintptr_t)(p)) >> 16))
#define FP_OFF(p) ((uint16_t)(uintptr_t)(p))
int _dos_allocmem(unsigned short, unsigned short *);
int _dos_freemem(unsigned short);
int _dos_setblock(unsigned short, unsigned short, unsigned short *);
int int86(int, union REGS *, union REGS *);
int int86x(int, union REGS *, union REGS *, struct SREGS *);
#endif
