import unittest,struct
from tools.gba.battle_functions import scan
class BattleFunctionTest(unittest.TestCase):
 def test_literal_and_bl(self):
  data=bytearray(16)
  struct.pack_into("<H",data,0,0x4801) # pool at 8
  struct.pack_into("<HH",data,2,0xF000,0xF800)
  struct.pack_into("<I",data,8,0x08001234)
  got=scan(bytes(data),0,12)
  self.assertEqual(got["literal_loads"][0]["value"],"0x08001234")
  self.assertEqual(got["calls"][0]["target"],"0x08000006")
 def test_bounds(self):
  with self.assertRaises(ValueError): scan(b"123",0,4)
