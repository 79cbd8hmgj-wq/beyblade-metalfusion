"""Small helpers shared by future semantic field decoders."""
from dataclasses import dataclass
@dataclass(frozen=True)
class SaveField:
 offset:int; size:int; name:str; confidence:str
 def __post_init__(self):
  if self.offset<0 or self.size<=0 or self.confidence not in {'confirmed','strongly_supported','candidate','unknown'}:raise ValueError('invalid save field')
