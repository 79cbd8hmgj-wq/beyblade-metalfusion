"""Central publication gate for GBA output and build audit data."""
from hashlib import sha256
from tools.gba.header import LOGO_SHA256
from .bps import apply
from .metadata import parse as parse_metadata
from .rom_image import RomError

def validate_declared_changes(image):
 source=image.source;output=bytes(image.data);actual=[];index=0
 while index<len(source):
  if source[index]==output[index]:index+=1;continue
  start=index
  while index<len(source) and source[index]!=output[index]:index+=1
  actual.append((start,index))
 declared=[(change.offset,change.offset+change.length) for change in image.changes if change.offset<len(source)]
 for start,end in actual:
  if not any(begin<=start and end<=finish for begin,finish in declared):raise RomError(f'undeclared original-ROM change 0x{start:08x}-0x{end:08x}')
 return actual
def validate_output(image,allocations=(),relocations=(),hooks=(),metadata=None,bps=None,require_base_unchanged=False,allow_invalid_header=False):
 data=bytes(image.data);errors=[];header_errors=[]
 if len(data)<0xc0:header_errors.append('ROM shorter than GBA header')
 else:
  if sha256(data[4:0xa0]).hexdigest()!=LOGO_SHA256:header_errors.append('invalid Nintendo logo')
  if data[0xb2]!=0x96:header_errors.append('invalid fixed value')
  if data[0xbd]!=(-sum(data[0xa0:0xbd])-0x19)&0xff:header_errors.append('invalid header complement')
  for name,start,end in [('entry instruction',0,4),('game code',0xac,0xb0),('maker code',0xb0,0xb2)]:
   if data[start:end]!=image.source[start:end]:errors.append(f'source {name} changed')
 if len(data)>0x02000000 or len(data)&(len(data)-1):errors.append('output size is not a valid GBA power of two')
 spans=sorted((a.offset,a.offset+a.size,a.id) for a in allocations)
 for i,(start,end,ident) in enumerate(spans):
  if not 0<=start<end<=len(data):errors.append(f'allocation {ident} out of bounds')
  if i and spans[i-1][1]>start:errors.append(f'allocations {spans[i-1][2]} and {ident} overlap')
 for record in relocations:
  target=int(record['new_target'],16)
  if not 0<=target<len(data):errors.append(f"relocation {record['id']} target out of bounds")
 for record in hooks:
  target=int(record['destination'],16)
  if not 0<=target<len(data):errors.append(f"hook {record['id']} target out of bounds")
 # Expansion bytes not covered by an explicit write must equal the declared fill.
 write_spans=[(change.offset,change.offset+change.length) for change in image.changes]
 if image.expansion_fill is not None:
  for offset,value in enumerate(data[len(image.source):],len(image.source)):
   if value!=image.expansion_fill and not any(start<=offset<end for start,end in write_spans):
    errors.append(f'undeclared expansion byte at 0x{offset:08x}');break
 original_changes=validate_declared_changes(image)
 if require_base_unchanged and data[:len(image.source)]!=image.source:errors.append('profile requires unchanged base ROM')
 if metadata is not None:parse_metadata(metadata)
 if bps is not None and apply(bps,image.source)!=data:errors.append('BPS did not reconstruct output')
 if not image.verify_source_unchanged():errors.append('source path bytes changed')
 if errors or (header_errors and not allow_invalid_header):raise RomError('; '.join(header_errors+errors))
 all_errors=header_errors+errors
 return {'status':'passed' if not all_errors else 'warning','errors':all_errors,'source_integrity':image.verify_source_unchanged(),'header':{'nintendo_logo':not any('Nintendo logo' in x for x in header_errors),'fixed_value':not any('fixed value' in x for x in header_errors),'complement':not any('complement' in x for x in header_errors)},'original_changed_ranges':[[f'0x{s:08x}',f'0x{e:08x}'] for s,e in original_changes],'expansion':{'start':f'0x{len(image.source):08x}','end':f'0x{len(data):08x}','fill_audited':True}}
