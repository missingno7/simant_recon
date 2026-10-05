#include <stdlib.h>
/* These fatal services belong to unselected OpenIndex error paths. */
void DosPunt(char *message) { (void)message; abort(); }
void Punt(char *format, ...) { (void)format; abort(); }
