import hashlib,json,tempfile,unittest
from pathlib import Path
from tools.build.bps import apply
from tools.build.build_rom import build
from tools.build.metadata import parse as parse_metadata
from tools.build.rom_image import SUPPORTED_SHA256
REAL=Path('Beyblade G-Revolution (USA).gba')
class Integration(unittest.TestCase):
 def synthetic_rom(self,path):
  data=bytearray(0x100);data[0xb2]=0x96;data[0xbd]=(-sum(data[0xa0:0xbd])-0x19)&255;path.write_bytes(data);return hashlib.sha256(data).hexdigest()
 def test_two_synthetic_builds_and_source_integrity(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);rom=root/'base.gba';source_hash=self.synthetic_rom(rom);before=rom.read_bytes()
   profile=json.loads(Path('data/build/profiles/infrastructure-smoke.json').read_text());profile['source_rom']={'sha256':source_hash,'size':'0x00000100'};profile['tables']=[];profile['smoke_test']['enabled']=False;profile['validation']['allow_invalid_header']=True;profile['validation']['require_base_unchanged']=True;profile['expansion']['target_size']='0x00000200';profile['allocation_regions']=[{'id':'x','start':'0x00000100','end':'0x00000200'}];profile['expansion']['reservations']=[]
   spec=root/'profile.json';spec.write_text(json.dumps(profile));first=root/'a';second=root/'b';build(rom,spec,first,True,True);build(rom,spec,second,True,True)
   for name in ('spirit-unbound.gba','spirit-unbound.bps','build-manifest.json','allocation-map.json','changed-ranges.json','build-report.md'):self.assertEqual((first/name).read_bytes(),(second/name).read_bytes())
   self.assertEqual(rom.read_bytes(),before);self.assertEqual(hashlib.sha256(rom.read_bytes()).hexdigest(),source_hash)
 def test_builder_executes_text_relocation_hook_and_patch(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);rom=root/'base.gba';source_hash=self.synthetic_rom(rom);raw=bytearray(rom.read_bytes());raw[0x40:0x42]=b'\x00\x00';raw[0x50:0x54]=(0x08000020).to_bytes(4,'little');raw[0x54:0x58]=b'\0'*4;raw[0x60]=0xaa;rom.write_bytes(raw);source_hash=hashlib.sha256(raw).hexdigest()
   profile=json.loads(Path('data/build/profiles/noop.json').read_text());profile['source_rom']={'sha256':source_hash,'size':'0x00000100'};profile['expansion']={'target_size':'0x00000200','fill':'0xff','reservations':[]};profile['allocation_regions']=[{'id':'expansion','start':'0x00000100','end':'0x00000200'}];profile['allocations']=[{'id':'code','size':'0x4','alignment':'0x2','class':'thumb'},{'id':'pool','size':'0x20','alignment':'0x4','class':'data'},{'id':'target','size':'0x4','alignment':'0x4','class':'data'}];profile['texts']=[{'id':'compile-text','kind':'string_pool','allocation':'pool','entries':[{'text':'ABC','mode':'nul'},{'raw_hex':'0102','mode':'fixed','width':'0x4'}],'alignment':'0x4','padding':'0xff','pointer_sites':[{'site':'0x54','expected':'00000000','entry_index':0}]}];profile['relocations']=[{'id':'move-pointer','kind':'pointer_sites','sites':['0x50'],'old_target':'0x20','target_allocation':'target','encoding':'rom_pointer'}];profile['hooks']=[{'id':'redirect','kind':'thumb_b','site':'0x40','expected':'0000','destination_allocation':'code'}];profile['patches']=[{'id':'guarded','kind':'write_u8','offset':'0x60','expected':'aa','value':'0xbb'}];profile['validation']['allow_invalid_header']=True
   spec=root/'profile.json';spec.write_text(json.dumps(profile));manifest=build(rom,spec,root/'out',True,True);output=(root/'out'/'spirit-unbound.gba').read_bytes();alloc={a['id']:int(a['offset'],16) for a in manifest['allocations']}
   self.assertEqual(output[alloc['pool']:alloc['pool']+8],b'ABC\0\x01\x02\0\0');self.assertEqual(int.from_bytes(output[0x50:0x54],'little'),0x08000000+alloc['target']);self.assertEqual(int.from_bytes(output[0x54:0x58],'little'),0x08000000+alloc['pool']);self.assertEqual(output[0x60],0xbb);self.assertEqual(len(manifest['hooks']),1);self.assertEqual(len(manifest['relocations']),1);self.assertEqual(len(manifest['texts']),1)
 @unittest.skipUnless(REAL.exists(),'real ROM not supplied')
 def test_real_profiles(self):
  source=REAL.read_bytes();self.assertEqual(hashlib.sha256(source).hexdigest(),SUPPORTED_SHA256)
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   noop=root/'noop';build(REAL,'data/build/profiles/noop.json',noop,True);self.assertEqual(hashlib.sha256((noop/'spirit-unbound.gba').read_bytes()).hexdigest(),SUPPORTED_SHA256)
   expansion=root/'expansion';build(REAL,'data/build/profiles/expansion-smoke.json',expansion,True);expanded=(expansion/'spirit-unbound.gba').read_bytes();self.assertEqual(len(expanded),0x800000);self.assertEqual(expanded[:0x400000],source);self.assertEqual(expanded[0x400000:],b'\xff'*0x400000)
   smoke=root/'smoke';manifest=build(REAL,'data/build/profiles/infrastructure-smoke.json',smoke,True);output=(smoke/'spirit-unbound.gba').read_bytes();self.assertEqual(output[:0x400000],source)
   metadata=next(a for a in manifest['allocations'] if a['id']=='metadata-block');parse_metadata(output[int(metadata['offset'],16):int(metadata['offset'],16)+144])
   module=next(a for a in manifest['allocations'] if a['id']=='thumb-fixture');self.assertEqual(output[int(module['offset'],16):int(module['offset'],16)+4],bytes.fromhex('00207047'))
   asset=next(a for a in manifest['allocations'] if a['id']=='public-fixture');self.assertEqual(output[int(asset['offset'],16):int(asset['offset'],16)+38],Path('data/build/fixtures/public-domain.txt').read_bytes())
   self.assertEqual(apply((smoke/'spirit-unbound.bps').read_bytes(),source),output);self.assertEqual(len(manifest['tables']),8);self.assertTrue(all(x['byte_identical'] for x in manifest['tables']))
   again=root/'again';build(REAL,'data/build/profiles/infrastructure-smoke.json',again,True)
   for name in ('spirit-unbound.gba','spirit-unbound.bps','build-manifest.json','allocation-map.json','changed-ranges.json','build-report.md'):self.assertEqual((smoke/name).read_bytes(),(again/name).read_bytes())
  self.assertEqual(REAL.read_bytes(),source)
if __name__=='__main__':unittest.main()
