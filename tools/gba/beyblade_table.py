"""Task 2 complete-Beyblade table model for the supported US ROM."""
from __future__ import annotations
from dataclasses import dataclass
import struct

ROM_BASE=0x08000000
TABLE_OFFSET=0x0007A1F4
RECORD_COUNT=83
RECORD_STRIDE=40
TABLE_END=TABLE_OFFSET+RECORD_COUNT*RECORD_STRIDE
LANGUAGES=("english","french","german","italian","spanish")
CONFIDENCE=("confirmed","strongly_supported","candidate","unknown")

@dataclass(frozen=True)
class BeybladeEntry:
    index:int; source_offset:int; name_pointers:tuple[int,...]
    field_14_ptr:int; field_18_ptr:int; field_1c_bytes:bytes
    field_20_bytes:bytes; field_24_u8:int; season:int; field_26_u16:int
    raw:bytes
    @property
    def runtime_address(self): return ROM_BASE+self.source_offset

def parse_record(raw:bytes,index:int,source_offset:int)->BeybladeEntry:
    if len(raw)!=RECORD_STRIDE: raise ValueError(f"record must be {RECORD_STRIDE} bytes")
    names=struct.unpack_from('<5I',raw)
    p14,p18=struct.unpack_from('<2I',raw,0x14)
    f24=raw[0x24]; season=raw[0x25]; f26=struct.unpack_from('<H',raw,0x26)[0]
    return BeybladeEntry(index,source_offset,names,p14,p18,raw[0x1c:0x20],raw[0x20:0x24],f24,season,f26,bytes(raw))

def serialize_record(entry:BeybladeEntry)->bytes:
    out=bytearray(entry.raw)
    struct.pack_into('<5I',out,0,*entry.name_pointers)
    struct.pack_into('<2I',out,0x14,entry.field_14_ptr,entry.field_18_ptr)
    out[0x1c:0x20]=entry.field_1c_bytes; out[0x20:0x24]=entry.field_20_bytes
    out[0x24]=entry.field_24_u8; out[0x25]=entry.season
    struct.pack_into('<H',out,0x26,entry.field_26_u16)
    return bytes(out)

def extract_records(rom:bytes)->list[BeybladeEntry]:
    if len(rom)<TABLE_END: raise ValueError(f"truncated ROM: need through 0x{TABLE_END:08X}")
    return [parse_record(rom[o:o+RECORD_STRIDE],i,o) for i,o in enumerate(range(TABLE_OFFSET,TABLE_END,RECORD_STRIDE))]

def read_c_string(rom:bytes,address:int)->str:
    off=address-ROM_BASE
    if not 0<=off<len(rom): raise ValueError(f"pointer 0x{address:08X} outside ROM")
    end=rom.find(b'\0',off)
    if end<0: raise ValueError("unterminated string")
    return rom[off:end].decode('ascii')
