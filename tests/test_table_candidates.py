import unittest
from tools.gba.table_candidates import pointer_field_counts,STRIDES
class TestCandidates(unittest.TestCase):
 def test_required_strides(self): self.assertIn(40,STRIDES);self.assertEqual(len(STRIDES),17)
 def test_bounds(self):
  with self.assertRaises(ValueError):pointer_field_counts(b'123',0,1,40)
