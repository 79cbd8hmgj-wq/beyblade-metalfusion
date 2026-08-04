from tools.gba.story_flags import *
def test_bit_addressing():
 assert bit_location(9)==(1,1); x=set_flag(b'\0\0',9,True); assert get_flag(x,9)
