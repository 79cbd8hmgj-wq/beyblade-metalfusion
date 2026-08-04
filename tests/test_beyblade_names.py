import unittest
from pathlib import Path
from tools.gba.beyblade_names import catalogue
class TestNames(unittest.TestCase):
 def test_catalogue_is_code_indexed(self):
  c=catalogue((Path(__file__).parents[1]/'Beyblade G-Revolution (USA).gba').read_bytes())
  self.assertEqual((len(c),c[0]['canonical_index'],c[-1]['displayed_text']),(83,0,'Rushing Boar'))
