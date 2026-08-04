# Persistence expansion feasibility

No Spirit Unbound field is implemented.

| Strategy | Assessment | Reason |
|---|---|---|
| Alter current header words/constants | unsafe | breaks retail validation/commit metadata |
| Reuse semantically unresolved payload bytes | unsafe | actively serialized and checksummed |
| Use apparent zero runs | unsafe | zero content is not non-use evidence |
| Use blocks `0x3EF–0x3FF` in a ROM patch | questionable | no direct original caller found, but indirect/library reservation not disproven |
| Compress/replace original payload | unknown | requires semantic completion and migration recovery |
| External sidecar/versioned new format | likely_safe | leaves original image untouched; integration design remains future work |

Custom identity/avatar/palettes/origin, Bey name, Spirit/temperament/bond/affinities/moves/masteries, rival summaries, favorite builds and NG+ flags all inherit the selected strategy's classification. A future migration should parse/preserve the complete old image, use an explicit new version outside validated legacy metadata, be copy-on-write, and retain rollback. Tail use is not classified safe.
