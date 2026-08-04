"""Byte-preserving model of G-Revolution's 64-Kbit EEPROM save."""
from __future__ import annotations
import argparse, hashlib, json, struct
from dataclasses import dataclass
from pathlib import Path
ROM_SHA256='c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5'
EEPROM_SIZE=0x2000; BLOCK_SIZE=8; BLOCK_COUNT=0x400
HEADER_SIZE=0x18; PAYLOAD_SIZE=0x1f60; PAYLOAD_BLOCK_FIRST=3; PAYLOAD_BLOCK_LAST=0x3ee
TAIL_OFFSET=0x1f78; MAGIC=0xfeedface; CONSTANT_WORDS=(0x00370053,0x00f6009c)
SIGNATURE=b'EEPROM_V124\0'; SIGNATURE_OFFSET=0x3a93bc
class SaveFormatError(ValueError): pass

def checksum(payload:bytes)->int:
 if len(payload)!=PAYLOAD_SIZE: raise SaveFormatError(f'payload must be 0x{PAYLOAD_SIZE:X} bytes')
 return sum(struct.unpack_from('<I',payload,o)[0] for o in range(4,PAYLOAD_SIZE,4))&0xffffffff
@dataclass(frozen=True)
class Header:
 magic:int; payload_checksum:int; unknown_08:int; unknown_0c:int; constant_10:int; constant_14:int
 @classmethod
 def parse(cls,data:bytes):
  if len(data)!=HEADER_SIZE: raise SaveFormatError('header must be 24 bytes')
  return cls(*struct.unpack('<6I',data))
 def to_bytes(self)->bytes:return struct.pack('<6I',self.magic,self.payload_checksum,self.unknown_08,self.unknown_0c,self.constant_10,self.constant_14)
 def validation(self,payload:bytes|None=None)->dict:
  checks={'magic':self.magic==MAGIC,'constants':(self.constant_10,self.constant_14)==CONSTANT_WORDS}
  if payload is not None: checks.update(header_checksum=self.payload_checksum==checksum(payload),payload_checksum=struct.unpack_from('<I',payload)[0]==checksum(payload))
  checks['valid']=all(checks.values()); return checks
@dataclass(frozen=True)
class SaveImage:
 header:Header; payload:bytes; tail:bytes
 @classmethod
 def parse(cls,data:bytes,allow_padding:bool=False):
  if allow_padding and len(data)>EEPROM_SIZE and all(x in (0,0xff) for x in data[EEPROM_SIZE:]): data=data[:EEPROM_SIZE]
  if len(data)!=EEPROM_SIZE: raise SaveFormatError(f'save must be exactly 0x{EEPROM_SIZE:X} bytes')
  return cls(Header.parse(data[:HEADER_SIZE]),data[HEADER_SIZE:TAIL_OFFSET],data[TAIL_OFFSET:])
 def to_bytes(self)->bytes:
  out=self.header.to_bytes()+self.payload+self.tail
  if len(out)!=EEPROM_SIZE: raise SaveFormatError('invalid preserved ranges')
  return out
 def report(self)->dict:
  return {'format':'beyblade-g-revolution-eeprom-v1','size':EEPROM_SIZE,'header':{**self.header.__dict__,'validation':self.header.validation(self.payload)},'payload':{'offset':HEADER_SIZE,'size':len(self.payload),'stored_checksum':struct.unpack_from('<I',self.payload)[0],'calculated_checksum':checksum(self.payload)},'tail':{'offset':TAIL_OFFSET,'size':len(self.tail),'classification':'unreferenced_candidate','sha256':hashlib.sha256(self.tail).hexdigest()}}
def inventory_bit(payload:bytes,offset:int,item_id:int,count:int)->bool:
 if not 0<=item_id<count: raise SaveFormatError('invalid component ID')
 if offset<0 or offset+(count+7)//8>len(payload): raise SaveFormatError('inventory bitfield out of bounds')
 return bool(payload[offset+item_id//8]&(1<<(item_id%8)))
def validate_rom(data:bytes,override:bool=False):
 digest=hashlib.sha256(data).hexdigest()
 if digest!=ROM_SHA256 and not override: raise SaveFormatError(f'unsupported ROM SHA-256: {digest}')
 hits=[]; start=0
 while True:
  i=data.find(SIGNATURE,start)
  if i<0: break
  hits.append(i); start=i+1
 if hits!=[SIGNATURE_OFFSET]: raise SaveFormatError(f'EEPROM signature starts were {[hex(x) for x in hits]}')
 return digest
def static_report(data:bytes,override=False)->dict:
 digest=validate_rom(data,override)
 return {'rom_sha256':digest,'signature':{'text':'EEPROM_V124','rom_offset':'0x003A93BC','runtime_address':'0x083A93BC','confidence':'confirmed'},'eeprom':{'capacity_bytes':EEPROM_SIZE,'blocks':BLOCK_COUNT,'block_size':BLOCK_SIZE,'confidence':'strongly_supported'},'ranges':[{'blocks':'0x000-0x002','offset':'0x0000','size':'0x18','purpose':'transaction_header'},{'blocks':'0x003-0x3EE','offset':'0x0018','size':'0x1F60','purpose':'serialized_payload'},{'blocks':'0x3EF-0x3FF','offset':'0x1F78','size':'0x88','purpose':'unreferenced_candidate'}]}
def write_copy(source:Path,dest:Path,image:SaveImage):
 if source.resolve()==dest.resolve(): raise SaveFormatError('refusing in-place write')
 dest.write_bytes(image.to_bytes())
def main(argv=None):
 p=argparse.ArgumentParser(); p.add_argument('--rom');p.add_argument('--save');p.add_argument('--output',required=True);p.add_argument('--research-override',action='store_true');p.add_argument('--allow-padding',action='store_true')
 a=p.parse_args(argv)
 if bool(a.rom)==bool(a.save):p.error('choose exactly one of --rom or --save')
 result=static_report(Path(a.rom).read_bytes(),a.research_override) if a.rom else SaveImage.parse(Path(a.save).read_bytes(),a.allow_padding).report()
 out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
