"""Neutral packed-bit addressing; no story meaning is assigned from one bit."""
def bit_location(index:int)->tuple[int,int]:
    if index<0: raise ValueError("negative flag index")
    return index>>3, index&7
def get_flag(data:bytes,index:int)->bool:
    byte,bit=bit_location(index)
    if byte>=len(data): raise IndexError(index)
    return bool(data[byte]&(1<<bit))
def set_flag(data:bytes,index:int,value:bool)->bytes:
    byte,bit=bit_location(index)
    if byte>=len(data): raise IndexError(index)
    out=bytearray(data); out[byte]=(out[byte]|(1<<bit)) if value else (out[byte]&~(1<<bit)); return bytes(out)
