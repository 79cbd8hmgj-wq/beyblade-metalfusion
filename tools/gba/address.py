"""GBA address conversion and memory classification."""
from __future__ import annotations
import argparse

ROM_SIZE_MAX = 0x02000000

def offset_to_address(offset: int) -> int:
    if not 0 <= offset < ROM_SIZE_MAX: raise ValueError("ROM offset outside 32 MiB window")
    return 0x08000000 + offset

def address_to_offset(address: int) -> int:
    if not 0x08000000 <= address < 0x0E000000: raise ValueError("not a Game Pak ROM address")
    return (address - 0x08000000) % ROM_SIZE_MAX

def normalize_rom_address(address: int) -> int:
    return offset_to_address(address_to_offset(address))

def split_thumb_pointer(address: int) -> tuple[int, bool]:
    return address & ~1, bool(address & 1)

def classify(address: int) -> str:
    a = address & ~1
    ranges = [(0,0x4000,"BIOS"),(0x02000000,0x02040000,"EWRAM"),(0x03000000,0x03008000,"IWRAM"),
      (0x04000000,0x04000400,"I/O registers"),(0x05000000,0x05000400,"palette RAM"),
      (0x06000000,0x06018000,"VRAM"),(0x07000000,0x07000400,"OAM"),
      (0x08000000,0x0E000000,"Game Pak ROM"),(0x0E000000,0x10000000,"Game Pak save memory")]
    return next((n for lo,hi,n in ranges if lo <= a < hi), "unmapped/unknown")

def main(argv=None):
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest="cmd",required=True)
    for cmd in ("offset-to-address","address-to-offset","classify","thumb"):
        q=sp.add_parser(cmd); q.add_argument("value",type=lambda x:int(x,0))
    a=p.parse_args(argv); v=a.value
    if a.cmd=="offset-to-address": print(f"0x{offset_to_address(v):08X}")
    elif a.cmd=="address-to-offset": print(f"0x{address_to_offset(v):08X}")
    elif a.cmd=="classify": print(classify(v))
    else:
        raw,thumb=split_thumb_pointer(v); print(f"address=0x{raw:08X} thumb={str(thumb).lower()}")
if __name__=="__main__": main()
