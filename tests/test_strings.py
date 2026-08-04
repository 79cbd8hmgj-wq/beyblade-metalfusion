import unittest,struct
from tools.gba.strings import scan,clusters,classify_text
class StringTests(unittest.TestCase):
 def test_features(self):
  d=bytearray(64);d[4:9]=b"hello";d[9]=0;struct.pack_into('<I',d,32,0x08000004)
  s=scan(bytes(d))[0];self.assertTrue(s["null_terminated"]);self.assertEqual(s["pointer_references"],1)
 def test_classify_cluster(self):
  self.assertEqual(classify_text("initTournament"),"debug/function identifiers")
  self.assertEqual(len(clusters([{"offset":x} for x in (0,10,20)])),1)
