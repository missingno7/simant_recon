/*
 * Bundles tile drawing state, display callbacks, colony control resources, map cursor geometry
 * and dialog handles. Its address named fields cover more than the generic window library.
 * The opaque or residual file name is retained; folder placement is ours (inferred).
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 */

struct Rect { int left; int top; int right; int bottom; };
typedef char far * far *Handle;
int far fd_50F6_37D2;
int far fd_50F6_37D4;
struct Rect far fd_50F6_37D6;
Handle far fd_50F6_37DE;
void (far * far fd_50F6_37E6)();
void (far * far fd_50F6_37EA)();
void (far * far fd_50F6_37EE)();
Handle far casteAnimHandle;
Handle far modeAnimHandle;
int far fd_50F6_37FA;
int far fd_50F6_37FC;
Handle far fd_50F6_3836;
long far fd_50F6_383A;
struct Rect far fd_50F6_3842;
struct Rect far fd_50F6_384A;
int far fd_50F6_3852;
int far multiplier;
int far mapXsize;
int far mapYsize;
char far * far fd_50F6_38B2;
int far fd_50F6_38B6;
void (far * far fd_50F6_38B8)();
void (far * far fd_50F6_38BC)();
int far fd_50F6_38C0;
struct Rect far mapCursorRect;
Handle far fd_50F6_3934;
Handle far fd_50F6_3938;
struct Rect far fd_50F6_393C;
long far fd_50F6_3944;
