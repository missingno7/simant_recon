#ifndef SIMANT_NATIVE_MENU_GLOBALS_H
#define SIMANT_NATIVE_MENU_GLOBALS_H
#include "portable/ui_model/menus/source_record_view.h"

/* One native view of the source kind-6 resource. Payload ownership remains
 * with the original database handle; only native pointer vectors live here. */
extern PortableMenuSourceRecordView g_menu_view;
extern char ***fd_55B3_6054;
void sim_menu_globals_release(void);
#endif
