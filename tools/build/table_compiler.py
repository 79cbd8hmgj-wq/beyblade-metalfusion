"""Build-facing lossless adapters for confirmed retail serializers."""
from .rom_image import RomError,parse_hex,digest

def compile_records(records,serializer,expected_count=None):
 if expected_count is not None and len(records)!=expected_count:raise RomError('table count change requires complete consumer bounds')
 return b''.join(serializer(record) for record in records)
def validate_noop(original,compiled):
 if bytes(original)!=bytes(compiled):raise RomError('table no-op round trip changed bytes')
 return {'status':'confirmed','size':len(original),'byte_identical':True,'sha256':digest(original)}
def execute_table(rom,spec):
 kind=spec['kind'];mode=spec['mode']
 if mode!='validate-only':raise RomError(f"{spec['id']}: only validate-only is integrated for confirmed retail tables")
 if kind=='beyblade':
  from tools.gba.beyblade_table import extract_records,serialize_record,TABLE_OFFSET,TABLE_END
  compiled=b''.join(serialize_record(x) for x in extract_records(rom));start,end=TABLE_OFFSET,TABLE_END
 elif kind=='component_names':
  from tools.gba.component_tables import extract_category,serialize_pointer_arrays,CATEGORY_BY_SLUG
  category=spec.get('category');table=CATEGORY_BY_SLUG.get(category)
  if table is None:raise RomError('unknown component category')
  start,end=table.offset,table.end;compiled=serialize_pointer_arrays(extract_category(rom,category))
 elif kind=='presentation_pairs':
  from tools.gba.move_tables import extract_pairs,serialize_pairs,PAIR_OFFSET,END
  start,end=PAIR_OFFSET,END;compiled=serialize_pairs(extract_pairs(rom))
 elif kind=='event_bindings':
  import struct
  from tools.gba.event_callbacks import extract_bindings
  bindings=extract_bindings(rom)
  if not bindings:raise RomError('no confirmed event bindings found')
  for binding in bindings:
   offset=int(binding['binding_offset'],16);original=rom[offset:offset+8];values=struct.unpack('<II',original);compiled=struct.pack('<II',*values)
   validate_noop(original,compiled)
  combined=b''.join(rom[int(x['binding_offset'],16):int(x['binding_offset'],16)+8] for x in bindings)
  return {'id':spec['id'],'kind':kind,'mode':mode,'status':'confirmed','record_count':len(bindings),'size':len(combined),'byte_identical':True,'sha256':digest(combined),'offsets':[x['binding_offset'].lower() for x in bindings]}
 elif kind=='event_named_record':
  from tools.gba.event_records import InlineNamedRecord
  start=parse_hex(spec['offset']);record=InlineNamedRecord.parse(rom,start,int(spec.get('field_count',3)));compiled=record.to_bytes();end=start+len(compiled)
 elif kind=='event_word_stream':
  from tools.gba.event_records import decode_words,encode_words
  start=parse_hex(spec['offset']);size=parse_hex(spec['size']);end=start+size;compiled=encode_words(decode_words(rom,start,size))
 else:raise RomError('unsupported table kind')
 result=validate_noop(rom[start:end],compiled);return {'id':spec['id'],'kind':kind,'mode':mode,'offset':f'0x{start:08x}',**result}
