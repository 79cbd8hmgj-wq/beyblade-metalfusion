import hashlib, subprocess, sys, tempfile, unittest
from pathlib import Path
from tools.gba.save_format import EEPROM_SIZE, TAIL_OFFSET
from src.custom_blader.custom_state import *
from src.custom_blader.custom_save import *
from src.custom_blader.name_render import substitute
from src.custom_blader.creator_menu import CreatorModel
from tools.gba.custom_save_extension import write_extension
class Task8Models(unittest.TestCase):
 def distinct_state(self):
  return sanitize(CustomBladerState(initialized=7,player_name='Rin7',bey_name='Core9',avatar_id=1,portrait_id=2,skin_palette_id=3,hair_style_id=1,hair_palette_id=2,outfit_palette_id=3,origin_id=1,tendency_id=2,blank_core_state=0,blank_core_id=0xF0,current_template_id=11,attack_ring_id=12,weight_disk_id=13,spin_gear_id=14,blade_base_id=15,future_flags=16))
 def test_defaults_validation_names(self):
  s=default_state(); self.assertEqual(s.player_name,'Blader'); self.assertEqual(s.blank_core_id,0xF0); self.assertTrue(is_valid(s))
  s.player_name=''; self.assertEqual(sanitize(s).player_name,'Blader')
  s.player_name='A'*40; self.assertEqual(len(sanitize(s).player_name),12)
 def test_token_aware_substitution(self):
  s=default_state(); s.player_name='Kaiya'; sanitize(s)
  self.assertEqual(substitute('Tyson and TYSON met Takao',s),'Kaiya and KAIYA met Kaiya')
  self.assertEqual(substitute('NotTyson Tysonic',s),'NotTyson Tysonic')
  self.assertEqual(substitute('Gingka and GINGKA',s),'Gingka and GINGKA')
  self.assertEqual(substitute('Tyson',s,True),'Tyson')
 def test_distinct_slot_roundtrip_and_selection(self):
  s=self.distinct_state(); raw=serialize_slot(s,1); ok,seq,st,msg=parse_slot(raw)
  self.assertTrue(ok,msg); self.assertEqual(seq,1)
  for field in s.to_dict(): self.assertEqual(getattr(st,field),getattr(s,field),field)
  older=serialize_slot(default_state(),0xfffffffe); newer=serialize_slot(s,1); self.assertEqual(select_newest(older,newer)[0],'B')
  self.assertFalse(seq_newer(0x80000000,0)); self.assertFalse(seq_newer(0,0x80000000))
  corrupt=bytearray(newer); corrupt[12]^=1; self.assertEqual(select_newest(older,bytes(corrupt))[0],'A')
 def test_interrupted_write_simulation(self):
  old=serialize_slot(default_state(),1); new=serialize_slot(self.distinct_state(),2)
  blank=bytes(SLOT_SIZE)
  for cut in range(0,SLOT_SIZE+1,8):
   partial=new[:cut]+blank[cut:]
   chosen=select_newest(old,partial)
   self.assertIn(chosen[0],('A','B'))
   self.assertEqual(chosen[2].player_name,'Blader' if chosen[0]=='A' else 'Rin7')
 def test_creator_navigation_and_bounds(self):
  c=CreatorModel(); self.assertEqual(c.step,'player_name'); c.next().next().back(); self.assertEqual(c.step,'bey_name')
  c.choose('avatar_id',99); self.assertEqual(c.state.avatar_id,0); c.cancel(); self.assertTrue(c.cancelled)
 def test_blank_core_invariants(self):
  s=default_state(); s.blank_core_id=1; s.blank_core_state=9; sanitize(s); self.assertEqual((s.blank_core_id,s.blank_core_state),(0xF0,0))
 def test_editor_preserves_prefix_padding_and_only_one_slot(self):
  with tempfile.TemporaryDirectory() as d:
   before=bytes([x&0xff for x in range(EEPROM_SIZE)])+b'WRAPPER'
   src=Path(d)/'in.sav'; out=Path(d)/'out.sav'; src.write_bytes(before)
   write_extension(src,out,self.distinct_state(),allow_unverified=True)
   after=out.read_bytes(); self.assertEqual(before[:TAIL_OFFSET],after[:TAIL_OFFSET]); self.assertEqual(before[EEPROM_SIZE:],after[EEPROM_SIZE:])
   changed=[i for i,(a,b) in enumerate(zip(before,after)) if a!=b]
   self.assertTrue(all(TAIL_OFFSET <= i < TAIL_OFFSET+SLOT_SIZE for i in changed))
   self.assertRaises(Exception,write_extension,src,Path(d)/'blocked.sav',self.distinct_state())
 def test_thumb_fixture_hash_and_bytes(self):
  raw=bytes.fromhex(Path('data/build/fixtures/task8-foundation.hex').read_text())
  self.assertEqual(raw,b'\x70\x47')
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'c7dfbb7d02759eacb64dbc916c1bb6f21eabaff1c1032ea5c9176abf7fd28df8')
if __name__=='__main__': unittest.main()
