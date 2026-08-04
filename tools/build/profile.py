"""Strict runtime validation for dependency-free JSON build profiles."""
import json,re
from hashlib import sha256
from pathlib import Path
from .rom_image import RomError,parse_hex,MAX_SIZE
ID=re.compile(r"^[a-z0-9][a-z0-9-]*$")
TOP={"schema_version","project","profile_id","source_rom","output","expansion","allocation_regions","allocations","assets","tables","texts","modules","patches","relocations","hooks","metadata","validation","smoke_test","extension_metadata"}
HEX_FIELDS={"size","target_size","fill","start","end","alignment","fixed_offset","maximum_address","proximity_to","branch_reach","offset","entry_offset","site","old_target","target_offset","width","length_bytes"}

def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()
def _obj(value,name,allowed,required=()):
 if not isinstance(value,dict):raise RomError(f"{name} must be an object")
 unknown=set(value)-set(allowed)
 if unknown:raise RomError(f"{name} has unknown fields: {','.join(sorted(unknown))}")
 missing=set(required)-set(value)
 if missing:raise RomError(f"{name} missing fields: {','.join(sorted(missing))}")
def _id(value,name):
 if not isinstance(value,str) or not ID.fullmatch(value):raise RomError(f"{name} must be a stable lowercase ID")
def _hex_fields(obj):
 for key,value in obj.items():
  if key in HEX_FIELDS:parse_hex(value,name=key)
def _deps(items,all_ids):
 graph={x['id']:x.get('depends_on',[]) for x in items};state={}
 for ident,deps in graph.items():
  if not isinstance(deps,list) or any(not isinstance(d,str) for d in deps):raise RomError(f"{ident}.depends_on must be a string array")
  for dep in deps:
   if dep not in all_ids:raise RomError(f"unknown dependency {dep}")
 def visit(n):
  if state.get(n)==1:raise RomError("dependency cycle")
  if state.get(n)==2:return
  state[n]=1
  for d in graph.get(n,[]):visit(d)
  state[n]=2
 for n in sorted(graph):visit(n)
def ordered(items,completed=()):
 remaining={x['id']:x for x in items};done=set(completed);result=[]
 while remaining:
  ready=sorted(k for k,v in remaining.items() if set(v.get('depends_on',()))<=done)
  if not ready:raise RomError('dependency cycle')
  for k in ready:result.append(remaining.pop(k));done.add(k)
 return result

