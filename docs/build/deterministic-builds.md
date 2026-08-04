# Deterministic builds and audits

`scripts/verify-build.sh SOURCE.gba` performs two clean builds and recursively compares them. ROM, BPS, manifest, JSON/CSV allocation map, changed ranges, and Markdown report must match byte-for-byte. Outputs omit time by default, so `SOURCE_DATE_EPOCH` is unnecessary. Each write records stable operation ID, offset/runtime address, length, old/new SHA-256, guard, and source artifact. Validation rejects undeclared differences, overlap, bad header, bad source integrity, or failed BPS reconstruction.
