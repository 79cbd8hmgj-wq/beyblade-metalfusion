from pathlib import Path
import pytest
from tools.gba.event_architecture import analyse
def test_unsupported_hash(tmp_path):
 p=tmp_path/'x.gba'; p.write_bytes(b'x')
 with pytest.raises(ValueError): analyse(p)
 assert analyse(p,True)['source_rom_modified'] is False
