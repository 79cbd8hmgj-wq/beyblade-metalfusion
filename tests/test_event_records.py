import struct,pytest
from tools.gba.event_records import *
def test_named_round_trip_unknowns():
 raw=struct.pack('<III',2,0x10,0xe319)+b'atDojo\0\0'
 r=InlineNamedRecord.parse(raw,0); assert r.name=='atDojo'; assert r.to_bytes()==raw
def test_malformed():
 with pytest.raises(ValueError): InlineNamedRecord.parse(b'\0'*8,0)
def test_words_unknown_roundtrip():
 raw=struct.pack('<III',4,0xcf,0xdeadbeef); assert encode_words(decode_words(raw))==raw
def test_pointer_bounds():
 assert normalize_rom_pointer(0x08000020,0x100)==0x20
 with pytest.raises(ValueError): normalize_rom_pointer(0x07000000,0x100)
