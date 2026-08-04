"""Deterministic dependency-ordered first-fit allocator."""
from dataclasses import dataclass,asdict
from .rom_image import RomError,parse_hex
@dataclass(frozen=True)
class Allocation:
 id:str;offset:int;size:int;alignment:int;allocation_class:str;internal:bool=False
 def json(self):
  value=asdict(self);value['offset']=f'0x{self.offset:08x}';value['end']=f'0x{self.offset+self.size:08x}';return value
class Allocator:
 def __init__(self,regions,reservations=(),source_size=0x400000):
  self.source_size=source_size;self.regions=[];self.used=[];self.warnings=[]
  for region in regions:
   start,end=parse_hex(region['start']),parse_hex(region['end']);internal=start<source_size
   if internal:
    if not (region.get('allow_internal') is True and region.get('expected_fill') and region.get('evidence')):raise RomError('internal allocation region is disabled')
    self.warnings.append(f"internal region {region['id']} enabled by evidence {region['evidence']}")
   self.regions.append((start,end,region))
  self.regions.sort(key=lambda x:(x[0],x[1],x[2].get('id','region')))
  for item in sorted(reservations,key=lambda x:x['id']):self.reserve(item['id'],parse_hex(item['start']),parse_hex(item['end'])-parse_hex(item['start']))
 def reserve(self,ident,start,size):self._check_free(start,size);self.used.append((start,start+size,ident))
 def _check_free(self,start,size):
  if size<=0:raise RomError('allocation size must be positive')
  if not any(a<=start and start+size<=b for a,b,_ in self.regions):raise RomError('allocation outside allowed regions')
  if any(start<end and begin<start+size for begin,end,_ in self.used):raise RomError('allocation overlap')
 def allocate(self,spec):
  ident=spec['id'];size=parse_hex(spec['size']);alignment=parse_hex(spec.get('alignment','0x1'))
  if alignment<=0 or alignment&(alignment-1):raise RomError('alignment must be power of two')
  if any(item[2]==ident for item in self.used):raise RomError('duplicate allocation ID')
  fixed=spec.get('fixed_offset');candidates=[]
  for begin,end,_ in self.regions:
   position=parse_hex(fixed) if fixed is not None else (begin+alignment-1)&~(alignment-1)
   while begin<=position and position+size<=end:
    overlap=[(a,z) for a,z,_ in self.used if position<z and a<position+size]
    if not overlap:candidates.append(position);break
    if fixed is not None:break
    position=(max(z for _,z in overlap)+alignment-1)&~(alignment-1)
  if not candidates:raise RomError('no allocation fits')
  start=min(candidates)
  if 'maximum_address' in spec and start+size>parse_hex(spec['maximum_address']):raise RomError('maximum address exceeded')
  if 'proximity_to' in spec and 'branch_reach' in spec and abs(start-parse_hex(spec['proximity_to']))>parse_hex(spec['branch_reach']):raise RomError('branch reach exceeded')
  self._check_free(start,size);self.used.append((start,start+size,ident));internal=start<self.source_size
  if internal:self.warnings.append(f'internal allocation {ident} at 0x{start:08x}')
  return Allocation(ident,start,size,alignment,spec.get('class','data'),internal)
