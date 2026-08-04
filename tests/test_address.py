import unittest
from tools.gba.address import *
class AddressTests(unittest.TestCase):
 def test_round_trip_and_mirrors(self):
  for x in (0,1,0x123456,0x1ffffff):self.assertEqual(address_to_offset(offset_to_address(x)),x)
  self.assertEqual(address_to_offset(0x0A123456),0x123456);self.assertEqual(normalize_rom_address(0x0C123457),0x08123457)
 def test_invalid(self):
  for x in (-1,0x2000000):self.assertRaises(ValueError,offset_to_address,x)
  self.assertRaises(ValueError,address_to_offset,0x02000000)
 def test_thumb_and_regions(self):
  self.assertEqual(split_thumb_pointer(0x08012345),(0x08012344,True))
  self.assertEqual(classify(0x02000000),"EWRAM");self.assertEqual(classify(0x10000000),"unmapped/unknown")
