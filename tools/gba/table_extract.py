"""Deterministic Task 2 Beyblade table extractor; never writes a ROM."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from .beyblade_table import *
from .component_tables import CATEGORIES, CATEGORY_BY_SLUG, LANGUAGES as COMPONENT_LANGUAGES, extract_category, serialize_pointer_arrays
from .move_tables import extract_pairs, serialize_pairs, PAIR_OFFSET, END as MOVE_END
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

def extract_components(rom_path:Path,out:Path,table:str,allow=False):
    data=rom_path.read_bytes(); digest=validate_rom(data,allow)
    specs=CATEGORIES if table=='components' else (CATEGORY_BY_SLUG[table],)
    out.mkdir(parents=True,exist_ok=True); all_rows=[]
    for spec in specs:
      entries=extract_category(data,spec.slug)
      original=data[spec.offset:spec.end]
      if serialize_pointer_arrays(entries)!=original: raise AssertionError(f'{spec.slug} round trip failed')
      rows=[{'category':x.category,'local_id':x.local_id,'global_id':None,
             'source_offset':f'0x{x.source_offset:08X}','runtime_address':f'0x{ROM_BASE+x.source_offset:08X}',
             'display_names':dict(zip(COMPONENT_LANGUAGES,x.names)),
             'name_pointers':[f'0x{p:08X}' for p in x.pointers],
             'confidence':'confirmed','evidence':['five language-major pointer arrays; IDs correlate with complete-template field']}
            for x in entries]
      (out/f'{spec.slug}.json').write_text(json.dumps(rows,indent=2)+'\n'); all_rows += rows
    (out/'records.json').write_text(json.dumps(all_rows,indent=2)+'\n')
    cols=['category','local_id','source_offset','runtime_address','display_name','confidence']
    with (out/'records.csv').open('w',newline='') as f:
      w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
      for x in all_rows:w.writerow({**{k:x[k] for k in cols if k!='display_name'},'display_name':x['display_names']['english']})
    summary={'rom_sha256':digest,'table':table,'categories':{s.slug:s.count for s in specs},
             'record_count':len(all_rows),'round_trip':'byte-perfect'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary

def extract_moves(rom_path:Path,out:Path,allow=False):
    data=rom_path.read_bytes();digest=validate_rom(data,allow);pairs=extract_pairs(data)
    if serialize_pairs(pairs)!=data[PAIR_OFFSET:MOVE_END]: raise AssertionError('move lookup round trip failed')
    out.mkdir(parents=True,exist_ok=True)
    def clean(row): return {**row,'source_offset':f"0x{row['source_offset']:08X}",'runtime_address':f"0x{row['runtime_address']:08X}",'pointers':[f'0x{x:08X}' for x in row['pointers']],'names':dict(zip(COMPONENT_LANGUAGES,row['names']))}
    doc=[{'pair_id':p['pair_id'],'bit_beast':clean(p['bit_beast']),'special_move':clean(p['special_move']),'confidence':'strongly_supported'} for p in pairs]
    (out/'special-moves.json').write_text(json.dumps(doc,indent=2)+'\n')
    summary={'rom_sha256':digest,'pair_count':32,'start':'0x00079CF4','end_exclusive':'0x0007A1F4','round_trip':'byte-perfect'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary

def main(argv=None):
 choices=['beyblades','components','bit-beasts-and-moves',*CATEGORY_BY_SLUG]
 p=argparse.ArgumentParser();p.add_argument('--rom',required=True,type=Path);p.add_argument('--table',choices=choices,required=True);p.add_argument('--output',required=True,type=Path);p.add_argument('--allow-unsupported-rom',action='store_true');a=p.parse_args(argv)
 try:
  fn=extract if a.table=='beyblades' else extract_moves if a.table=='bit-beasts-and-moves' else extract_components
  print(json.dumps(fn(a.rom,a.output,a.allow_unsupported_rom) if fn is not extract_components else fn(a.rom,a.output,a.table,a.allow_unsupported_rom),indent=2))
 except (OSError,ValueError) as e:p.error(str(e))
if __name__=='__main__':main()
