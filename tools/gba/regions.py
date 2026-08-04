"""Coarse, evidence-led region and fill-run classification."""
from __future__ import annotations
from collections import Counter
from .address import offset_to_address
def fill_runs(data,min_length=64):
    out=[]; start=0
    for i in range(1,len(data)+1):
        if i==len(data) or data[i]!=data[start]:
            if i-start>=min_length and data[start] in (0,255):out.append((start,i,data[start]))
            start=i
    return out
def coarse_map(data,strings,pointers,compressed,block=0x10000):
    rows=[{"start_offset":0,"end_offset":0xC0,"start_address":offset_to_address(0),"end_address":offset_to_address(0xC0),"classification":"header","confidence":"confirmed","evidence":["validated GBA header"]}]
    fills=fill_runs(data)
    for start in range(0xC0,len(data),block):
        end=min(len(data),start+block); seg=data[start:end]
        ns=sum(start<=s["offset"]<end for s in strings); np=sum(start<=p["offset"]<end for p in pointers); nc=sum(start<=c["offset"]<end for c in compressed)
        fill=max(Counter(seg).values())/len(seg); ent=__import__('tools.gba.compression',fromlist=['entropy']).entropy(seg)
        if fill>.98: kind,conf="padding","strongly_supported"
        elif nc: kind,conf="compressed data candidate","strongly_supported"
        elif ns>=20:kind,conf="string pool","strongly_supported"
        elif np>=100:kind,conf="mixed code/literal pool","candidate"
        else:kind,conf="unknown","unknown"
        rows.append({"start_offset":start,"end_offset":end,"start_address":offset_to_address(start),"end_address":offset_to_address(end) if end<0x2000000 else 0x0a000000,"classification":kind,"confidence":conf,"evidence":[f"strings={ns}",f"pointers={np}",f"validated_compression={nc}",f"entropy={ent:.3f}",f"dominant_byte_fraction={fill:.3f}"]})
    return rows
def free_space(data,pointers,compressed,min_length=256):
    result=[]
    for a,b,byte in fill_runs(data,min_length):
        refs=sum(p.get("target_offset") is not None and a<=p["target_offset"]<b for p in pointers)
        overlap=any(a<c["offset"]+c["compressed_length"] and c["offset"]<b for c in compressed)
        trailing=b==len(data); confidence="likely_safe" if trailing and not refs and not overlap else "questionable"
        result.append({"start_offset":a,"end_offset":b,"start_address":offset_to_address(a),"end_address":offset_to_address(b) if b<0x2000000 else 0x0a000000,"length":b-a,"fill_byte":f"0x{byte:02X}","alignment":a%4,"direct_pointer_references":refs,"branch_targets":"not exhaustively detected","compressed_overlap":overlap,"trailing_padding":trailing,"confidence":confidence,"reasoning":"Trailing uniform fill with no direct aligned pointer or validated compression overlap." if confidence=="likely_safe" else "Uniform fill alone does not establish safety; dynamic branch/reference analysis remains incomplete."})
    return result
