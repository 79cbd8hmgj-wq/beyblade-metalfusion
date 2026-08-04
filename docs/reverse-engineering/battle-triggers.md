# Battle triggers

Five confirmed high-ROM bindings share `TriggerBattle` stream `0x0809B350`.
Its initial words are `0x04, 0x9B, 0x0E, 0x11, 0x10, 0xCF, 0x16`, followed by a
ROM pointer. Parameter semantics and result codes remain **unknown** until the
consumer and a live battle handoff are traced. The extractor therefore exposes
neutral words and byte-perfect serialization; it does not label opponent,
arena, AI, reward, or branches without evidence.
