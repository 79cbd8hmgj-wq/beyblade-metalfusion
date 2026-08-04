import struct
from tools.gba.event_callbacks import extract_bindings
def test_duplicate_callback_names():
 d=bytearray(0x300200); s=0x300000; d[s:s+14]=b'TriggerBattle\0'; ptr=0x08000000+s
 for p in (0x10,0x20): struct.pack_into('<II',d,p,ptr,0x08000100)
 x=extract_bindings(bytes(d)); assert len(x)==2 and {e['name'] for e in x}=={'TriggerBattle'}
