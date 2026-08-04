# Task 6 static anchors. Use only with a copied save/state.
set pagination off
set confirm off
# Native tournament/progression entry points
break *0x0802c6ac
break *0x0802c70c
break *0x0802cc58
break *0x0802ccc4
break *0x0802d144
break *0x0802d184
break *0x0802d1c4
break *0x0802d258
break *0x08042f08
commands
 silent
 printf "TASK6 pc=%08x r0=%08x r1=%08x r2=%08x r3=%08x sp=%08x lr=%08x\n",$pc,$r0,$r1,$r2,$r3,$sp,$lr
 x/16wx $r0
 continue
end
# Stream targets are DATA: do not set execution breakpoints at 0x0809b350.
# Set a read watchpoint only after the central consumer register is identified.
