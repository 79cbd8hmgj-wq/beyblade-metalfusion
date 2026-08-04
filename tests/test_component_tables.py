import unittest
from dataclasses import replace
from pathlib import Path
from tools.gba.component_tables import *

ROM=Path(__file__).parents[1]/"Beyblade G-Revolution (USA).gba"

class ComponentTablesTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.rom=ROM.read_bytes()
 def test_counts_names_and_round_trips(self):
  expected={"spin-gears":("Normal","SG Metal Weight"),"attack-rings":("Cross Dragon","Hammer Task"),
            "blade-bases":("Flat","Final Clutch Base"),"weight-disks":("6 Balance","Circle Balance")}
  for spec in CATEGORIES:
   rows=extract_category(self.rom,spec.slug)
   self.assertEqual((rows[0].names[0],rows[-1].names[0]),expected[spec.slug])
   self.assertEqual(serialize_pointer_arrays(rows),self.rom[spec.offset:spec.end])
 def test_invalid_and_truncated(self):
  with self.assertRaisesRegex(ValueError,"invalid"): extract_category(self.rom,"nope")
  with self.assertRaisesRegex(ValueError,"truncated"): extract_category(b"", "attack-rings")
 def test_configuration(self):
  got=decode_template_configuration(bytes.fromhex("000f0540070b00ff"))
  self.assertEqual((got["attack_ring_id"],got["weight_disk_id"],got["blade_base_id"]),(15,5,7))
  self.assertEqual(got["field_23_u8"],255)
 def test_serializer_rejects_malformed(self):
  rows=extract_category(self.rom,"weight-disks")
  with self.assertRaises(ValueError): serialize_pointer_arrays([replace(rows[0],local_id=2)])

