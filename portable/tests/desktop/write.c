/* Inject actual short/failed host writes below the DOS service. No game state
 * or errno policy is stubbed; compile the production adapter in this TU. */
#include <io.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
static int mode, calls;
static int test_write(int fd, const void *data, unsigned count)
{
    (void)fd;(void)data;++calls;
    if (!count) return 0;
    if (mode==1 && calls==1) return (int)(count/2);
    if (mode==1) return (int)count;
    if (mode==2 && calls==1) return 2;
    if (mode==2) { errno=ENOSPC;return -1; }
    return 0;
}
#define _write test_write
#include "portable/whole_program/platform/dos_io.c"
#undef _write
#define CHECK(x) do { if(!(x)) {fprintf(stderr,"failed line %d: %s\n",__LINE__,#x);exit(71);} } while(0)
int main(void)
{
    char data[10]={0};handle_initialized[3]=1;host_handles[3]=1;
    mode=1;calls=0;CHECK(dos_write(3,data,10)==10 && calls==2 && dos_errno==0);
    mode=2;calls=0;CHECK(dos_write(3,data,10)==-1 && calls==2 && dos_errno==28);
    mode=3;calls=0;CHECK(dos_write(3,data,10)==-1 && dos_errno==28);
    CHECK(dos_write(3,data,0)==0 && dos_errno==0);
    CHECK(dos_write(3,NULL,0)==0 && dos_errno==0);
    puts("PASS short write completion; disk-full and zero-progress failures");return 0;
}
