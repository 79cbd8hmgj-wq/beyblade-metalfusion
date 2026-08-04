"""Only instruction-supported tournament comparisons and wrapping score add."""
def add_points(current:int,delta:int)->int: return (current+delta)&0xffff
def team_ahead(a:int,b:int)->int|None: return 0 if a>b else (1 if b>a else None)
def points_difference(a:int,b:int)->int: return abs(a-b)
def winning_team(a:int,b:int)->int|None: return team_ahead(a,b)
def losing_team(a:int,b:int)->int|None:
    winner=team_ahead(a,b); return None if winner is None else 1-winner
