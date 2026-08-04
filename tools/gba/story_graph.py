"""Validation and deterministic JSON for compact evidence graphs."""
import json
def validate_graph(graph:dict)->None:
    ids=[n["id"] for n in graph.get("nodes",[])]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate node")
    known=set(ids)
    for e in graph.get("edges",[]):
        if e["source"] not in known or e["target"] not in known: raise ValueError("edge references missing node")
def deterministic_json(value)->str: return json.dumps(value,indent=2,sort_keys=True)+"\n"
