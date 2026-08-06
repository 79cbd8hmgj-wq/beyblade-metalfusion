set pagination off
set confirm off
set endian little
set architecture armv4t
target remote 127.0.0.1:2345
set $task8_hits = 0

# Candidate localized NEW GAME row consumer.
b *0x08064e10
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=new-game|event=function|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 if $task8_hits >= 16
  disconnect
  quit
 end
 continue
end

# Candidate descriptor consumer whose +0x04 field is the localized row.
b *0x080654b8
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=new-game|event=descriptor-function|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 if $task8_hits >= 16
  disconnect
  quit
 end
 continue
end

# Serializer/deserializer anchors establish whether an existing save or a new
# runtime state is active during the same session.
b *0x08045198
commands
 silent
 printf "TASK8|experiment=new-game|event=serializer|pc=0x%08x|r0=0x%08x|r1=0x%08x\n", $pc, $r0, $r1
 continue
end

b *0x08045590
commands
 silent
 printf "TASK8|experiment=new-game|event=deserializer|pc=0x%08x|r0=0x%08x|r1=0x%08x\n", $pc, $r0, $r1
 continue
end

printf "TASK8|experiment=new-game|event=armed|pc=0x%08x\n", $pc
continue
