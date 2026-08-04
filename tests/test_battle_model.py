import unittest
from tools.gba.battle_model import EffectiveStats,move_value,clamp_nonnegative
class BattleModelTest(unittest.TestCase):
 def test_all_confirmed_paths(self):
  s=EffectiveStats(10,20,30); rng=lambda n: n-1
  self.assertEqual([move_value(0,m,s,rng) for m in range(4)],[10,20,20,0])
  self.assertEqual([move_value(1,m,s,rng) for m in range(3)],[20,20,60])
  self.assertEqual(move_value(2,0,s,rng),5)
  self.assertEqual(move_value(3,3,s,rng),60)
  self.assertEqual(move_value(3,2,s,rng),0)
  self.assertEqual(move_value(4,0,s,rng),0)
  self.assertEqual(move_value(5,2,s,rng),60)
  self.assertEqual(move_value(6,0,s,rng),3)
  self.assertEqual(move_value(7,0,s,rng),0)
 def test_clamp(self): self.assertEqual((clamp_nonnegative(-1),clamp_nonnegative(2)),(0,2))
