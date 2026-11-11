/* Functional scheduler storage for the immutable shipped SOUND corpus.
 * All initialized/current/best indices belong to 0..N-1, 2 <= N <= 10.
 * Capacity 10 is an operational allocation choice, not a historical COMDEF
 * capacity, original allocating translation unit or placement claim.
 * Resource/consumer proof: evidence/canonical/shipped-resource-domain/review.md.
 */
unsigned char far fd_50F6_4B30[10];
long far fd_50F6_4B42[10];
