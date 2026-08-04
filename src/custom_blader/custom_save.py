"""64-byte transaction slot model for Task 8 custom save extension."""
from __future__ import annotations
import binascii, struct
from .custom_state import CustomBladerState, default_state, sanitize, MAX_NAME, SCHEMA_VERSION
SLOT_SIZE=64; SLOT_A_BLOCKS=(0x3EF,0x3F6); SLOT_B_BLOCKS=(0x3F7,0x3FE); RESERVED_BLOCK=0x3FF
MAGIC=b'SU8C'; COMMIT=b'OK8!'

def _enc(s): return s.encode('ascii','replace')[:MAX_NAME].ljust(MAX_NAME,b'\0')
def _dec(b): return b.split(b'\0',1)[0].decode('ascii','replace')
def crc(data:bytes)->int: return binascii.crc32(data)&0xffffffff

def serialize_slot(state:CustomBladerState, sequence:int)->bytes:
    state=sanitize(state)
    body=bytearray(56)
    body[0:4]=MAGIC; struct.pack_into('<I',body,4,sequence&0xffffffff); body[8]=SCHEMA_VERSION; body[9]=state.initialized&0xff
    body[10:22]=_enc(state.player_name); body[22:34]=_enc(state.bey_name)
    body[34:46]=bytes([state.avatar_id,state.portrait_id,state.skin_palette_id,state.hair_style_id,state.hair_palette_id,state.outfit_palette_id,state.origin_id,state.tendency_id,state.blank_core_state,state.blank_core_id,state.current_template_id,state.future_flags])
    body[46:50]=struct.pack('<BBBB',state.attack_ring_id,state.weight_disk_id,state.spin_gear_id,state.blade_base_id)
    body[50:54]=struct.pack('<I',state.validation)
    tail=struct.pack('<I4s',crc(bytes(body)),COMMIT)
    return bytes(body)+tail

def parse_slot(raw:bytes)->tuple[bool,int,CustomBladerState|None,str]:
    if len(raw)!=SLOT_SIZE: return False,0,None,'slot must be 64 bytes'
    if raw[0:4]!=MAGIC: return False,0,None,'missing magic'
    if raw[60:64]!=COMMIT: return False,0,None,'missing commit'
    got=struct.unpack_from('<I',raw,56)[0]
    if got!=crc(raw[:56]): return False,0,None,'crc mismatch'
    if raw[8]>SCHEMA_VERSION: return False,0,None,'newer schema'
    seq=struct.unpack_from('<I',raw,4)[0]
    fields=list(raw[34:46]); comps=list(raw[46:50]); validation=struct.unpack_from('<I',raw,50)[0]
    st=CustomBladerState(
        schema_version=raw[8], initialized=raw[9], player_name=_dec(raw[10:22]), bey_name=_dec(raw[22:34]),
        avatar_id=fields[0], portrait_id=fields[1], skin_palette_id=fields[2], hair_style_id=fields[3],
        hair_palette_id=fields[4], outfit_palette_id=fields[5], origin_id=fields[6], tendency_id=fields[7],
        blank_core_state=fields[8], blank_core_id=fields[9], current_template_id=fields[10], future_flags=fields[11],
        attack_ring_id=comps[0], weight_disk_id=comps[1], spin_gear_id=comps[2], blade_base_id=comps[3], validation=validation)
    st=sanitize(st)
    return True,seq,st,'valid'

def seq_newer(a:int,b:int)->bool: return ((a-b)&0xffffffff)<0x80000000 and a!=b

def select_newest(slot_a:bytes,slot_b:bytes):
    va,sa,sta,ea=parse_slot(slot_a); vb,sb,stb,eb=parse_slot(slot_b)
    if va and vb: return ('A',sa,sta) if seq_newer(sa,sb) else ('B',sb,stb)
    if va: return ('A',sa,sta)
    if vb: return ('B',sb,stb)
    return ('default',0,default_state())