def validate(p):
 _obj(p,'profile',TOP,TOP-{'allocations','extension_metadata'}); _id(p['profile_id'],'profile_id')
 if p['schema_version']!=1 or not isinstance(p['project'],str):raise RomError('unsupported schema/project')
 _obj(p['source_rom'],'source_rom',{'sha256','size'},{'sha256','size'});parse_hex(p['source_rom']['size']);
 if not re.fullmatch(r'[0-9a-f]{64}',p['source_rom']['sha256']):raise RomError('source SHA-256 must be lowercase hexadecimal')
 _obj(p['output'],'output',{'rom_name','bps_name'},{'rom_name','bps_name'})
 for k,suffix in [('rom_name','.gba'),('bps_name','.bps')]:
  value=p['output'][k]
  if not isinstance(value,str) or Path(value).name!=value or not value.endswith(suffix):raise RomError(f'invalid {k}')
 _obj(p['expansion'],'expansion',{'target_size','fill','reservations'},{'target_size','fill','reservations'});_hex_fields(p['expansion'])
 target=parse_hex(p['expansion']['target_size']);source_size=parse_hex(p['source_rom']['size'])
 if target<source_size or target>MAX_SIZE or target&(target-1):raise RomError('invalid expansion target')
 fill=parse_hex(p['expansion']['fill']);
 if fill>0xff:raise RomError('expansion fill must be one byte')
 region_ids=set()
 for i,r in enumerate(p['allocation_regions']):
  _obj(r,f'region[{i}]',{'id','start','end','allow_internal','expected_fill','evidence','extension_metadata'},{'id','start','end'});_id(r['id'],'region ID');_hex_fields(r)
  if r['id'] in region_ids: raise RomError('duplicate region ID')
  region_ids.add(r['id'])
  start,end=parse_hex(r['start']),parse_hex(r['end'])
  if not 0<=start<end<=target:raise RomError('invalid allocation region bounds')
  if start<source_size and not (r.get('allow_internal') is True and isinstance(r.get('expected_fill'),str) and isinstance(r.get('evidence'),str) and r['evidence']):raise RomError('internal region requires allow_internal, expected_fill, and evidence')
 for r in p['expansion']['reservations']:
  _obj(r,'reservation',{'id','start','end'},{'id','start','end'});_id(r['id'],'reservation ID');_hex_fields(r)
 allocations=p.get('allocations',[]);allocation_ids=set()
 for a in allocations:
  _obj(a,'allocation',{'id','size','alignment','class','depends_on','fixed_offset','maximum_address','proximity_to','branch_reach','group','extension_metadata'},{'id','size','alignment','class'});_id(a['id'],'allocation ID');_hex_fields(a)
  if a['id'] in allocation_ids: raise RomError('duplicate allocation ID')
  allocation_ids.add(a['id'])
  if a['class'] not in ('data','arm','thumb'):raise RomError('invalid allocation class')
 sections=[]
 specs={
 'assets':({'id','allocation','path','sha256','encoding','depends_on','extension_metadata'},{'id','allocation','path','sha256'}),
 'modules':({'id','allocation','path','sha256','encoding','entry_offset','thumb','depends_on','extension_metadata'},{'id','allocation','path','sha256'}),
 'tables':({'id','kind','mode','category','offset','size','field_count','allocation','reference_sites','depends_on','extension_metadata'},{'id','kind','mode'}),
 'texts':({'id','kind','allocation','entries','deduplicate','alignment','padding','pointer_sites','depends_on','extension_metadata'},{'id','kind','allocation','entries'}),
 'patches':({'id','kind','offset','expected','data','value','target_allocation','thumb','depends_on','extension_metadata'},{'id','kind','offset','expected'}),
 'relocations':({'id','kind','sites','old_target','target_allocation','target_offset','encoding','depends_on','extension_metadata'},{'id','kind','sites','old_target','encoding'}),
 'hooks':({'id','kind','site','expected','destination_allocation','destination_offset','veneer_allocation','depends_on','extension_metadata'},{'id','kind','site','expected','destination_allocation'}),}
 known_kinds={'tables':{'beyblade','component_names','presentation_pairs','event_named_record','event_word_stream','event_bindings'},'texts':{'string_pool'},'patches':{'write_bytes','replace_exact','fill','write_u8','write_u16','write_u32','write_rom_pointer','write_thumb_pointer'},'relocations':{'pointer_sites','fixed_table'},'hooks':{'thumb_b','thumb_bl','arm_b','arm_bl'},'assets':set(),'modules':set()}
 op_ids=set()
 for section,(allowed,required) in specs.items():
  if not isinstance(p[section],list):raise RomError(f'{section} must be an array')
  for op in p[section]:
   _obj(op,section,allowed,required);_id(op['id'],'operation ID');_hex_fields(op)
   if op['id'] in op_ids: raise RomError('duplicate operation ID')
   op_ids.add(op['id']); sections.append(op)
   if section in ('assets','modules','texts') and op['allocation'] not in allocation_ids:raise RomError(f"{op['id']} references unknown allocation")
   if section in ('assets','modules'):
    if op.get('encoding','raw') not in ('raw','hex'):raise RomError('unsupported tracked resource encoding')
    if not isinstance(op['path'],str) or Path(op['path']).is_absolute() or '..' in Path(op['path']).parts:raise RomError('resource path must be repository-relative')
    if not re.fullmatch(r'[0-9a-f]{64}',op['sha256']):raise RomError('resource SHA-256 must be lowercase hexadecimal')
   if section=='texts':
    if not isinstance(op['entries'],list):raise RomError('text entries must be an array')
    for entry in op['entries']:
     _obj(entry,'text entry',{'text','raw_hex','mode','width','length_bytes','extension_metadata'},())
     if ('text' in entry)==('raw_hex' in entry):raise RomError('text entry requires exactly one of text/raw_hex')
     if entry.get('mode','nul') not in ('nul','fixed','length'):raise RomError('unsupported text field mode')
     _hex_fields(entry)
    for row in op.get('pointer_sites',[]):
     _obj(row,'text pointer row',{'site','expected','entry_index'},{'site','expected','entry_index'});parse_hex(row['site']);
     if not isinstance(row['entry_index'],int) or not 0<=row['entry_index']<len(op['entries']):raise RomError('text pointer entry index out of range')
   if section=='patches' and op.get('target_allocation') and op['target_allocation'] not in allocation_ids:raise RomError('patch references unknown allocation')
   if section=='relocations':
    if op.get('encoding') not in ('rom_pointer','thumb_pointer','file_offset'):raise RomError('unknown relocation encoding')
    if op.get('kind')=='pointer_sites' and op.get('target_allocation') not in allocation_ids:raise RomError('relocation references unknown allocation')
    if not isinstance(op.get('sites'),list) or not op['sites']:raise RomError('relocation requires explicit sites')
    for site in op['sites']:parse_hex(site)
   if section=='hooks':
    if op['destination_allocation'] not in allocation_ids:raise RomError('hook references unknown allocation')
    if op.get('veneer_allocation') and op['veneer_allocation'] not in allocation_ids:raise RomError('hook veneer references unknown allocation')
   if section in ('tables','texts','patches','relocations','hooks') and op.get('kind') not in known_kinds[section]:raise RomError(f"unknown {section} operation kind")
 _deps(allocations,allocation_ids);_deps(sections,op_ids|allocation_ids)
 _obj(p['metadata'],'metadata',{'enabled','id','allocation','project_version','extension_metadata'},{'enabled'})
 if p['metadata']['enabled']:
  _id(p['metadata'].get('id'),'metadata ID')
  if p['metadata'].get('allocation') not in allocation_ids:raise RomError('metadata references unknown allocation')
 _obj(p['validation'],'validation',{'allow_invalid_header','require_base_unchanged','extension_metadata'},{'allow_invalid_header'})
 _obj(p['smoke_test'],'smoke_test',{'enabled','mgba','gdb','port','timeout','extension_metadata'},{'enabled'})
 return p

def load(path):
 with open(path,encoding='utf8') as handle:return validate(json.load(handle))
def profile_hash(profile):return sha256(canonical(profile)).hexdigest()
