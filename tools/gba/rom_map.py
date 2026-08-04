"""Deterministic Task 1 analysis driver; never writes the input ROM."""
from __future__ import annotations
import argparse,csv,json,hashlib,shutil,sys
from pathlib import Path
from collections import Counter
from . import header,strings,pointers,compression,regions
SUPPORTED_SHA256="c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"
def hx(v): return f"0x{v:08X}"
def dump(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument("--rom",required=True);p.add_argument("--tracked-output",default="analysis");p.add_argument("--generated-output",default="analysis/generated");p.add_argument("--allow-unsupported-rom",action="store_true");p.add_argument("--clean-generated",action="store_true");a=p.parse_args(argv)
 rp=Path(a.rom); raw=rp.read_bytes(); before=hashlib.sha256(raw).hexdigest()
 if before!=SUPPORTED_SHA256 and not a.allow_unsupported_rom: p.error(f"unsupported ROM SHA-256 {before}; use --allow-unsupported-rom for research")
 out=Path(a.tracked_output); gen=Path(a.generated_output)
 if a.clean_generated and gen.exists(): shutil.rmtree(gen)
 gen.mkdir(parents=True,exist_ok=True)
 print("[1/6] validating header",file=sys.stderr); ident=header.inspect(raw,rp.as_posix());dump(out/"rom-map/rom-identity.json",ident)
 print("[2/6] scanning strings",file=sys.stderr); ss=strings.scan(raw); cs=strings.clusters(ss);dump(gen/"strings/all.json",ss)
 counts=Counter(s["classification"] for s in ss); important=[s for s in ss if s["classification"]!="unknown" or any(x.lower() in s["text"].lower() for x in strings.ANCHORS)]
 dump(out/"strings/summary.json",{"confidence":"confirmed","total_string_count":len(ss),"counts_by_classification":dict(sorted(counts.items())),"referenced_by_pointers":sum(bool(s["pointer_references"]) for s in ss),"duplicate_texts":sum(s["duplicate_count"]>1 for s in ss),"cluster_count":len(cs),"raw_output":"analysis/generated/strings/all.json","regeneration_command":COMMAND})
 dump(out/"strings/classified-important.json",important[:500]);dump(out/"strings/debug-symbols.json",[s for s in ss if s["classification"]=="debug/function identifiers"][:500])
 print("[3/6] scanning pointers",file=sys.stderr); ps=pointers.scan(raw); runs=pointers.runs(ps);dump(gen/"pointers/all.json",ps)
 dump(out/"pointers/summary.json",{"confidence":"confirmed","aligned_candidate_count":len(ps),"run_count":len(runs),"target_regions":dict(Counter(p["target_region"] for p in ps)),"raw_output":"analysis/generated/pointers/all.json"});dump(out/"pointers/pointer-runs.json",runs[:200]);dump(out/"pointers/table-candidates.json",runs[:50])
 print("[4/6] validating compression",file=sys.stderr); comp=compression.scan(raw);dump(gen/"compression/all.json",comp);dump(out/"rom-map/compression-summary.json",{"confidence":"confirmed","validated_count":len(comp),"by_type":dict(Counter(c["type"] for c in comp)),"plausible_header_counts":compression.header_scan(raw),"validation_scope":"LZ77 streams are fully decoded; Huffman, RLE, and differential tags are scanned but remain unvalidated candidates until format-specific bounded parsers accept them.","candidates":comp[:100],"raw_output":"analysis/generated/compression/all.json"})
 sigs=[]
 for name in (b"EEPROM_V",b"SRAM_V",b"FLASH",b"MPlayDef.s",b"Sappy"):
  pos=0
  while (i:=raw.find(name,pos))>=0:sigs.append({"signature":name.decode(),"offset":i,"address":0x08000000+i,"confidence":"confirmed","evidence_type":"direct_binary_evidence"});pos=i+1
 dump(out/"rom-map/library-signatures.json",{"signatures":sigs,"rejected_interpretations":["No audio engine is named solely from instruction/data heuristics."]})
 print("[5/6] classifying regions",file=sys.stderr); rm=regions.coarse_map(raw,ss,ps,comp);free=regions.free_space(raw,ps,comp);dump(out/"rom-map/rom-map.json",{"rom_size":len(raw),"regions":rm});dump(out/"rom-map/region-summary.json",{"counts":dict(Counter(r["classification"] for r in rm)),"confidence":"structural inference; classifications retain per-region confidence"});dump(out/"rom-map/free-space.json",{"internal_candidates":[x for x in free if not x["trailing_padding"]],"trailing_padding":[x for x in free if x["trailing_padding"]],"theoretical_expansion":{"from":len(raw),"to":0x800000,"bytes":0x800000-len(raw),"confidence":"candidate","reasoning":"8 MiB is a conventional power-of-two GBA capacity; compatibility and address references require testing."}});dump(out/"rom-map/asset-region-summary.json",{"validated_compressed_regions":len(comp),"heuristic_asset_classification":"unknown","notes":["Palette/tile/tilemap/audio byte patterns are non-unique and are not assigned semantics without references or runtime evidence."]})
 with (out/"rom-map/rom-map.csv").open("w",newline="") as f:
  w=csv.DictWriter(f,fieldnames=["start_offset","end_offset","start_address","end_address","classification","confidence","evidence"]);w.writeheader();w.writerows({**r,"start_offset":hx(r["start_offset"]),"end_offset":hx(r["end_offset"]),"start_address":hx(r["start_address"]),"end_address":hx(r["end_address"]),"evidence":"; ".join(r["evidence"])} for r in rm)
 after=hashlib.sha256(rp.read_bytes()).hexdigest();
 if after!=before:raise RuntimeError("ROM changed during analysis")
 print(f"[6/6] complete; ROM unchanged: {after}",file=sys.stderr)
COMMAND='python3 -m tools.gba.rom_map --rom "Beyblade G-Revolution (USA).gba" --tracked-output analysis --generated-output analysis/generated --clean-generated'
if __name__=="__main__":main()
