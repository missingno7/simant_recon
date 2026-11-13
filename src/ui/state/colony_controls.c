/*
 * Defines mode and caste control levels and triangle geometry. The control window initializer
 * and drawing handlers use the dimensions, points and knob size.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS references: resident data extension (section 27), registered frames 50F6. Source-owned
 * storage; original placement, owning file and completeness are unproven.
 * Windows: unknown; this storage file has no functions to pair.
 * Build profile: msc600ax; /AL /Os /Gs.
 *
 * The functional ownership and OMF/runtime probes do not establish an
 * original object boundary, address, segment order or initial bytes.
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
struct TriPoints far modeVerts;
struct TriPoints far casteVerts;
long far leftYSlope;
/*
 * Mode triangle point before subtracting half the knob dimensions.
 */
struct Pt far mode_knob_center;
/*
 * Caste triangle point before subtracting half the knob dimensions.
 */
struct Pt far caste_knob_center;
