#ifndef SIMANT_WHOLE_PROGRAM_WINDOW_LIST_REFS_H
#define SIMANT_WHOLE_PROGRAM_WINDOW_LIST_REFS_H

/* Source root:m23E6 stores List.text at (object + 0x2a) + 0x0a =
 * object + 0x34.  The four-byte DOS Handle wire cell is represented by the
 * live window registry's native char** sidecar instead of an eight-byte
 * pointer written into the serialized object. */
char ***sim_window_list_text_slot(const void *list_view);

#endif
