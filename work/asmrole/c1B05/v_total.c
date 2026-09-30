/* Experiment (worker asmrole): can MSC 6.00AX produce f_1B05_0046 as a C function whose body is
   inline _asm?  (the only C route left for a proc with lodsb/ss:/DS switching, rule ASM-1) */
extern char far fd_4F6F_0000[];

static char far *RingBuf = fd_4F6F_0000;
static int Threshold = 2;
static char far *SrcPtr = 0;
static int SrcCount = 0;
static int RingPos = 0;
static int Flags = 0;
static int SaveDX = 0;
static int SaveCX = 0;
static int MatchLen = 0;
static int State = 1;

int far f_1B05_0046(char far *dst, int n)
{
    unsigned ringseg;
    int total;
    _asm {
	mov	total, 0
	mov	bx, RingPos
	mov	dx, SaveDX
	mov	cx, SaveCX
	push	ds
	mov	ax, word ptr RingBuf+2
	mov	ringseg, ax
	mov	ax, Flags
	les	di, dst
	lds	si, SrcPtr
	cmp	ss:State, 0
	je	L00A6
	dec	ss:State
	je	L00AD
	dec	ss:State
	je	L00BB
	dec	ss:State
	je	L00E4
	dec	ss:State
	je	L00EE
	mov	ds, ringseg
	jmp	L0136
L009A:	mov	di, 1
	jmp	L0157
L00A0:	mov	di, 2
	jmp	L0157
L00A6:	shr	ax, 1
	test	ah, 1
	jne	L00B7
L00AD:	dec	ss:SrcCount
	js	L009A
	lodsb
	mov	ah, 0FFh
L00B7:	test	al, 1
	je	L00E4
L00BB:	dec	ss:SrcCount
	js	L00A0
	mov	dl, [si]
	inc	si
	mov	es:[di], dl
	inc	di
	mov	ds, ringseg
	mov	byte ptr fd_4F6F_0000[bx], dl
	mov	ds, word ptr ss:SrcPtr+2
	inc	bx
	and	bx, 0FFFh
	inc	total
	dec	n
	je	L0154
	jmp	L00A6
L00E4:	dec	ss:SrcCount
	js	L014A
	mov	cl, [si]
	inc	si
L00EE:	dec	ss:SrcCount
	js	L0145
	mov	dl, [si]
	inc	si
	mov	ch, dl
	shr	ch, 1
	shr	ch, 1
	shr	ch, 1
	shr	ch, 1
	and	dl, 0Fh
	add	dl, byte ptr ss:Threshold
	xor	dh, dh
	mov	ss:MatchLen, dx
	mov	ds, ringseg
L0114:	xchg	bx, cx
	mov	dl, byte ptr fd_4F6F_0000[bx]
	inc	bx
	and	bx, 0FFFh
	mov	es:[di], dl
	inc	di
	xchg	bx, cx
	mov	byte ptr fd_4F6F_0000[bx], dl
	inc	bx
	and	bx, 0FFFh
	inc	total
	dec	n
	je	L014F
L0136:	dec	ss:MatchLen
	jns	L0114
	mov	ds, word ptr ss:SrcPtr+2
	jmp	L00A6
L0145:	mov	di, 4
	jmp	L0157
L014A:	mov	di, 3
	jmp	L0157
L014F:	mov	di, 5
	jmp	L0157
L0154:	mov	di, 0
L0157:	pop	ds
	mov	State, di
	mov	Flags, ax
	mov	RingPos, bx
	mov	word ptr SrcPtr, si
	mov	SaveDX, dx
	mov	SaveCX, cx
    }
    return total;
}
