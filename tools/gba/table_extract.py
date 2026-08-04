"""Deterministic Task 2 Beyblade table extractor; never writes a ROM."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from .beyblade_table import *
SUPPORTED_SHA256='c4a568adc896bace0e25dbff4aa0c1802933c88e3f4a4e825075116c8c4173e5'

def validate_rom(data:bytes,allow_unsupported=False):
    digest=hashlib.sha256(data).hexdigest()
    if digest!=SUPPORTED_SHA256 and not allow_unsupported:
        raise ValueError(f"unsupported ROM SHA-256 {digest}; expected {SUPPORTED_SHA256}")
    return digest

def record_dict(r,rom):
    names=[read_c_string(rom,p) for p in r.name_pointers]
    return {'index':r.index,'source_offset':f'0x{r.source_offset:08X}','runtime_address':f'0x{r.runtime_address:08X}',
      'display_names':dict(zip(LANGUAGES,names)),'name_pointers':[f'0x{x:08X}' for x in r.name_pointers],
      'field_14_ptr':f'0x{r.field_14_ptr:08X}','field_18_ptr':f'0x{r.field_18_ptr:08X}',
      'field_1c_bytes':r.field_1c_bytes.hex(),'field_20_bytes':r.field_20_bytes.hex(),
      'field_24_u8':r.field_24_u8,'season':r.season,'field_26_u16':r.field_26_u16,
      'raw_record_hex':r.raw.hex(),'confidence':{'structure':'confirmed','season':'strongly_supported','unknown_fields':'unknown'},
      'evidence':['getBeyBladeWithIndex at ROM 0x0003DCFC multiplies index by 40 and adds 0x0807A1F4']}
def validate_record_document(doc:dict):
    required={"index","source_offset","runtime_address","display_names","name_pointers","raw_record_hex","confidence","evidence"}
    missing=required-doc.keys()
    if missing: raise ValueError(f"record violates schema; missing {sorted(missing)}")
    if len(doc["name_pointers"])!=5 or len(doc["raw_record_hex"])!=80: raise ValueError("record violates schema shape")
    if not 0<=doc["index"]<=82: raise ValueError("record index violates schema")
    return doc

def extract(rom_path:Path,out:Path,allow=False):
    data=rom_path.read_bytes(); digest=validate_rom(data,allow); rs=extract_records(data)
    if any(serialize_record(r)!=r.raw for r in rs): raise AssertionError('round trip failed')
    out.mkdir(parents=True,exist_ok=True); rows=[validate_record_document(record_dict(r,data)) for r in rs]
    (out/'records.json').write_text(json.dumps(rows,indent=2)+'\n')
    cols=['index','source_offset','runtime_address','display_name','season','field_14_ptr','field_18_ptr','field_1c_bytes','field_20_bytes','field_24_u8','field_26_u16','raw_record_hex']
    with (out/'records.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
      for x in rows:w.writerow({k:(x['display_names']['english'] if k=='display_name' else x[k]) for k in cols})
    summary={'rom_sha256':digest,'table_offset':'0x0007A1F4','table_end_exclusive':'0x0007AEE4','record_count':83,'stride':40,'round_trip':'byte-perfect'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (out/'summary.txt').write_text('\n'.join(f'{k}: {v}' for k,v in summary.items())+'\n')
    return summary

def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--rom',required=True,type=Path);p.add_argument('--table',choices=['beyblades'],required=True);p.add_argument('--output',required=True,type=Path);p.add_argument('--allow-unsupported-rom',action='store_true');a=p.parse_args(argv)
 try: print(json.dumps(extract(a.rom,a.output,a.allow_unsupported_rom),indent=2))
 except (OSError,ValueError) as e:p.error(str(e))
if __name__=='__main__':main()
