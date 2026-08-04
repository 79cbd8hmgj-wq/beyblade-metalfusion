import pytest
from tools.gba.script_flow import *
def test_signed_and_cfg():
 assert signed(0xfe,8)==-2
 ins=[Instruction(0,2,'conditional',2),Instruction(2,2),Instruction(4,2,'end')]
 assert build_cfg(ins)[0]==[4,2]
def test_invalid_target():
 with pytest.raises(ValueError): build_cfg([Instruction(0,2,'branch',1)])
