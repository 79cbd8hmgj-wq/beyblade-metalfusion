set pagination off
set confirm off
set endian little
set architecture armv4t
target remote 127.0.0.1:2345
set $task8_hits = 0

# Three static consumers of the descriptor at ROM 0x000BAE54 whose +0x14
# field points to the localized Enter name row. Their semantics remain
# candidates until one triggers during the retail name-entry flow.
b *0x0806645c
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=name-entry|event=function|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 x/32bx $r0
 if $task8_hits >= 12
  disconnect
  quit
 end
 continue
end

b *0x080668c8
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=name-entry|event=function|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 x/32bx $r0
 if $task8_hits >= 12
  disconnect
  quit
 end
 continue
end

b *0x08066984
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=name-entry|event=function|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 x/32bx $r0
 if $task8_hits >= 12
  disconnect
  quit
 end
 continue
end

printf "TASK8|experiment=name-entry|event=armed|pc=0x%08x\n", $pc
continue
