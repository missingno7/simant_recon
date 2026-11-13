/*
 * Defines the DOS release version string. It is the data contribution immediately after the
 * runtime BEGDATA region.
 * File name and folder are ours, inferred from the DOS routines or storage defined here.
 * DOS: resident data extension, section 27; segments 55B3:0042. Data contributions are exact;
 * original translation unit completeness is unproven.
 * Windows: none (DOS only), based on the platform-specific code or DOS release data.
 *
 * This contribution follows BEGDATA at 55B3:0042. Its only reference is
 * version_message_pointer in the next object: an external-symbol relocation group
 * proves separate files. The text resembles "Ver 1.00 " __TIMESTAMP__;
 * the original file time is unknown, so the version stamp is spelled out.
 */

/*
 * DOS build version and timestamp displayed by the event handler.
 */
char dos_version_string[] = "Ver 1.00 Fri Dec 06 14:51:14 1991";
