"""Experimental CLI helpers for Task 8 custom save extension stored in EEPROM tail slots."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from src.custom_blader.custom_state import CustomBladerState, sanitize
from src.custom_blader.custom_save import SLOT_SIZE, parse_slot, serialize_slot, select_newest
from .save_format import SaveImage, TAIL_OFFSET, EEPROM_SIZE, SaveFormatError
A0=0; B0=64
WARNING='WARNING: EEPROM tail extension is unverified; operate only on copied saves.'

def extension_report(data:bytes)->dict:
    img=SaveImage.parse(data, allow_padding=True)
    a=img.tail[A0:A0+SLOT_SIZE]; b=img.tail[B0:B0+SLOT_SIZE]
    pa=parse_slot(a); pb=parse_slot(b); newest=select_newest(a,b)
    return {'tail_offset':f'0x{TAIL_OFFSET:04X}','slot_a':{'blocks':'0x3EF-0x3F6','valid':pa[0],'sequence':pa[1],'status':pa[3]},'slot_b':{'blocks':'0x3F7-0x3FE','valid':pb[0],'sequence':pb[1],'status':pb[3]},'reserved_block':'0x3FF','safety':'unverified','selected':{'slot':newest[0],'sequence':newest[1],'state':newest[2].to_dict()}}

def write_extension(source:Path,output:Path,state:CustomBladerState,sequence:int|None=None,allow_unverified:bool=False)->None:
    if not allow_unverified: raise SaveFormatError('refusing unverified EEPROM-tail edit without --allow-unverified-tail-extension')
    if source.resolve()==output.resolve(): raise SaveFormatError('refusing in-place custom extension edit')
    raw=bytearray(source.read_bytes())
    if len(raw) < EEPROM_SIZE: raise SaveFormatError('save must contain at least one 0x2000-byte EEPROM image')
    img=SaveImage.parse(bytes(raw[:EEPROM_SIZE]), allow_padding=False)
    selected=select_newest(img.tail[A0:A0+SLOT_SIZE], img.tail[B0:B0+SLOT_SIZE])
    seq=((selected[1]+1)&0xffffffff) if sequence is None else sequence&0xffffffff
    target=(B0 if selected[0]=='A' else A0)+TAIL_OFFSET
    before=bytes(raw)
    raw[target:target+SLOT_SIZE]=serialize_slot(sanitize(state),seq)
    if before[:TAIL_OFFSET]!=bytes(raw[:TAIL_OFFSET]): raise SaveFormatError('internal error: bytes before tail changed')
    if len(before)>EEPROM_SIZE and before[EEPROM_SIZE:]!=bytes(raw[EEPROM_SIZE:]): raise SaveFormatError('internal error: wrapper/padding bytes changed')
    output.write_bytes(bytes(raw))

def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument('--save',required=True); p.add_argument('--output'); p.add_argument('--set-player-name'); p.add_argument('--set-bey-name'); p.add_argument('--avatar',type=int); p.add_argument('--portrait',type=int); p.add_argument('--origin',type=int); p.add_argument('--tendency',type=int); p.add_argument('--allow-unverified-tail-extension',action='store_true')
    a=p.parse_args(argv); data=Path(a.save).read_bytes(); rep=extension_report(data)
    if not a.output:
        print(json.dumps(rep,indent=2,sort_keys=True)); return
    if not a.allow_unverified_tail_extension:
        p.error('editing requires --allow-unverified-tail-extension; use copied saves only')
    print(WARNING,file=sys.stderr)
    st=CustomBladerState(**rep['selected']['state'])
    if a.set_player_name is not None: st.player_name=a.set_player_name
    if a.set_bey_name is not None: st.bey_name=a.set_bey_name
    if a.avatar is not None: st.avatar_id=a.avatar
    if a.portrait is not None: st.portrait_id=a.portrait
    if a.origin is not None: st.origin_id=a.origin
    if a.tendency is not None: st.tendency_id=a.tendency
    write_extension(Path(a.save),Path(a.output),sanitize(st),allow_unverified=True)
if __name__=='__main__': main()
