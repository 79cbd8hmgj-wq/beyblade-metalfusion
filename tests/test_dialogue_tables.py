import pytest
from tools.gba.dialogue_tables import *
def test_unknown_control_roundtrip():
 raw=b'Hi\x01\x7f!\x1f\0'; assert encode_control_stream(parse_control_stream(raw))==raw
def test_language_lookup():
 assert language_lookup([[1,2],[3,4]],1,0)==3
 with pytest.raises(IndexError): language_lookup([[1]],2,0)
