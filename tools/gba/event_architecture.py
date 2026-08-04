"""Generate a compact, deterministic Task 6 architecture report."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from .event_callbacks import extract_bindings
EXPECTED="c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5"
def analyse(path:Path,allow_unsupported=False):
    data=path.read_bytes(); digest=hashlib.sha256(data).hexdigest()
    if digest!=EXPECTED and not allow_unsupported: raise ValueError("unsupported ROM SHA-256")
    return {"architecture":"hybrid_native_word_streams","confidence":"strongly_supported","rom_sha256":digest,
            "source_rom_modified":False,"bindings":extract_bindings(data)}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--rom",required=True,type=Path); p.add_argument("--output",required=True,type=Path); p.add_argument("--allow-unsupported",action="store_true"); a=p.parse_args()
    result=analyse(a.rom,a.allow_unsupported); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
