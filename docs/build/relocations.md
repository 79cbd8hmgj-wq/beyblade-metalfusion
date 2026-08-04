# Relocations

Relocations operate only on enumerated or parser-derived sites. Encodings are little-endian file offsets, ROM pointers (`0x08000000 + offset`, accepting Game Pak mirrors when decoding), and Thumb pointers with bit zero set. Arrays, language-major rows, fixed-stride tables, and variable blobs are represented as explicit site lists. The engine checks the old word, target alignment, pointer mode, bounds, overlaps, and every recorded old/new target. It never scans and replaces matching words globally.
