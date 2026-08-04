from tools.gba.tournament_system import *
def test_arithmetic_and_teams():
 assert add_points(0xffff,2)==1; assert team_ahead(8,3)==0; assert losing_team(8,3)==1; assert team_ahead(4,4) is None; assert points_difference(2,7)==5
