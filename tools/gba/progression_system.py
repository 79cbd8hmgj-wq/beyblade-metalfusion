"""Reference for the directly visible saturating experience addition helper."""
def saturating_experience(old:int,increment:int,maximum:int)->int:
    if not all(0<=x<=0xffff for x in (old,increment,maximum)): raise ValueError("u16 input required")
    return min(old+increment,maximum)
