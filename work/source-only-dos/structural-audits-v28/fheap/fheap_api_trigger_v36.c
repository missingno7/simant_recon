#include <malloc.h>

void far main(void)
{
    void far *near_block;
    void far *far_block;

    near_block = malloc(32);
    far_block = _fmalloc(32);
    free(near_block);
    _ffree(far_block);
}
