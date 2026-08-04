"""Parse intentionally compact KEY=VALUE GDB observation logs."""
import argparse,json,re
from pathlib import Path
LINE=re.compile(r"^([A-Za-z][A-Za-z0-9_]*)=(0x[0-9A-Fa-f]+|[-+]?[0-9]+)$")
def parse(text:str)->dict:
    observations=[]
    for number,line in enumerate(text.splitlines(),1):
        line=line.strip()
        if not line or line.startswith("#"): continue
        m=LINE.fullmatch(line)
        if not m: raise ValueError(f"line {number}: expected KEY=INTEGER")
        observations.append({"key":m[1],"value":int(m[2],0)})
    return {"format":"battle-gdb-observations-v1","observations":observations}
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(argv); Path(a.output).write_text(json.dumps(parse(Path(a.input).read_text()),indent=2)+"\n")
if __name__=="__main__": main()
