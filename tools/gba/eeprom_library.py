"""Canonical Task-5 EEPROM anchors and checked block arithmetic."""
from .save_format import BLOCK_COUNT,BLOCK_SIZE,SaveFormatError
FUNCTIONS={0x080674bc:'configure',0x08067584:'read_dword',0x08067634:'program_wrapper',0x08067648:'program_extended',0x080677a8:'verify',0x08067800:'program_verify_retry'}
def block_offset(index:int)->int:
 if not 0<=index<BLOCK_COUNT:raise SaveFormatError('EEPROM block index out of range')
 return index*BLOCK_SIZE
