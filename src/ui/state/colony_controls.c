/*
 * Functional source-only owner candidate for the control state used by root:0798.
 * This is a scratch source for ownership and OMF/runtime probes; it does not
 * claim a historical object boundary, address, segment order, or initial bytes.
 */
struct TriLevel {
    unsigned frac;
    unsigned mid;
    unsigned weight;
};

struct Pt {
    int x;
    int y;
};

struct TriPoints {
    int apexX;
    int apexY;
    int leftX;
    int leftY;
    int rightX;
    int rightY;
};

/* root:0798 initControls writes all three words of both triples. */
struct TriLevel far casteLevels;
struct TriLevel far modeLevels;

/* root:0798 initControls loads the bitmap dimensions; InitTriVars writes the
 * four dimensions and the associated mode/caste triangle geometry. */
struct Pt far knobSize;
unsigned far triHeight;
unsigned far triWidth;
unsigned far triWidthL;
unsigned far triWidthR;
struct TriPoints far fd_50F6_3816;
struct TriPoints far fd_50F6_3822;
long far fd_50F6_382E;
struct Pt far fd_50F6_0358;
struct Pt far fd_50F6_022E;
