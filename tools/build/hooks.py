"""Instruction-verified ARM/Thumb branch and veneer primitives."""
from .rom_image import RomError
def _signed(v,bits):return v-(1<<bits) if v&(1<<(bits-1)) else v
def thumb_b(src,dst):
 if src&1 or dst&1:raise RomError('Thumb branch alignment')
 displacement=dst-(src+4)
 if displacement%2 or not -2048<=displacement<=2046:raise RomError('Thumb B out of range')
 return (0xe000|((displacement>>1)&0x7ff)).to_bytes(2,'little')
def decode_thumb_b(src,data):return src+4+(_signed(int.from_bytes(data,'little')&0x7ff,11)<<1)
def thumb_bl(src,dst):
 if src&1 or dst&1:raise RomError('Thumb BL alignment')
 displacement=dst-(src+4)
 if displacement%2 or not -(1<<22)<=displacement<=(1<<22)-2:raise RomError('Thumb BL out of range')
 encoded=displacement&0x7fffff;return (0xf000|((encoded>>12)&0x7ff)).to_bytes(2,'little')+(0xf800|((encoded>>1)&0x7ff)).to_bytes(2,'little')
def decode_thumb_bl(src,data):
 high=int.from_bytes(data[:2],'little')&0x7ff;low=int.from_bytes(data[2:],'little')&0x7ff
 return src+4+_signed((high<<12)|(low<<1),23)
def arm_branch(src,dst,link=False):
 if src%4 or dst%4:raise RomError('ARM branch alignment')
 displacement=dst-(src+8)
 if displacement%4 or not -(1<<25)<=displacement<=(1<<25)-4:raise RomError('ARM branch out of range')
 return ((0xeb000000 if link else 0xea000000)|((displacement>>2)&0xffffff)).to_bytes(4,'little')
def decode_arm_branch(src,data):return src+8+(_signed(int.from_bytes(data,'little')&0xffffff,24)<<2)
def thumb_veneer(src,dst):
 """Emit `ldr r3,[pc,#0]; bx r3; .word dst|1` at a word-aligned address."""
 if src%4:raise RomError('Thumb veneer must be word aligned')
 if dst&1:raise RomError('Thumb veneer destination must be even before setting Thumb bit')
 return b'\x00\x4b\x18\x47'+(dst|1).to_bytes(4,'little')
def arm_veneer(src,dst,link=False):
 if link:raise RomError('ARM call veneer is unsupported: return semantics are not verified')
 if src%4 or dst%4:raise RomError('ARM veneer alignment')
 return b'\x04\xf0\x1f\xe5'+dst.to_bytes(4,'little')
def validate_trampoline(insns):
 for halfword in insns:
  if halfword&0xf800 in (0x4800,0xe000,0xf000,0xf800) or halfword in (0x4778,):raise RomError('unsafe PC-relative, branch, literal-load, or mode-changing instruction')
 return True
