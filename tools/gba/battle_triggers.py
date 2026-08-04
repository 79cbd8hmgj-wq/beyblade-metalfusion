"""Lossless neutral view of the observed TriggerBattle word streams."""
from dataclasses import dataclass
import struct
@dataclass(frozen=True)
class BattleTrigger:
    words:tuple[int,...]; raw:bytes
    @classmethod
    def parse(cls,data:bytes):
        if not data or len(data)%4: raise ValueError("trigger must contain aligned words")
        return cls(struct.unpack("<"+"I"*(len(data)//4),data),data)
    def to_bytes(self): return self.raw
