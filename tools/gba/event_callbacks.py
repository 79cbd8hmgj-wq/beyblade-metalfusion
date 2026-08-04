"""Extraction of the directly evidenced name-to-command-stream bindings."""
from __future__ import annotations
import struct
from .event_records import ROM_BASE, normalize_rom_pointer

ANCHORS = ("atExitToStreets", "atDojo", "inAlley", "LockPoolDoors", "StartPrelim", "StadiumEntry", "TriggerBattle")

def extract_bindings(rom: bytes) -> list[dict]:
    out=[]
    for name in ANCHORS:
        string_offset=rom.find(name.encode()+b"\0", 0x300000)
        if string_offset < 0: continue
        needle=struct.pack("<I", ROM_BASE+string_offset); pos=0
        while True:
            pos=rom.find(needle,pos)
            if pos < 0: break
            if pos+8 > len(rom): raise ValueError("truncated binding")
            target=struct.unpack_from("<I",rom,pos+4)[0]
            target_offset=normalize_rom_pointer(target, len(rom))
            out.append({"name":name,"string_offset":f"0x{string_offset:08X}","binding_offset":f"0x{pos:08X}",
                        "stream_address":f"0x{target:08X}","stream_offset":f"0x{target_offset:08X}",
                        "mode":"data","confidence":"confirmed"})
            pos+=4
    return sorted(out,key=lambda x:(x["name"],x["binding_offset"]))
