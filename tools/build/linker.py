from __future__ import annotations


def linker_script(address, entry=None, absolute_symbols=None):
    symbols = absolute_symbols or {}
    lines = [
        'OUTPUT_FORMAT("elf32-littlearm")',
        'OUTPUT_ARCH(arm)',
    ]
    if entry:
        lines.append(f'ENTRY({entry})')
    for name, value in sorted(symbols.items()):
        if not name.replace('_', '').isalnum() or name[0].isdigit():
            raise ValueError(f'invalid linker symbol: {name}')
        lines.append(f'{name} = 0x{int(value):08x};')
    lines.extend(
        [
            'SECTIONS {',
            f' . = 0x{address:08x};',
            ' .text : { *(.text.task8_entry) *(.text*) }',
            ' .rodata : { *(.rodata*) }',
            ' .data : { *(.data*) }',
            ' .bss : { *(.bss*) }',
            ' /DISCARD/ : { *(.ARM.attributes) *(.ARM.exidx*) *(.ARM.extab*) *(.comment) *(.note*) }',
            '}',
            '',
        ]
    )
    return '\n'.join(lines)


def parse_map(text):
    out = {}
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            if parts[0].startswith('0x'):
                address = int(parts[0], 16)
            else:
                address = int(parts[0], 16)
        except ValueError:
            continue
        symbol = parts[-1]
        if symbol and not symbol.startswith('.'):
            out[symbol] = address
    return out
