#include <stdint.h>
#include <stdlib.h>

/* FindIndex has no call edges to these historical OpenIndex/CloseIndex leaves.
 * Fail immediately if the linker ever retains/reaches one during this test. */
void DosPunt(char *message) { (void)message; abort(); }
void Punt(char *format, ...) { (void)format; abort(); }
void **f_171C_13CA(int32_t size, int16_t flags, char *name)
{ (void)size; (void)flags; (void)name; abort(); return NULL; }
void dos_free(void *p) { (void)p; abort(); }
