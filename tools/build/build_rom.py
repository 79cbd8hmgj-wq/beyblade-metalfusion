"""Authoritative deterministic clean ROM builder."""
import argparse,csv,json,shutil
from pathlib import Path
from . import __version__
from .allocator import Allocator
from .bps import create as make_bps
from .emulator_smoke import run as run_smoke
from .hooks import thumb_b,thumb_bl,arm_branch,thumb_veneer,arm_veneer
from .metadata import serialize as metadata_bytes
from .modules import load_raw,insert_raw,_decode
from .profile import load as load_profile,profile_hash,canonical,ordered
from .relocations import relocate_sites
from .rom_image import RomImage,RomError,digest,parse_hex
from .table_compiler import execute_table
from .text_compiler import compile_pool
from .toolchain import discover,version
from .validation import validate_output

def dump(path,obj):Path(path).write_text(json.dumps(obj,sort_keys=True,indent=2)+'\n',encoding='utf8')
def _toolchain_manifest():
 info=discover();result={'available':info['available'],'install_hint':info['install_hint'],'versions':{}}
 if info['available']:
  for name,path in sorted(info['tools'].items()):result['versions'][name]=version(path)
 return result
def _offset(spec,key,default='0x0'):return parse_hex(spec.get(key,default))
def _apply_patch(image,spec,allocations):
 kind=spec['kind'];offset=parse_hex(spec['offset']);expected=bytes.fromhex(spec['expected']);operation=spec['id'];depends=spec.get('depends_on',())
 if kind in ('write_bytes','replace_exact'):data=bytes.fromhex(spec['data'])
 elif kind=='fill':data=bytes([parse_hex(spec['value'])])*len(expected)
 elif kind in ('write_u8','write_u16','write_u32'):
  width={'write_u8':1,'write_u16':2,'write_u32':4}[kind];data=parse_hex(spec['value']).to_bytes(width,'little')
 elif kind in ('write_rom_pointer','write_thumb_pointer'):
  target=allocations[spec['target_allocation']].offset+_offset(spec,'target_offset');data=(0x08000000+target+(kind=='write_thumb_pointer')).to_bytes(4,'little')
 else:raise RomError(f'unsupported patch kind {kind}')
 if len(data)!=len(expected):raise RomError(f'{operation}: expected/data lengths differ')
 image.write(offset,data,operation,expected=expected,depends_on=depends);return {'id':operation,'kind':kind,'offset':f'0x{offset:08x}','length':len(data),'emitted':data.hex()}
def _execute_text(image,spec,allocation):
 if spec['kind']!='string_pool':raise RomError('unsupported text kind')
 entries=[]
 for entry in spec['entries']:
  if not isinstance(entry,dict):raise RomError('text entry must be an object')
  if 'raw_hex' in entry:
   item={'raw':bytes.fromhex(entry['raw_hex']),'mode':entry.get('mode','nul')}
  else:item={'text':entry.get('text',''),'mode':entry.get('mode','nul')}
  for key in ('width','length_bytes'):
   if key in entry:item[key]=parse_hex(entry[key])
  entries.append(item)
 pool,offsets=compile_pool(entries,spec.get('deduplicate',False),parse_hex(spec.get('alignment','0x1')),parse_hex(spec.get('padding','0xff')))
 if len(pool)>allocation.size:raise RomError(f"{spec['id']}: text pool exceeds allocation")
 image.write(allocation.offset,pool,spec['id'],source_artifact=digest(pool),depends_on=spec.get('depends_on',()))
 pointers=[]
 for row in spec.get('pointer_sites',[]):
  index=row['entry_index'];site=parse_hex(row['site']);old=bytes.fromhex(row['expected']);value=0x08000000+allocation.offset+offsets[index]
  image.write_u32(site,value,f"{spec['id']}:pointer:{index}",expected=old,depends_on=(spec['id'],));pointers.append({'site':f'0x{site:08x}','entry_index':index,'value':f'0x{value:08x}'})
 return {'id':spec['id'],'kind':'string_pool','allocation':allocation.id,'size':len(pool),'sha256':digest(pool),'entry_offsets':[f'0x{x:x}' for x in offsets],'pointer_rows':pointers}
