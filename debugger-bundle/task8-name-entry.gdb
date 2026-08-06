set pagination off
set confirm off
set endian little
set architecture armv4t
target remote 127.0.0.1:2345
set $task8_hits = 0

# Retail name-entry initialization. This establishes the keyboard buffer and
# lets the trace distinguish scene entry from the final commit path.
b *0x0806645c
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=name-entry|event=scene-init|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 continue
end

# Confirmed retail selection/confirm handler.
b *0x080668c8
commands
 silent
 set $task8_hits = $task8_hits + 1
 set $task8_root = *(unsigned int *)0x03000198
 set $task8_slot = $task8_root + 0x18c8
 set $task8_keyboard = *(unsigned int *)0x030009ac
 printf "TASK8|experiment=name-entry|event=retail-handler|pc=0x%08x|root=0x%08x|slot=0x%08x|keyboard=0x%08x\n", $pc, $task8_root, $task8_slot, $task8_keyboard
 x/16bx $task8_keyboard
 x/64bx $task8_slot
 continue
end

# Patched module entry replacing the retail copy call at ROM 0x00066962.
b *0x08400078
commands
 silent
 set $task8_hits = $task8_hits + 1
 set $task8_root = *(unsigned int *)0x03000198
 set $task8_slot = $task8_root + 0x18c8
 printf "TASK8|experiment=name-entry|event=native-name-hook|pc=0x%08x|source=0x%08x|retail-destination=0x%08x|length=%u|slot=0x%08x\n", $pc, $r0, $r1, $r2, $task8_slot
 x/16bx $r0
 x/64bx $task8_slot
 continue
end

# C persistence routine receives r0=SU8C slot and r1=retail 16-byte buffer.
b *0x084002f8
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=name-entry|event=commit-player-name|pc=0x%08x|slot=0x%08x|source=0x%08x\n", $pc, $r0, $r1
 x/16bx $r1
 x/64bx $r0
 continue
end

# First instruction after the replaced retail BL. The retail runtime name and
# the custom slot must both contain the entered value at this point.
b *0x08066966
commands
 silent
 set $task8_hits = $task8_hits + 1
 set $task8_root = *(unsigned int *)0x03000198
 set $task8_slot = $task8_root + 0x18c8
 set $task8_retail_name = $task8_root + 0x858
 printf "TASK8|experiment=name-entry|event=commit-returned|pc=0x%08x|retail-name=0x%08x|slot=0x%08x\n", $pc, $task8_retail_name, $task8_slot
 x/16bx $task8_retail_name
 x/64bx $task8_slot
 disconnect
 quit
end

printf "TASK8|experiment=name-entry|event=armed|pc=0x%08x\n", $pc
continue
