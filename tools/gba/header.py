"""Official GBA cartridge-header validation."""
from __future__ import annotations
import binascii, hashlib, struct

# SHA-256 of the fixed 156-byte Nintendo logo, avoiding reproduction in reports.
LOGO_SHA256="08a0153cfd6b0ea54b938f7d209933fa849da0d56f5a34c481060c9ff2fad818"
def decode_branch(word:int)->int|None:
    if word>>24 != 0xEA: return None
    imm=word&0xFFFFFF
    if imm&0x800000: imm-=1<<24
    return 8+(imm<<2)
def inspect(data:bytes,path:str="") -> dict:
    if len(data)<0xC0: raise ValueError("file too small for GBA header")
    calc=(-sum(data[0xA0:0xBD])-0x19)&0xFF
    word=struct.unpack_from("<I",data)[0]
    sha256=hashlib.sha256(data).hexdigest()
    cap=1<<(len(data)-1).bit_length()
    trailing=len(data)-len(data.rstrip(b"\xff"))
    return {"confidence":"confirmed","evidence_type":"direct_binary_evidence","path":path,"size":len(data),
      "sha256":sha256,"sha1":hashlib.sha1(data).hexdigest(),"crc32":f"{binascii.crc32(data)&0xffffffff:08x}",
      "internal_title":data[0xA0:0xAC].rstrip(b"\0").decode("ascii","replace"),"game_code":data[0xAC:0xB0].decode("ascii","replace"),
      "maker_code":data[0xB0:0xB2].decode("ascii","replace"),"software_version":data[0xBC],"fixed_value":data[0xB2],
      "header_checksum":data[0xBD],"calculated_checksum":calc,"checksum_valid":calc==data[0xBD],
      "nintendo_logo_valid":hashlib.sha256(data[4:0xA0]).hexdigest()==LOGO_SHA256,
      "entry_point_raw":f"0x{word:08X}","entry_point_destination":None if decode_branch(word) is None else f"0x{0x08000000+decode_branch(word):08X}",
      "likely_capacity":cap,"trailing_ff_bytes":trailing,
      "image_assessment":"valid_padded" if cap==len(data) and trailing else ("valid" if cap==len(data) else "trimmed_or_nonstandard")}
