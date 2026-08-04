set pagination off
set confirm off
set endian little
set architecture armv4t
target remote 127.0.0.1:2345
set $task8_hits = 0

# EEPROM_V124 read candidate: r0=block index, r1=destination candidate.
b *0x08067584
commands
 silent
 set $task8_hits = $task8_hits + 1
 if $r0 >= 0x3ef
  printf "TASK8|experiment=eeprom-tail|event=read|pc=0x%08x|block=0x%x|buffer=0x%08x|write=false\n", $pc, $r0, $r1
 end
 if $task8_hits >= 4096
  disconnect
  quit
 end
 continue
end

# Program wrapper candidate: r0=block index, r1=source candidate.
b *0x08067634
commands
 silent
 set $task8_hits = $task8_hits + 1
 if $r0 >= 0x3ef
  printf "TASK8|experiment=eeprom-tail|event=write-wrapper|pc=0x%08x|block=0x%x|buffer=0x%08x|write=true\n", $pc, $r0, $r1
  x/8bx $r1
 end
 if $task8_hits >= 4096
  disconnect
  quit
 end
 continue
end

# Extended program candidate, retained separately in case the wrapper is bypassed.
b *0x08067648
commands
 silent
 set $task8_hits = $task8_hits + 1
 if $r0 >= 0x3ef
  printf "TASK8|experiment=eeprom-tail|event=write|pc=0x%08x|block=0x%x|buffer=0x%08x|write=true\n", $pc, $r0, $r1
  x/8bx $r1
 end
 if $task8_hits >= 4096
  disconnect
  quit
 end
 continue
end

printf "TASK8|experiment=eeprom-tail|event=armed|pc=0x%08x\n", $pc
continue
