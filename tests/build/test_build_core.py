import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.build.allocator import Allocator
from tools.build.bps import create,apply,BPSError
from tools.build.hooks import *
from tools.build.metadata import serialize,parse
from tools.build.profile import load
from tools.build.relocations import relocate_sites
from tools.build.rom_image import *
from tools.build.text_compiler import compile_pool,compile_string
class CoreTests(unittest.TestCase):
 def test_expansion_and_io(self):
  r=RomImage(bytes(range(256))*4);r.expand(2048,0xaa);self.assertEqual(r.read(1024,4),b'\xaa'*4)
  with self.assertRaises(RomError):r.expand(3000)
  r.write_u16(2,0x1234,'x',expected=b'\x02\x03');self.assertEqual(r.read_u16(2),0x1234);self.assertEqual(len(r.changes),1)
  with self.assertRaises(RomError):r.write(2,b'x','bad',expected=b'z')
 def test_path_refusal(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';p.write_bytes(b'x');r=RomImage(b'x',p)
   with self.assertRaises(RomError):r.atomic_write(p)
 def test_allocator(self):
  a=Allocator([{'start':'0x00400000','end':'0x00400100'}],[{'id':'r','start':'0x00400000','end':'0x00400010'}])
  x=a.allocate({'id':'b','size':'0x10','alignment':'0x10'});self.assertEqual(x.offset,0x400010)
  with self.assertRaises(RomError):a.allocate({'id':'i','size':'0x4','alignment':'0x1','fixed_offset':'0x00400010'})
  with self.assertRaises(RomError):Allocator([{'id':'internal','start':'0x0','end':'0x10'}],source_size=0x100)
 def test_pointers_relocation(self):
  self.assertEqual(runtime_to_offset(0x0a000010),0x10);self.assertEqual(offset_to_runtime(4),0x08000004)
  r=RomImage(bytearray(32));r.data[4:8]=(0x08000010).to_bytes(4,'little');relocate_sites(r,'r',[4],0x10,0x18);self.assertEqual(r.read_u32(4),0x08000018)
  with self.assertRaises(RomError):relocate_sites(r,'z',[8],0x10,0x18)
 def test_strings(self):
  self.assertEqual(compile_string(b'A\x01','nul'),b'A\x01\0');pool,off=compile_pool([{'text':'A'},{'text':'A'}],True,4);self.assertEqual(off,[0,0])
 def test_branches(self):
  for s,d in [(0x100,0x80),(0x100,0x700)]:self.assertEqual(decode_thumb_b(s,thumb_b(s,d)),d)
  for s,d in [(0x1000,0x100),(0x1000,0x400000)]:self.assertEqual(decode_thumb_bl(s,thumb_bl(s,d)),d)
  for link in (False,True):self.assertEqual(decode_arm_branch(0x1000,arm_branch(0x1000,0x2000,link)),0x2000)
  self.assertEqual(len(thumb_veneer(0x100,0x9000000)),8)
  with self.assertRaises(RomError):thumb_b(0,0x10000)
  with self.assertRaises(RomError):validate_trampoline([0x4800])
 def test_metadata(self):
  h='00'*32;b=serialize(1,'0.1',h,h,h,'1.0');self.assertEqual(parse(b)['schema_version'],1)
  with self.assertRaises(RomError):parse(b[:-1]+bytes([b[-1]^1]))
 def test_bps(self):
  s=b'abcdef';t=b'abXXef-more';p=create(s,t);self.assertEqual(apply(p,s),t)
  with self.assertRaises(BPSError):apply(p,b'xxxxxx')
  with self.assertRaises(BPSError):apply(p[:-1]+bytes([p[-1]^1]),s)
 def test_stale_offset_absent(self):
  self.assertNotIn('0x003A937C',Path('docs/reverse-engineering/unresolved.md').read_text())
  self.assertNotIn('0x003A937C',Path('docs/reverse-engineering/rom-map.md').read_text())
 def test_profiles(self):
  for p in Path('data/build/profiles').glob('*.json'):load(p)
class ModuleFixtureTests(unittest.TestCase):
 def test_hex_fixture_decodes_exact_bytes(self):
  from tools.build.modules import load_raw
  module=load_raw('data/build/fixtures/thumb-return.hex','a7ddd513d149ea16fdd4db3f82267f83087aeaddd06b5dde5468adb704205fc4',encoding='hex')
  self.assertEqual(module['bytes'],bytes.fromhex('00207047'))
 def test_bad_hex_forms_and_hash(self):
  from tools.build.modules import load_raw
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'x.hex'
   path.write_text('xyz0')
   with self.assertRaises(RomError):load_raw(path,encoding='hex')
   path.write_text('123')
   with self.assertRaises(RomError):load_raw(path,encoding='hex')
   path.write_text('00')
   with self.assertRaises(RomError):load_raw(path,'00'*32,encoding='hex')
   with self.assertRaises(RomError):load_raw(path,encoding='base64')
 def test_asset_manifest_hashes_decoded_bytes(self):
  from tools.build.asset_manifest import validate
  manifest=json.loads(Path('data/build/manifests/infrastructure-assets.json').read_text())
  results=validate(manifest)
  fixture=next(x for x in results if x['id']=='thumb-return')
  self.assertEqual(fixture['decoded_sha256'],'a7ddd513d149ea16fdd4db3f82267f83087aeaddd06b5dde5468adb704205fc4')
  self.assertNotEqual(fixture['source_sha256'],fixture['decoded_sha256'])
 def test_no_tracked_binary_fixture(self):
  import subprocess
  tracked=subprocess.check_output(['git','ls-files','data/build/fixtures']).decode().splitlines()
  self.assertFalse(any(path.endswith('.bin') for path in tracked))
if __name__=='__main__':unittest.main()
