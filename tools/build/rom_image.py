"""Immutable-source ROM image and guarded, auditable writes."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
from pathlib import Path
import os, tempfile
ROM_BASE=0x08000000; MAX_SIZE=0x02000000
SUPPORTED_SHA256="c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"
SUPPORTED_SIZE=0x400000
class RomError(ValueError): pass
def digest(b:bytes)->str:return sha256(b).hexdigest()
def parse_hex(v, *, name="value"):
    if isinstance(v,int): return v
    if not isinstance(v,str) or not v.startswith("0x") or v != v.lower() or len(v)<3: raise RomError(f"{name} must be strict lowercase 0x hexadecimal")
    try:return int(v[2:],16)
    except ValueError:raise RomError(f"invalid {name}")
def offset_to_runtime(o:int)->int:
    if not 0<=o<MAX_SIZE: raise RomError("ROM offset outside Game Pak window")
    return ROM_BASE+o
def runtime_to_offset(a:int)->int:
    # Normalize 0x08/0x0a/0x0c mirrors.
    if not 0x08000000<=a<0x0e000000: raise RomError("not a Game Pak address")
    o=(a-0x08000000)%0x02000000
    if o>=MAX_SIZE: raise RomError("invalid mirror")
    return o
@dataclass(frozen=True)
class Change:
    operation_id:str; offset:int; runtime_address:int; length:int; old_sha256:str; new_sha256:str; expected:str|None; source_artifact:str|None
    def json(self):
        d=asdict(self); d["offset"]=f"0x{self.offset:08x}"; d["runtime_address"]=f"0x{self.runtime_address:08x}"; return d
class RomImage:
    def __init__(self, source:bytes, source_path:Path|None=None):
        self.source=bytes(source); self.data=bytearray(source); self.source_path=source_path.resolve() if source_path else None; self.source_hash=digest(source); self.changes=[]; self._writes=[]; self.expansion_fill=None
    @classmethod
    def load(cls,path, expected_hash=SUPPORTED_SHA256, expected_size=SUPPORTED_SIZE, research_override=False):
        p=Path(path); data=p.read_bytes()
        if len(data)!=expected_size: raise RomError(f"source size {len(data):#x}, expected {expected_size:#x}")
        if digest(data)!=expected_hash and not research_override: raise RomError("unsupported source ROM SHA-256")
        return cls(data,p)
    def _bounds(self,o,n):
        if o<0 or n<0 or o+n>len(self.data):raise RomError("out-of-bounds ROM access")
    def read(self,o,n):self._bounds(o,n);return bytes(self.data[o:o+n])
    def read_u8(self,o):return self.read(o,1)[0]
    def read_u16(self,o):return int.from_bytes(self.read(o,2),'little')
    def read_u32(self,o):return int.from_bytes(self.read(o,4),'little')
    def expand(self,target,fill=0xff):
        if target<len(self.data) or target>MAX_SIZE or target&(target-1):raise RomError("target must be a power of two, >= source, <= 32 MiB")
        if not 0<=fill<=255:raise RomError("invalid fill")
        self.data.extend(bytes([fill])*(target-len(self.data))); self.expansion_fill=fill
    def write(self,o,b,operation_id,expected=None,source_artifact=None,depends_on=()):
        b=bytes(b); old=self.read(o,len(b))
        if expected is not None and old!=bytes(expected):raise RomError(f"{operation_id}: expected-byte guard failed at {o:#x}")
        for a,z,prior in self._writes:
            if o<z and a<o+len(b) and prior not in depends_on:raise RomError(f"{operation_id}: overlaps {prior}")
        if old==b:return False
        self.data[o:o+len(b)]=b; self._writes.append((o,o+len(b),operation_id))
        self.changes.append(Change(operation_id,o,offset_to_runtime(o),len(b),digest(old),digest(b),expected.hex() if expected is not None else None,source_artifact));return True
    def write_u8(self,o,v,op,**kw):return self.write(o,bytes([v]),op,**kw)
    def write_u16(self,o,v,op,**kw):return self.write(o,v.to_bytes(2,'little'),op,**kw)
    def write_u32(self,o,v,op,**kw):return self.write(o,v.to_bytes(4,'little'),op,**kw)
    def write_rom_pointer(self,o,target,op,thumb=False,**kw):
        if target&1:raise RomError("unaligned target")
        value=offset_to_runtime(target)|(1 if thumb else 0);return self.write_u32(o,value,op,**kw)
    def verify_source_unchanged(self):
        return self.source_path is None or digest(self.source_path.read_bytes())==self.source_hash
    def atomic_write(self,path):
        p=Path(path).resolve()
        if self.source_path and p==self.source_path:raise RomError("output resolves to source ROM")
        p.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.tmp-',dir=p.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(self.data);f.flush();os.fsync(f.fileno())
            os.replace(tmp,p)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    def header_errors(self):
        if len(self.data)<0xc0:return ["ROM shorter than GBA header"]
        e=[]
        if self.data[0xb2]!=0x96:e.append("invalid fixed value")
        check=(-sum(self.data[0xa0:0xbd])-0x19)&0xff
        if self.data[0xbd]!=check:e.append("invalid header complement")
        return e
    def recalculate_header_checksum(self):self.data[0xbd]=(-sum(self.data[0xa0:0xbd])-0x19)&0xff
