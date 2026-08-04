from .rom_image import RomError
def insert_table(image,operation_id,compiled,mode,source_offset=None,source_size=None,target_offset=None):
 if mode=='validate-only':return False
 if mode=='in-place-same-size':
  if len(compiled)!=source_size:raise RomError('in-place table size changed')
  return image.write(source_offset,compiled,operation_id,expected=image.read(source_offset,source_size))
 if mode=='relocate':return image.write(target_offset,compiled,operation_id)
 raise RomError('unknown table insertion mode')
