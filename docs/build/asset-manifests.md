# Asset manifests

Versioned manifests record stable ID, type, relative source/generated path and SHA-256, format, alignment, allocation class, sizes, dependencies, provenance/license note, and known consumers. Supported extensible types include raw binaries, palettes, tiles, maps, sprites, portraits, animation metadata, compressed blobs, audio, and code. Task 7 fixtures are project-created CC0 data; commercial extracted assets are forbidden.

Tracked preassembled code uses a text-safe `hex` representation. Manifests distinguish `source_sha256` (UTF-8 representation) from `decoded_sha256` (bytes inserted into the ROM); allocation and module verification always use the decoded-byte hash. Raw binary loading remains supported for ignored/generated future modules, not for tracked binary fixtures.
