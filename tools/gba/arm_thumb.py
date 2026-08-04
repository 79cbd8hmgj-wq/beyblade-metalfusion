"""Small, dependency-free Thumb-1 helpers for auditable address arithmetic."""
def thumb_bl_target(address:int,first:int,second:int)->int:
 if first&0xf800!=0xf000 or second&0xf800!=0xf800: raise ValueError('not a Thumb-1 BL pair')
 hi=first&0x7ff
 if hi&0x400: hi-=0x800
 return ((address+4)+(hi<<12)+((second&0x7ff)<<1))&0xffffffff

def literal_address(instruction_address:int,opcode:int)->int:
 if opcode&0xf800!=0x4800: raise ValueError('not LDR literal')
 return ((instruction_address+4)&~3)+((opcode&0xff)<<2)
