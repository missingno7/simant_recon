#include "main_loop_counter.h"

/* Source root:m15F8 owns the only writer; C static-duration initialization
 * supplies the original zeroed DGROUP state before main starts. */
int32_t fd_50F6_383A = 0;
