/* Appended to the converted History TU. Private presentation selection, copied
 * without calling ToggleHistButton or regenerating a graph. */
#include "portable/whole_program/enhanced/snapshot.h"
void enhanced_read_history_selection(EnhancedHistorySnapshot *out)
{
    for(unsigned i=0;i<4;++i)out->shown[i]=shownGraphs[i];
    for(unsigned i=0;i<10;++i)out->colors[i]=histColor[i];
    out->selection_available=1;
}
