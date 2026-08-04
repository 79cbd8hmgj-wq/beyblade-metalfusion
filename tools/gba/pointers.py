"""Candidate pointer scans and structural runs."""
from __future__ import annotations
import struct
from collections import Counter
from .address import classify,address_to_offset,offset_to_address
def scan(data:bytes,unaligned=False):
    out=[]; step=1 if unaligned else 4
    for off in range(0,len(data)-3,step):
        value=struct.unpack_from("<I",data,off)[0]; region=classify(value)
        if region in {"Game Pak ROM","EWRAM","IWRAM","VRAM","palette RAM","OAM","Game Pak save memory"}:
            target=None
            if region=="Game Pak ROM":
                target=address_to_offset(value & ~1)
                if target>=len(data):continue
            out.append({"offset":off,"address":offset_to_address(off),"value":value,"target_offset":target,"target_region":region,"thumb":bool(value&1) and region=="Game Pak ROM"})
    return out
def runs(points,min_entries=3):
    ans=[]; cur=[]
    for p in points:
        if not cur or p["offset"]==cur[-1]["offset"]+4:cur.append(p)
        else:
            if len(cur)>=min_entries:ans.append(summarize(cur))
            cur=[p]
    if len(cur)>=min_entries:ans.append(summarize(cur))
    return ans
def summarize(run):
    dist=Counter(p["target_region"] for p in run); targets={(p["target_region"],p["target_offset"] or p["value"]&~1) for p in run}
    return {"start_offset":run[0]["offset"],"end_offset":run[-1]["offset"]+4,"runtime_address":offset_to_address(run[0]["offset"]),"entries":len(run),"stride":4,"alignment":run[0]["offset"]%4,"target_region_distribution":dict(sorted(dist.items())),"valid_targets":len(run),"unique_targets":len(targets),"confidence":"strongly_supported" if len(run)>=8 else "candidate","supporting_evidence":["consecutive aligned pointer-like words"],"counterevidence":["static scan cannot prove table semantics"]}
