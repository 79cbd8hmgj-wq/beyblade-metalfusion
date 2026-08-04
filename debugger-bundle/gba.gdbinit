set pagination off
set confirm off
set endian little
set architecture armv4t
set disassemble-next-line on
set print pretty on
set breakpoint auto-hw on

target remote 127.0.0.1:2345

printf "Connected to mGBA ARMv4T target at 127.0.0.1:2345.\n"
printf "GBA ROM is normally mapped at 0x08000000.\n"
printf "Use 'info registers', 'x/16i $pc', 'break *ADDRESS', and 'continue'.\n"
