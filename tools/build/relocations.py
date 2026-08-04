from .rom_image import RomError,runtime_to_offset,offset_to_runtime
def encode_pointer(target,encoding='rom_pointer'):
 if encoding=='file_offset':return target
 if target&1:raise RomError('unaligned relocation target')
 return offset_to_runtime(target)|(1 if encoding=='thumb_pointer' else 0)
def relocate_sites(image,operation_id,sites,old_target,new_target,encoding='rom_pointer',depends_on=()):
 old=encode_pointer(old_target,encoding);new=encode_pointer(new_target,encoding);out=[]
 for i,site in enumerate(sites):
  if image.read_u32(site)!=old:raise RomError(f'unexpected relocation source at {site:#x}')
  image.write_u32(site,new,f'{operation_id}:{i}',expected=old.to_bytes(4,'little'),depends_on=depends_on)
  out.append({'site':f'0x{site:08x}','old_target':f'0x{old_target:08x}','new_target':f'0x{new_target:08x}','encoding':encoding,'thumb':encoding=='thumb_pointer'})
 return out
def relocate_fixed_table(image,operation_id,old_offset,new_offset,size,sites):
 image.write(new_offset,image.read(old_offset,size),operation_id)
 return relocate_sites(image,operation_id+'-refs',sites,old_offset,new_offset,depends_on=(operation_id,))
