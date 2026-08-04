import struct,unittest
from tools.gba.pointers import scan,runs
class PointerTests(unittest.TestCase):
 def test_mirror_thumb_run(self):
  d=bytearray(64)
  for i,v in enumerate((0x08000021,0x0a000024,0x02000000)):struct.pack_into('<I',d,i*4,v)
  p=scan(bytes(d));self.assertEqual(len(p),3);self.assertTrue(p[0]["thumb"]);self.assertEqual(len(runs(p)),1)
