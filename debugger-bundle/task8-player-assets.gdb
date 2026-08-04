set pagination off
set confirm off
set endian little
set architecture armv4t
target remote 127.0.0.1:2345
set $task8_hits = 0

# Strongly supported protagonist-name row consumer. This is the first verified
# player-specific presentation lookup and provides a language-index baseline.
b *0x0802e4dc
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=player-assets|event=protagonist-row-consumer|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 if $task8_hits >= 32
  disconnect
  quit
 end
 continue
end

# Instruction that loads the row itself. Capturing surrounding registers after
# stopping here helps identify the language source and text destination.
b *0x0802e598
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=player-assets|event=row-load|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x|r4=0x%08x|r6=0x%08x\n", $pc, $r0, $r1, $r2, $r3, $r4, $r6
 x/5wx 0x08077f10
 if $task8_hits >= 32
  disconnect
  quit
 end
 continue
end

printf "TASK8|experiment=player-assets|event=armed|pc=0x%08x\n", $pc
continue
