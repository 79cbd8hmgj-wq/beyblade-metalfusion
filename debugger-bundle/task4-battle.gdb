set pagination off
set confirm off
target remote 127.0.0.1:2345
break *0x0802ff48
break *0x0802ffac
break *0x080300d4
break *0x08030316
commands 1
 silent
 printf "BREAK=0x0802ff48\nR0=0x%x\n", $r0
 x/wx $r0+0x2c8
 x/wx $r0+0x2cc
 x/bx $r0+0x30c
 continue
end
# Enable only after reaching a battle-ready state. Capture with:
# gdb-multiarch -x debugger-bundle/task4-battle.gdb | tee analysis/runtime/session.log
