import unittest
from tools.gba.battle_trace import parse
class BattleTraceTest(unittest.TestCase):
 def test_parse(self):
  self.assertEqual(parse("# x\nR0=0x20\nMOVE=3\n")["observations"],[{"key":"R0","value":32},{"key":"MOVE","value":3}])
 def test_bad(self):
  with self.assertRaisesRegex(ValueError,"line 1"): parse("not gdb")
