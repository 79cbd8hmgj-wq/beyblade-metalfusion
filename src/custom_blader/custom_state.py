"""Task 8 custom Blader state reference model.

This Python model is the authoritative source for save tools and tests. The ROM
profile currently carries the matching metadata in expansion space; native hooks
remain documented as unresolved until runtime patch sites are proven.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import re
SCHEMA_VERSION=1
MAX_NAME=12
DEFAULT_PLAYER_NAME="Blader"
DEFAULT_BEY_NAME="Blank Bey"
BLANK_CORE_ID=0xF0
BLANK_CORE_DORMANT=0
VALID_IDS=range(4)
ENC_RE=re.compile(r"^[ A-Za-z0-9'\-]{1,12}$")

@dataclass
class CustomBladerState:
    schema_version:int=SCHEMA_VERSION
    initialized:int=0
    player_name:str=DEFAULT_PLAYER_NAME
    bey_name:str=DEFAULT_BEY_NAME
    avatar_id:int=0
    portrait_id:int=0
    skin_palette_id:int=0
    hair_style_id:int=0
    hair_palette_id:int=0
    outfit_palette_id:int=0
    origin_id:int=0
    tendency_id:int=0
    blank_core_state:int=BLANK_CORE_DORMANT
    blank_core_id:int=BLANK_CORE_ID
    current_template_id:int=0
    attack_ring_id:int=0
    weight_disk_id:int=0
    spin_gear_id:int=0
    blade_base_id:int=0
    future_flags:int=0
    validation:int=0
    def to_dict(self): return asdict(self)

def normalize_name(value:str, default:str)->str:
    value=(value or '').strip()
    filtered=''.join(ch for ch in value if ch in " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'-")[:MAX_NAME]
    return filtered if filtered and ENC_RE.match(filtered) else default

def validate_id(value:int, valid=VALID_IDS)->int:
    return int(value) if int(value) in valid else 0

def default_state()->CustomBladerState:
    return sanitize(CustomBladerState(initialized=1))

def compute_validation(state:CustomBladerState)->int:
    total=0x43555354
    for key,val in state.to_dict().items():
        if key=='validation': continue
        if isinstance(val,str):
            for b in val.encode('ascii','replace'): total=((total<<5)-total+b)&0xffffffff
        else: total=((total<<5)-total+int(val))&0xffffffff
    return total

def sanitize(state:CustomBladerState)->CustomBladerState:
    state.schema_version=SCHEMA_VERSION
    state.player_name=normalize_name(state.player_name,DEFAULT_PLAYER_NAME)
    state.bey_name=normalize_name(state.bey_name,DEFAULT_BEY_NAME)
    state.avatar_id=validate_id(state.avatar_id)
    state.portrait_id=validate_id(state.portrait_id)
    state.skin_palette_id=validate_id(state.skin_palette_id)
    state.hair_style_id=state.avatar_id
    state.hair_palette_id=validate_id(state.hair_palette_id)
    state.outfit_palette_id=validate_id(state.outfit_palette_id)
    state.origin_id=validate_id(state.origin_id)
    state.tendency_id=validate_id(state.tendency_id)
    state.blank_core_state=0 if state.blank_core_state not in (0,) else state.blank_core_state
    state.blank_core_id=BLANK_CORE_ID
    for f in ('current_template_id','attack_ring_id','weight_disk_id','spin_gear_id','blade_base_id','future_flags'):
        setattr(state,f,max(0,min(255,int(getattr(state,f)))))
    state.validation=compute_validation(state)
    return state

def is_valid(state:CustomBladerState)->bool:
    s=sanitize(CustomBladerState(**{k:v for k,v in state.to_dict().items() if k!='validation'}))
    return s.to_dict()==state.to_dict()
