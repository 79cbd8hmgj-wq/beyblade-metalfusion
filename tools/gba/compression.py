"""Bounded validators for common BIOS compression headers."""
from __future__ import annotations
import math
from collections import Counter
def entropy(b):
    if not b:return 0.0
    from collections import Counter
    return -sum((n/len(b))*math.log2(n/len(b)) for n in Counter(b).values())
def lz77(data,off,max_output=0x800000):
    if off+4>len(data) or data[off]!=0x10:return None
    size=int.from_bytes(data[off+1:off+4],"little")
    # Tiny sizes overwhelmingly arise by chance in code/literals and are not
    # credible standalone BIOS streams without an external reference.
    if not 32<=size<=max_output:return None
    src=off+4; out=bytearray()
    try:
      while len(out)<size:
        flags=data[src];src+=1
        for bit in range(8):
          if len(out)>=size:break
          if flags&(0x80>>bit):
            x=(data[src]<<8)|data[src+1];src+=2; length=(x>>12)+3; disp=(x&0xfff)+1
            if disp>len(out):return None
            for _ in range(length):
              if len(out)>=size:break
              out.append(out[-disp])
          else:out.append(data[src]);src+=1
    except IndexError:return None
    return {"offset":off,"type":"LZ77 0x10","decompressed_size":size,"compressed_length":src-off,"entropy":round(entropy(data[off:src]),4),"alignment":off%4,"confidence":"confirmed"}
def scan(data):
    return [x for i,b in enumerate(data) if b==0x10 and (x:=lz77(data,i))]
def header_scan(data, max_output=0x800000):
    """Count plausible headers for every BIOS family without trusting the tag."""
    names={0x10:"LZ77 0x10",0x20:"Huffman 0x20",0x30:"RLE 0x30",0x80:"differential/filter 0x80"}; out=Counter()
    for i in range(len(data)-4):
        tag=data[i]&0xF0
        if tag not in names:continue
        size=int.from_bytes(data[i+1:i+4],"little")
        if 32<=size<=max_output:out[names[tag]]+=1
    return dict(sorted(out.items()))
