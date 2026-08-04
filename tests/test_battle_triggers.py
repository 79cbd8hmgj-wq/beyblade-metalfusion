import struct,pytest
from tools.gba.battle_triggers import BattleTrigger
def test_roundtrip():
 raw=struct.pack('<IIII',4,0x9b,0xe,0x11); assert BattleTrigger.parse(raw).to_bytes()==raw
 with pytest.raises(ValueError): BattleTrigger.parse(b'abc')
