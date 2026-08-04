import unittest
from pathlib import Path
from tools.gba.battle_enums import extract
class BattleEnumsTest(unittest.TestCase):
 def test_supported_rom_tables(self):
  p=Path("Beyblade G-Revolution (USA).gba")
  if not p.exists(): self.skipTest("research ROM absent")
  result=extract(p.read_bytes())
  self.assertEqual([r["value"] for r in result["move"]],list(range(7)))
  self.assertEqual(result["move"][6]["label"],"RPS_MOVE_DODGE")
  self.assertEqual(result["type"][7]["label"],"RPS_TYPE_HURT")
 def test_rejects_other_hash(self):
  with self.assertRaisesRegex(ValueError,"unsupported ROM"): extract(bytes(1024))
