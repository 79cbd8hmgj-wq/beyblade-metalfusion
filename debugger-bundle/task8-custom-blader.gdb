# Task 8 custom blader planned runtime experiments. Requires mGBA gdb stub on 127.0.0.1:2345.
target remote 127.0.0.1:2345
set pagination off
# Existing name-entry localized row and candidate functions remain static-only.
b *0x08045198
commands
 silent
 printf "save serializer hit pc=%08x\n", $pc
 continue
end
b *0x08045590
commands
 silent
 printf "save deserializer hit pc=%08x\n", $pc
 continue
end
# Candidate localized protagonist table pointer range for manual watch experiments.
printf "Task8 script loaded: set hardware watchpoints on EEPROM tail blocks 0x3EF-0x3FF during save/load cycles.\n"
