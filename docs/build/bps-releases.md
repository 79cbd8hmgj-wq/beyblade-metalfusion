# BPS patch-only releases

`bps.py` emits deterministic BPS1 using SourceRead and TargetRead actions and validates source, target, and patch CRC32 plus sizes. Every build reapplies its patch and requires exact target equality. Only `.bps`, manifests, and documentation may be distributed; source/built ROMs, saves, states, dumps, and commercial assets must never be committed or released. Corrupt or wrong-source patches fail clearly and never write in place.
