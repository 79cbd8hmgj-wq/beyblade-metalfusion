import unittest
from tools.gba.compression import lz77,header_scan
class CompressionTests(unittest.TestCase):
 def test_literal(self):self.assertEqual(lz77(b"\x10\x20\0\0"+b"\0abcdefgh"*4,0)["decompressed_size"],32)
 def test_reject(self):self.assertIsNone(lz77(b"\x10\xff\xff\xff",0));self.assertIsNone(lz77(b"\x20\0\0\0",0))
 def test_all_header_families(self):
  d=b"".join(bytes((x,32,0,0))+b"xxxx" for x in (0x10,0x20,0x30,0x80));self.assertEqual(len(header_scan(d)),4)
