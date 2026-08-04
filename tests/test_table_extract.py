import tempfile,unittest,json,csv
from pathlib import Path
from tools.gba.table_extract import *
class TestExtract(unittest.TestCase):
 def test_hash_and_outputs(self):
  rom=Path(__file__).parents[1]/'Beyblade G-Revolution (USA).gba'
  with tempfile.TemporaryDirectory() as d:
   s=extract(rom,Path(d));self.assertEqual(s['record_count'],83)
   rows=json.loads((Path(d)/'records.json').read_text());self.assertEqual(len(rows),83)
   self.assertEqual(len(list(csv.DictReader((Path(d)/'records.csv').read_text().splitlines()))),83)
 def test_malformed_schema(self):
  with self.assertRaises(ValueError):validate_record_document({'index': 0})
 def test_unsupported(self):
  with self.assertRaises(ValueError):validate_rom(b'not rom')
  self.assertEqual(len(validate_rom(b'not rom',True)),64)
