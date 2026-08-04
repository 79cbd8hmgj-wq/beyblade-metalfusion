import binascii,struct
from .rom_image import RomError
MAGIC=b'SU_BUILD';SIZE=144
def _hash(v):
 b=bytes.fromhex(v) if isinstance(v,str) else bytes(v)
 if len(b)!=32:raise RomError('metadata hashes must be SHA-256')
 return b
def serialize(schema_version,project_version,profile_hash,source_hash,manifest_hash,tool_version,allocation_pointer=0,allocation_size=0,flags=0):
 strings=(project_version.encode()[:8].ljust(8,b'\0')+tool_version.encode()[:8].ljust(8,b'\0'))
 body=MAGIC+bytes([schema_version,flags])+strings+_hash(profile_hash)+_hash(source_hash)+_hash(manifest_hash)+struct.pack('<II',allocation_pointer,allocation_size)
 body=body.ljust(SIZE-4,b'\0');return body+struct.pack('<I',binascii.crc32(body))
def parse(data):
 if len(data)!=SIZE or data[:8]!=MAGIC:raise RomError('invalid metadata block')
 if binascii.crc32(data[:-4])!=struct.unpack('<I',data[-4:])[0]:raise RomError('metadata CRC mismatch')
 return {'schema_version':data[8],'flags':data[9],'project_version':data[10:18].rstrip(b'\0').decode(),'tool_version':data[18:26].rstrip(b'\0').decode(),'profile_hash':data[26:58].hex(),'source_hash':data[58:90].hex(),'manifest_core_hash':data[90:122].hex(),'allocation_pointer':struct.unpack('<I',data[122:126])[0]}