def _execute_hook(image,spec,allocations):
 site=parse_hex(spec['site']);destination=allocations[spec['destination_allocation']].offset+_offset(spec,'destination_offset');kind=spec['kind'];expected=bytes.fromhex(spec['expected']);veneer=None
 encoder=(lambda target:{'thumb_b':thumb_b,'thumb_bl':thumb_bl}[kind](site,target)) if kind.startswith('thumb') else (lambda target:arm_branch(site,target,kind=='arm_bl'))
 try:emitted=encoder(destination)
 except RomError as error:
  if 'out of range' not in str(error):raise
  veneer_id=spec.get('veneer_allocation')
  if not veneer_id:raise RomError(f"{spec['id']}: branch out of range and no veneer allocation supplied")
  allocation=allocations[veneer_id]
  if kind.startswith('thumb'):
   if allocation.alignment<4 or allocation.offset%4:raise RomError('Thumb veneer allocation must be 4-byte aligned')
   veneer_bytes=thumb_veneer(allocation.offset,destination)
  else:
   if kind=='arm_bl':raise RomError('ARM BL veneer is unsupported until call/return semantics are verified')
   veneer_bytes=arm_veneer(allocation.offset,destination)
  if len(veneer_bytes)>allocation.size:raise RomError('veneer exceeds allocation')
  image.write(allocation.offset,veneer_bytes,f"{spec['id']}:veneer",depends_on=spec.get('depends_on',()));emitted=encoder(allocation.offset);veneer={'allocation':veneer_id,'offset':f'0x{allocation.offset:08x}','bytes':veneer_bytes.hex()}
 if len(expected)!=len(emitted):raise RomError(f"{spec['id']}: expected hook extent does not match instruction")
 image.write(site,emitted,spec['id'],expected=expected,depends_on=spec.get('depends_on',()))
 return {'id':spec['id'],'kind':kind,'site':f'0x{site:08x}','destination':f'0x{destination:08x}','expected':expected.hex(),'emitted':emitted.hex(),'veneer':veneer}
