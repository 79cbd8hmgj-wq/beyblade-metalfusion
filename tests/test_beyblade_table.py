import unittest
from pathlib import Path
from tools.gba.beyblade_table import *
ROM=Path(__file__).parents[1]/'Beyblade G-Revolution (USA).gba'
class TestTable(unittest.TestCase):
 @classmethod
 def setUpClass(c): c.data=ROM.read_bytes(); c.rows=extract_records(c.data)
 def test_extent(self): self.assertEqual((len(self.rows),self.rows[0].source_offset,self.rows[-1].source_offset),(83,0x7a1f4,0x7aec4))
 def test_first_middle_final(self):
  self.assertEqual([read_c_string(self.data,self.rows[i].name_pointers[0]) for i in (0,41,82)],['Dragoon S','Bakushin-Oh','Rushing Boar'])
 def test_all_languages_shared(self): self.assertTrue(all(len(set(r.name_pointers))==1 for r in self.rows))
 def test_round_trip_and_unknowns(self): self.assertTrue(all(serialize_record(r)==r.raw for r in self.rows))
 def test_truncated(self):
  with self.assertRaises(ValueError):extract_records(self.data[:TABLE_END-1])
 def test_malformed_record(self):
  with self.assertRaises(ValueError):parse_record(b'bad',0,0)
