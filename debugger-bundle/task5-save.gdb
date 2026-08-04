set pagination off
set confirm off
# Boot/config and load
break *0x080674bc
break *0x08044a8c
break *0x08067584
break *0x08044fb0
break *0x0804504c
break *0x080450e4
break *0x08045590
# Save ordering
break *0x08044dac
break *0x08044e54
break *0x08044ea0
break *0x08044f14
break *0x08044d2c
break *0x08067634
break *0x080677a8
# At each stop: info registers; x/24bx buffer pointers; record block index.
