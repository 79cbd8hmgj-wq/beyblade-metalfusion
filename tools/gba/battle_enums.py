"""Extract the two battle diagnostic pointer tables from the supported ROM."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path

SHA256="c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"
TABLES=((0x77F24,8,"type"),(0x77F44,7,"move"))
def extract(data:bytes)->dict:
    if hashlib.sha256(data).hexdigest()!=SHA256: raise ValueError("unsupported ROM SHA-256")
    out={}
    for base,count,name in TABLES:
        rows=[]
        for value in range(count):
            ptr=struct.unpack_from("<I",data,base+4*value)[0]; off=ptr-0x08000000
            if not 0 <= off < len(data): raise ValueError("name pointer outside ROM")
            end=data.find(b"\0",off, min(off+128,len(data)))
            if end<0: raise ValueError("unterminated battle name")
            rows.append({"value":value,"label":data[off:end].decode("ascii"),
                         "pointer_entry_rom":f"0x{base+4*value:08X}",
                         "string_rom":f"0x{off:08X}","storage":"word",
                         "confidence":"strongly_supported"})
        out[name]=rows
    return out
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--rom",required=True); p.add_argument("--output")
    a=p.parse_args(argv); result=extract(Path(a.rom).read_bytes()); text=json.dumps(result,indent=2)+"\n"
    if a.output:
        output=Path(a.output); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(text)
    else: print(text,end="")
if __name__=="__main__": main()
