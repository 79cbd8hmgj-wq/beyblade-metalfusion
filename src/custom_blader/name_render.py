from __future__ import annotations
import re
from .custom_state import CustomBladerState, default_state
FIXED=('Tyson','Takao')
_PATTERN=re.compile(r"\b(Tyson|Takao|TYSON|TAKAO)\b")
def substitute(text:str,state:CustomBladerState|None=None,intentional_npc:bool=False)->str:
    if intentional_npc: return text
    name=(state or default_state()).player_name
    def repl(match:re.Match[str])->str:
        token=match.group(0)
        return name.upper() if token.isupper() else name
    return _PATTERN.sub(repl,text)
