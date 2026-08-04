def linker_script(address):
 return f'''OUTPUT_ARCH(arm)\nSECTIONS {{\n . = 0x{address:08x};\n .text : {{ *(.text*) }}\n .rodata : {{ *(.rodata*) }}\n .data : {{ *(.data*) }}\n .bss : {{ *(.bss*) }}\n /DISCARD/ : {{ *(.comment) *(.note*) }}\n}}\n'''
def parse_map(text):
 out={}
 for line in text.splitlines():
  p=line.split()
  if len(p)>=2 and p[0].startswith('0x'):
   try:out[p[-1]]=int(p[0],16)
   except ValueError:pass
 return out
