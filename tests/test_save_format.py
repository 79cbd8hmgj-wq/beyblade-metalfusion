import hashlib,json,struct,tempfile,unittest
from pathlib import Path
from tools.gba.eeprom_library import block_offset
from tools.gba.save_diff import diff
from tools.gba.save_format import *
class SaveTests(unittest.TestCase):
 def payload(self):
  p=bytearray(PAYLOAD_SIZE);struct.pack_into('<I',p,4,0xffffffff);struct.pack_into('<I',p,8,2);struct.pack_into('<I',p,0,checksum(p));return bytes(p)
 def image(self):
  p=self.payload();h=Header(MAGIC,checksum(p),0,0,*CONSTANT_WORDS);return SaveImage(h,p,bytes(EEPROM_SIZE-TAIL_OFFSET))
 def test_layout(self):self.assertEqual(PAYLOAD_BLOCK_LAST-PAYLOAD_BLOCK_FIRST+1,1004);self.assertEqual(TAIL_OFFSET+0x88,EEPROM_SIZE);self.assertEqual(block_offset(0x3ff),0x1ff8);self.assertRaises(SaveFormatError,block_offset,0x400)
 def test_header_roundtrip_and_validation(self):
  x=self.image();self.assertEqual(Header.parse(x.header.to_bytes()),x.header);self.assertTrue(x.header.validation(x.payload)['valid'])
  self.assertFalse(Header(0,0,0,0,0,0).validation(x.payload)['valid'])
  self.assertFalse(Header(MAGIC,0,0,0,*CONSTANT_WORDS).validation(x.payload)['valid'])
 def test_checksum_overflow_and_exclusion(self):self.assertEqual(checksum(self.payload()),1);p=bytearray(self.payload());p[0]^=1;self.assertEqual(checksum(p),1)
 def test_full_roundtrip_unknown_preserved(self):
  x=self.image();raw=x.to_bytes();self.assertEqual(SaveImage.parse(raw).to_bytes(),raw)
  blank=bytes(EEPROM_SIZE);self.assertEqual(SaveImage.parse(blank).to_bytes(),blank)
 def test_sizes_and_padding(self):
  self.assertRaises(SaveFormatError,SaveImage.parse,b'x')
  self.assertRaises(SaveFormatError,SaveImage.parse,bytes(EEPROM_SIZE+1))
  self.assertEqual(len(SaveImage.parse(self.image().to_bytes()+b'\xff'*16,True).to_bytes()),EEPROM_SIZE)
 def test_inventory(self):
  p=bytearray(PAYLOAD_SIZE);p[10]=4;self.assertTrue(inventory_bit(p,10,2,77));self.assertRaises(SaveFormatError,inventory_bit,p,10,77,77)
 def test_diff_deterministic(self):
  a=self.image().to_bytes();b=bytearray(a);b[30]=1;d=diff(a,bytes(b));self.assertEqual(d['changed_byte_count'],1);self.assertEqual(json.dumps(d,sort_keys=True),json.dumps(diff(a,bytes(b)),sort_keys=True))
 def test_write_refuses_in_place(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(self.image().to_bytes());self.assertRaises(SaveFormatError,write_copy,p,p,self.image())
 def test_signature_and_hash(self):
  rom=Path('Beyblade G-Revolution (USA).gba').read_bytes();self.assertEqual(validate_rom(rom),ROM_SHA256);self.assertEqual(rom.find(SIGNATURE),SIGNATURE_OFFSET);self.assertEqual(rom.find(SIGNATURE,SIGNATURE_OFFSET+1),-1)
  self.assertRaises(SaveFormatError,validate_rom,b'bad')
if __name__=='__main__':unittest.main()
