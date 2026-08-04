from .rom_image import RomError
def compile_string(value,mode='nul',width=None,length_bytes=1):
 raw=value if isinstance(value,bytes) else value.encode('ascii','strict')
 if mode=='nul':return raw+b'\0'
 if mode=='fixed':
  if width is None or len(raw)>width:raise RomError('fixed string too long')
  return raw.ljust(width,b'\0')
 if mode=='length':
  if len(raw)>=(1<<(8*length_bytes)):raise RomError('string too long')
  return len(raw).to_bytes(length_bytes,'little')+raw
 raise RomError('unknown string mode')
def compile_pool(entries,deduplicate=False,alignment=1,pad=0xff):
 out=bytearray();offsets=[];seen={}
 for e in entries:
  b=compile_string(e.get('raw',e.get('text','')),e.get('mode','nul'),e.get('width'),e.get('length_bytes',1))
  if deduplicate and b in seen:offsets.append(seen[b]);continue
  while len(out)%alignment:out.append(pad)
  offsets.append(len(out));seen[b]=len(out);out+=b
 return bytes(out),offsets
