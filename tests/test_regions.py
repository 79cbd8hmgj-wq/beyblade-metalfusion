import unittest
from tools.gba.regions import fill_runs,free_space
class RegionTests(unittest.TestCase):
 def test_fill(self):self.assertEqual(fill_runs(b"x"+b"\xff"*64,64),[(1,65,255)])
 def test_trailing(self):self.assertEqual(free_space(b"a"*16+b"\0"*256,[],[])[0]["confidence"],"likely_safe")