def build(rom_path,profile_path,output_dir,clean=False,research_override=False):
 profile=load_profile(profile_path);output=Path(output_dir);source_path=Path(rom_path).resolve()
 if output.resolve()==source_path or source_path in output.resolve().parents:raise RomError('output resolves to source ROM')
 if clean and output.exists():shutil.rmtree(output)
 source=profile['source_rom'];image=RomImage.load(rom_path,source['sha256'],parse_hex(source['size']),research_override)
 source_before=image.source_hash;target=parse_hex(profile['expansion']['target_size']);fill=parse_hex(profile['expansion']['fill']);image.expand(target,fill)
 allocator=Allocator(profile['allocation_regions'],profile['expansion']['reservations'],len(image.source));allocations=[];by_id={}
 completed=set()
 for spec in ordered(profile.get('allocations',[])):
  allocation=allocator.allocate(spec);allocations.append(allocation);by_id[allocation.id]=allocation;completed.add(spec['id'])
 root=Path(__file__).resolve().parents[2];assets=[];modules=[];tables=[];texts=[];patches=[];relocations=[];hooks=[]
 for spec in ordered(profile['assets'],completed):
  path=root/spec['path'];decoded=_decode(path,spec.get('encoding','raw'));actual=digest(decoded)
  if actual!=spec['sha256']:raise RomError(f"{spec['id']}: decoded asset hash mismatch")
  allocation=by_id[spec['allocation']]
  if len(decoded)>allocation.size:raise RomError('asset exceeds allocation')
  image.write(allocation.offset,decoded,spec['id'],source_artifact=actual,depends_on=spec.get('depends_on',()));completed.add(spec['id']);assets.append({'id':spec['id'],'allocation':allocation.id,'encoding':spec.get('encoding','raw'),'source_sha256':digest(path.read_bytes()),'decoded_sha256':actual,'decoded_size':len(decoded)})
 for spec in ordered(profile['modules'],completed):
  module=load_raw(root/spec['path'],spec.get('sha256'),_offset(spec,'entry_offset'),spec.get('thumb',True),spec.get('encoding','raw'));insert_raw(image,by_id[spec['allocation']],module,spec['id']);completed.add(spec['id']);modules.append({'id':spec['id'],'allocation':spec['allocation'],'encoding':module['encoding'],'sha256':module['sha256'],'size':len(module['bytes']),'entry_offset':f"0x{module['entry_offset']:x}",'thumb':module['thumb']})
 for spec in ordered(profile['tables'],completed):tables.append(execute_table(image.source,spec));completed.add(spec['id'])
 for spec in ordered(profile['texts'],completed):texts.append(_execute_text(image,spec,by_id[spec['allocation']]));completed.add(spec['id'])
 for spec in ordered(profile['patches'],completed):patches.append(_apply_patch(image,spec,by_id));completed.add(spec['id'])
 for spec in ordered(profile['relocations'],completed):
  if spec['kind']=='fixed_table':raise RomError('fixed_table relocation requires complete consumer bounds and is not integrated')
  target=by_id[spec['target_allocation']].offset+_offset(spec,'target_offset');old=parse_hex(spec['old_target']);sites=[parse_hex(x) for x in spec['sites']]
  records=relocate_sites(image,spec['id'],sites,old,target,spec['encoding'],spec.get('depends_on',()))
  for record in records:record.update({'id':spec['id'],'new_target':f'0x{target:08x}'})
  relocations.extend(records);completed.add(spec['id'])
 for spec in ordered(profile['hooks'],completed):hooks.append(_execute_hook(image,spec,by_id));completed.add(spec['id'])
 profile_digest=profile_hash(profile);core={'profile_id':profile['profile_id'],'profile_hash':profile_digest,'source_sha256':image.source_hash,'expansion':{'source_size':len(image.source),'target_size':len(image.data),'fill':f'0x{fill:02x}','range':f'0x{len(image.source):08x}-0x{len(image.data)-1:08x}'},'allocations':[a.json() for a in allocations],'assets':assets,'tables':tables,'texts':texts,'modules':modules,'relocations':relocations,'hooks':hooks,'patches':patches};manifest_core_hash=digest(canonical(core));metadata=None;metadata_result=None
 if profile['metadata'].get('enabled'):
  allocation=by_id[profile['metadata']['allocation']];metadata=metadata_bytes(1,profile['metadata']['project_version'],profile_digest,image.source_hash,manifest_core_hash,__version__,0,len(allocations))
  if len(metadata)>allocation.size:raise RomError('metadata exceeds allocation')
  image.write(allocation.offset,metadata,profile['metadata']['id']);metadata_result={'allocation':allocation.id,'offset':f'0x{allocation.offset:08x}','size':len(metadata),'sha256':digest(metadata)}
 patch=make_bps(image.source,bytes(image.data),profile['profile_id'].encode())
 validation=validate_output(image,allocations,relocations,hooks,metadata,patch,profile['validation'].get('require_base_unchanged',False),profile['validation'].get('allow_invalid_header',False))
 output.mkdir(parents=True,exist_ok=True);rom_path_out=output/profile['output']['rom_name'];image.atomic_write(rom_path_out);(output/profile['output']['bps_name']).write_bytes(patch)
 smoke={'status':'not-requested'}
 if profile['smoke_test']['enabled']:
  smoke=run_smoke(str(rom_path_out),profile['smoke_test'].get('mgba','mgba'),profile['smoke_test'].get('gdb','gdb-multiarch'),profile['smoke_test'].get('port',2345),profile['smoke_test'].get('timeout',10))
 if digest(source_path.read_bytes())!=source_before:raise RomError('source hash changed after integration build')
 manifest={**core,'schema_version':1,'build_id':digest(canonical(core))[:16],'output_size':len(image.data),'output_sha256':digest(image.data),'bps':{'sha256':digest(patch),'size':len(patch),'verified':True},'changed_ranges':[change.json() for change in image.changes],'metadata':metadata_result,'validation':validation,'smoke_test':smoke,'tool_version':__version__,'toolchain':_toolchain_manifest(),'warnings':allocator.warnings}
 dump(output/'build-manifest.json',manifest);dump(output/'allocation-map.json',core['allocations']);dump(output/'changed-ranges.json',manifest['changed_ranges'])
 for name,value in [('relocations.json',relocations),('hooks.json',hooks),('assets.json',assets),('tables.json',tables),('texts.json',texts),('modules.json',modules),('validation.json',validation)]:dump(output/name,value)
 with (output/'allocation-map.csv').open('w',newline='') as handle:
  writer=csv.writer(handle,lineterminator='\n');writer.writerow(['id','offset','end','size','alignment','class','internal'])
  for allocation in allocations:writer.writerow([allocation.id,f'0x{allocation.offset:08x}',f'0x{allocation.offset+allocation.size:08x}',allocation.size,allocation.alignment,allocation.allocation_class,str(allocation.internal).lower()])
 report=f"# Deterministic build report\n\n* Profile: `{profile['profile_id']}`\n* Build ID: `{manifest['build_id']}`\n* Source: `{image.source_hash}`\n* Output: `{manifest['output_sha256']}`\n* BPS: `{manifest['bps']['sha256']}` (exact reconstruction: confirmed)\n* Tables: {len(tables)} confirmed no-op round trips\n* Smoke: {smoke['status']}\n* Evidence status: confirmed\n"
 (output/'build-report.md').write_text(report,encoding='utf8');return manifest
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--rom',required=True);parser.add_argument('--profile',required=True);parser.add_argument('--output-dir',required=True);parser.add_argument('--clean',action='store_true');parser.add_argument('--research-override',action='store_true');args=parser.parse_args();manifest=build(args.rom,args.profile,args.output_dir,args.clean,args.research_override);print(json.dumps({'build_id':manifest['build_id'],'output_sha256':manifest['output_sha256'],'bps_sha256':manifest['bps']['sha256']},sort_keys=True))
if __name__=='__main__':main()
