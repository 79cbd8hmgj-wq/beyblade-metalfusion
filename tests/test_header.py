import unittest
from tools.gba.header import decode_branch,inspect
class HeaderTests(unittest.TestCase):
 def test_branch(self):self.assertEqual(decode_branch(0xEA00002E),0xC0);self.assertIsNone(decode_branch(0))
 def test_short(self):self.assertRaises(ValueError,inspect,b"x")
