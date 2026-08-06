set pagination off
set confirm off
set endian little
set architecture armv4t
target remote 127.0.0.1:2345
set $task8_hits = 0

# Confirm complete-template lookup and inspect byte +0x21 (retail Bit Chip ID).
b *0x0803dcfc
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=blank-core|event=template-lookup|pc=0x%08x|template_id=%u|lr=0x%08x\n", $pc, $r0, $lr
 if $task8_hits >= 64
  disconnect
  quit
 end
 continue
end

# High-priority consumer from Task 4 that follows the complete-template pointer
# and reads packed component state near +0x1f. Runtime observation is required
# before assigning exact argument or object semantics.
b *0x08030316
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=blank-core|event=component-consumer|pc=0x%08x|r0=0x%08x|r1=0x%08x|r2=0x%08x|r3=0x%08x\n", $pc, $r0, $r1, $r2, $r3
 if $task8_hits >= 64
  disconnect
  quit
 end
 continue
end

# Move-value helper provides a safe boundary for detecting accidental retail
# Bit Beast/Special Move behavior once a future overlay is active.
b *0x080300d4
commands
 silent
 set $task8_hits = $task8_hits + 1
 printf "TASK8|experiment=blank-core|event=move-value|pc=0x%08x|participant=0x%08x|lr=0x%08x\n", $pc, $r0, $lr
 if $task8_hits >= 64
  disconnect
  quit
 end
 continue
end

printf "TASK8|experiment=blank-core|event=armed|pc=0x%08x\n", $pc
continue
