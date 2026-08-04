import unittest
from tools.gba.arm_thumb import *
class TestThumb(unittest.TestCase):
 def test_literal(self): self.assertEqual(literal_address(0x0803dd1e,0x4902),0x0803dd28)
 def test_reject(self):
  with self.assertRaises(ValueError):literal_address(0,0)
