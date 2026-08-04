"""Deterministic byte-range save differ."""
import argparse,json
from pathlib import Path
from .save_format import SaveImage
def diff(before:bytes,after:bytes):
 SaveImage.parse(before);SaveImage.parse(after)
 ranges=[];start=None
 for i,(a,b) in enumerate(zip(before,after)):
  if a!=b and start is None:start=i
  if a==b and start is not None:ranges.append({'offset':start,'length':i-start,'before':before[start:i].hex(),'after':after[start:i].hex()});start=None
 if start is not None:ranges.append({'offset':start,'length':len(before)-start,'before':before[start:].hex(),'after':after[start:].hex()})
 return {'size':len(before),'changed_byte_count':sum(r['length'] for r in ranges),'ranges':ranges}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--after',required=True);p.add_argument('--output',required=True);p.add_argument('--custom-extension',action='store_true');a=p.parse_args();d=diff(Path(a.before).read_bytes(),Path(a.after).read_bytes());
 if a.custom_extension:
  from .custom_save_extension import extension_report
  d['custom_extension']={'before':extension_report(Path(a.before).read_bytes()),'after':extension_report(Path(a.after).read_bytes())}
 Path(a.output).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
