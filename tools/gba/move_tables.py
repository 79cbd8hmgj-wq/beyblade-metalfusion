"""Bit-Beast/special-move localization lookup at the end of the mixed region."""
from __future__ import annotations
import struct
from .component_tables import LANGUAGES, ROM_BASE, _string

PAIR_OFFSET = 0x00079CF4
PAIR_COUNT = 32
ROW_SIZE = 20
PAIR_SIZE = 40
END = PAIR_OFFSET + PAIR_COUNT * PAIR_SIZE

def extract_pairs(rom: bytes) -> list[dict]:
    if len(rom) < END:
        raise ValueError(f"truncated ROM: need through 0x{END:08X}")
    result=[]
    for i in range(PAIR_COUNT):
        rows=[]
        for kind,delta in (("bit_beast",0),("special_move",ROW_SIZE)):
            off=PAIR_OFFSET+i*PAIR_SIZE+delta
            ptrs=struct.unpack_from("<5I",rom,off)
            rows.append({"kind":kind,"source_offset":off,"runtime_address":ROM_BASE+off,
                         "pointers":ptrs,"names":tuple(_string(rom,p) for p in ptrs)})
        result.append({"pair_id":i,"bit_beast":rows[0],"special_move":rows[1]})
    return result

def serialize_pairs(pairs: list[dict]) -> bytes:
    if len(pairs)!=PAIR_COUNT: raise ValueError(f"expected {PAIR_COUNT} pairs")
    return b"".join(struct.pack("<5I",*pair[kind]["pointers"])
                    for pair in pairs for kind in ("bit_beast","special_move"))

