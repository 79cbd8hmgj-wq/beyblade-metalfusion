"""ASCII catalogue with references, duplicates, clusters, and conservative labels."""
from __future__ import annotations
import re, struct
from collections import Counter, defaultdict
from .address import offset_to_address

ANCHORS=("getBeyBladeWithIndex","getRandomBeyBladeFromSeason","removeBladeFromTysonsCollection","initTournament","addTournamentPoints","getWinningTeam","getLosingTeam","getPointsDifference","initBattleOverlays","drawSelectMoveMenu","initBeybladeMenu","updateAttackHold","initRipCord")
def classify_text(s:str)->str:
    lo=s.lower()
    if re.search(r"\.(c|h|cpp)$|[/\\].*\.(c|h)",s): return "source filenames and build paths"
    if any(x in lo for x in ("assert","error","failed")): return "assertions and errors"
    if re.fullmatch(r"(?:get|set|init|update|draw|add|remove)[A-Za-z0-9_]+",s): return "debug/function identifiers"
    if any(x in lo for x in ("beyblade","blade","dragoon","dranzer","driger","draciel")): return "Beyblade names"
    if any(x in lo for x in ("attack","move","ripcord")): return "move and attack names"
    if re.fullmatch(r"[A-Z][A-Z0-9_]{3,}",s): return "enum-like identifiers"
    if any(x in lo for x in ("menu","select","press start","continue","options")): return "menu/interface text"
    if len(s)>35 and " " in s: return "dialogue candidates"
    return "unknown"
def scan(data:bytes,min_length:int=4):
    ptrrefs=Counter()
    for i in range(0,len(data)-3,4):
        v=struct.unpack_from("<I",data,i)[0]&~1
        if 0x08000000<=v<0x0e000000: ptrrefs[(v-0x08000000)%0x2000000]+=1
    out=[]
    for m in re.finditer(rb"[ -~]{%d,}"%min_length,data):
        a,b=m.span(); text=m.group().decode("ascii"); null=b<len(data) and data[b]==0
        lp=a>0 and data[a-1]==len(text) and len(text)<256
        out.append({"offset":a,"address":offset_to_address(a),"text":text,"length":len(text),"null_terminated":null,"length_prefixed":lp,"alignment":a%4,"pointer_references":ptrrefs[a],"classification":classify_text(text)})
    dup=Counter(x["text"] for x in out)
    for x in out:x["duplicate_count"]=dup[x["text"]]
    return out
def clusters(strings,gap=128):
    groups=[]
    for s in strings:
        if not groups or s["offset"]-groups[-1][-1]["offset"]>gap: groups.append([s])
        else: groups[-1].append(s)
    return [g for g in groups if len(g)>=3]
