"""Lossless tokenizer for synthetic/isolated dialogue control streams."""
from dataclasses import dataclass

@dataclass(frozen=True)
class TextToken: raw:bytes; kind:str

def parse_control_stream(data:bytes)->list[TextToken]:
    out=[]; i=0; text=bytearray()
    def flush():
        if text: out.append(TextToken(bytes(text),"text")); text.clear()
    while i<len(data):
        b=data[i]
        if b==0: flush(); out.append(TextToken(b"\0","end")); i+=1
        elif b<0x20:
            flush(); width=2 if b in (1,2,3) else 1
            if i+width>len(data): raise ValueError("truncated control code")
            out.append(TextToken(data[i:i+width],"control")); i+=width
        else: text.append(b); i+=1
    flush(); return out

def encode_control_stream(tokens:list[TextToken])->bytes: return b"".join(t.raw for t in tokens)

def language_lookup(tables:list[list[int]], language:int, entry:int)->int:
    if not 0<=language<len(tables) or not 0<=entry<len(tables[language]): raise IndexError("language or entry out of range")
    return tables[language][entry]
