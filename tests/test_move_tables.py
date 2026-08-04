import unittest
from pathlib import Path
from tools.gba.move_tables import *
class MoveTablesTest(unittest.TestCase):
 def test_pairs_and_round_trip(self):
  rom=(Path(__file__).parents[1]/"Beyblade G-Revolution (USA).gba").read_bytes();p=extract_pairs(rom)
  self.assertEqual(len(p),32);self.assertEqual(p[0]["bit_beast"]["names"][0],"Dragoon")
  self.assertEqual(p[0]["special_move"]["names"][0],"Gaia Storm")
  self.assertEqual(serialize_pairs(p),rom[PAIR_OFFSET:END])
 def test_truncated(self):
  with self.assertRaisesRegex(ValueError,"truncated"):extract_pairs(b"")

