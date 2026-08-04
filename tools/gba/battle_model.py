"""Conservative, non-patching model of the stat selector at 0x080300D4.

Only paths visible in the Thumb instructions are modeled.  Names deliberately
describe storage rather than asserting game semantics.
"""
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable

class Move(IntEnum):
    ATTACK=0; DEFENSE=1; ENDURANCE=2; BIT_BEAST=3
    BIT_BEAST_TARGET=4; JUMP=5; DODGE=6
class RpsType(IntEnum):
    ATTACK=0; DEFEND=1; COMBO=2; BIT_BEAST=3
    OTHER=4; IDLE=5; COMBO_TARGET=6; HURT=7

@dataclass(frozen=True)
class EffectiveStats:
    field_10: int
    field_14: int
    field_18: int

def move_value(move_type:int, move:int, stats:EffectiveStats,
               rng:Callable[[int],int]) -> int:
    """Instruction-order equivalent of the supported 0x080300D4 switch.

    The helper dispatches on ``move_type`` despite the debug names. Values
    outside 0..6 return zero through the default path.
    """
    if move_type == 0:
        return (stats.field_10, stats.field_10 << 1, stats.field_14)[move] if 0 <= move <= 2 else 0
    if move_type in (1, 5):
        return (stats.field_14, stats.field_10 << 1,
                stats.field_14 + (stats.field_14 << 1))[move] if 0 <= move <= 2 else 0
    if move_type == 2:
        return stats.field_10 >> 1
    if move_type == 3:
        return stats.field_10 + stats.field_14 + stats.field_18 if move == 3 else 0
    if move_type == 6:
        return rng(4)
    return 0

def clamp_nonnegative(value:int)->int:
    """Signed clamp used twice by the exchange path at 0x08030030."""
    return 0 if value < 0 else value
