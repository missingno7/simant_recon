# RandWorld acceptance and controls (2026-09-30)

The whole-module accepted.c owns the 1,355-byte RandWorld body at S08:35F5:0050.
The profile is msc600ax /AL /Os /Og /Oe /Zi. CONST is 55B3:8548 (208 bytes),
_DATA is 55B3:26D0 (120 bytes). Both data contributions and the 17 prior claims
remain exact. The reviewed cross-version naming decision is in decisions.json.

The initializer count = (seed < 0) is explicitly STEERED. Since seed is unsigned,
its value is always zero, but the eliminated original expression is unknown.
ZERO-1 records a controlled positive and negative compiler experiment using this
module's declaration and live-variable context; it is not a universal rule.
The unused y declaration is retained from the earlier draft; all boundary-column
indexes are literal zero and there is no dead y assignment. No original bytes,
object patches, assembly workaround, or dummy identifiers were accepted.

literal_zero.c differs at the first loop entry and is four bytes longer.
live_y.c is the old, 16-byte-longer draft whose dead initializer survives and
whose second-loop CSE and cross-jump differ. Neither control is accepted.

Within-group relocation order remains pending. Both attempted complete extents
35F50:3730D were refused by the stricter order gate under Zi and Zd; these are
negative controls, not accepted TU claims. The partial claim passed verification
and was promoted through promote.py. S08 is therefore still a partial TU.
