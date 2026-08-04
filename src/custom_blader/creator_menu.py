from __future__ import annotations
from dataclasses import dataclass
from .custom_state import default_state, sanitize
STEPS=['player_name','bey_name','avatar','skin','hair','outfit','portrait','origin','tendency','summary','confirm']
@dataclass
class CreatorModel:
    index:int=0
    state:object=None
    cancelled:bool=False
    def __post_init__(self):
        if self.state is None: self.state=default_state()
    @property
    def step(self): return STEPS[self.index]
    def next(self): self.index=min(self.index+1,len(STEPS)-1); return self
    def back(self): self.index=max(self.index-1,0); return self
    def cancel(self): self.cancelled=True; return self
    def choose(self,field,value): setattr(self.state,field,value); sanitize(self.state); return self
