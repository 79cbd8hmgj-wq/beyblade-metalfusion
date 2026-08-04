"""Small CFG model used for synthetic and eventually decoded command streams."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Instruction:
    offset:int; size:int; kind:str="raw"; displacement:int|None=None

def signed(value:int,bits:int)->int:
    mask=(1<<bits)-1; value &= mask
    return value-(1<<bits) if value&(1<<(bits-1)) else value

def build_cfg(items:list[Instruction], external_targets:set[int]|None=None)->dict[int,list[int]]:
    external_targets=external_targets or set(); starts={i.offset for i in items}; graph={}
    for i in items:
        edges=[]
        if i.kind in {"branch","conditional"}:
            if i.displacement is None: raise ValueError("branch has no displacement")
            target=i.offset+i.size+i.displacement
            if target not in starts and target not in external_targets: raise ValueError(f"invalid branch target 0x{target:X}")
            edges.append(target)
        if i.kind not in {"branch","end"} and i.offset+i.size in starts: edges.append(i.offset+i.size)
        graph[i.offset]=edges
    return graph
