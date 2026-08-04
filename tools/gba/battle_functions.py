"""Dependency-free scanning primitives for compact battle analysis."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
from .battle_enums import SHA256
from .arm_thumb import thumb_bl_target, literal_address

def halfwords(data:bytes,start:int,end:int):
    if start<0 or end>len(data) or start>end or start&1 or end&1: raise ValueError("invalid aligned extent")
    for off in range(start,end,2): yield off,struct.unpack_from("<H",data,off)[0]
def scan(data:bytes,start:int,end:int)->dict:
    literals=[]; calls=[]; words=list(halfwords(data,start,end))
    for i,(off,op) in enumerate(words):
        address=0x08000000+off
        if op&0xf800==0x4800:
            la=literal_address(address,op); lo=la-0x08000000
            if lo+4<=len(data): literals.append({"instruction":f"0x{address:08X}","pool":f"0x{la:08X}","value":f"0x{struct.unpack_from('<I',data,lo)[0]:08X}"})
        if op&0xf800==0xf000 and i+1<len(words) and words[i+1][1]&0xf800==0xf800:
            calls.append({"instruction":f"0x{address:08X}","target":f"0x{thumb_bl_target(address,op,words[i+1][1]):08X}"})
    return {"extent":{"rom_start":f"0x{start:08X}","rom_end_exclusive":f"0x{end:08X}"},"literal_loads":literals,"calls":calls}
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--rom",required=True); p.add_argument("--output",required=True); p.add_argument("--start",type=lambda x:int(x,0),default=0x2ff48); p.add_argument("--end",type=lambda x:int(x,0),default=0x3b700)
    a=p.parse_args(argv); data=Path(a.rom).read_bytes()
    if hashlib.sha256(data).hexdigest()!=SHA256: raise ValueError("unsupported ROM SHA-256")
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(scan(data,a.start,a.end),indent=2)+"\n")
if __name__=="__main__": main()
