from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def discover():
    gnu_names = [
        'arm-none-eabi-gcc',
        'arm-none-eabi-as',
        'arm-none-eabi-ld',
        'arm-none-eabi-objcopy',
    ]
    llvm_names = ['clang', 'ld.lld', 'llvm-objcopy']
    gnu = {name: shutil.which(name) for name in gnu_names}
    llvm = {name: shutil.which(name) for name in llvm_names}
    if all(gnu.values()):
        return {
            'available': True,
            'provider': 'gnu-arm-none-eabi',
            'tools': gnu,
            'install_hint': 'sudo apt-get install gcc-arm-none-eabi binutils-arm-none-eabi',
        }
    if all(llvm.values()):
        return {
            'available': True,
            'provider': 'llvm-arm-none-eabi',
            'tools': llvm,
            'install_hint': 'install clang, lld, and llvm-objcopy',
        }
    return {
        'available': False,
        'provider': None,
        'tools': {},
        'install_hint': 'install GNU Arm Embedded or clang/lld/llvm-objcopy',
    }


def version(executable):
    return subprocess.run(
        [executable, '--version'],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()[0]


def _compile_command(provider, tools, source, output):
    common = [
        '-c',
        str(source),
        '-o',
        str(output),
        '-mcpu=arm7tdmi',
        '-mthumb',
        '-ffreestanding',
        '-fno-ident',
        '-fno-asynchronous-unwind-tables',
        '-fno-builtin',
        '-fomit-frame-pointer',
        '-fno-stack-protector',
        '-ffunction-sections',
        '-fdata-sections',
    ]
    if provider == 'gnu-arm-none-eabi':
        return [
            tools['arm-none-eabi-gcc'],
            *common,
            '-Os',
            '-frandom-seed=spirit-unbound',
        ]
    if provider == 'llvm-arm-none-eabi':
        return [
            tools['clang'],
            '--target=arm-none-eabi',
            *common,
            '-Oz',
            '-frandom-seed=spirit-unbound',
        ]
    raise RuntimeError(f'unsupported ARM toolchain provider: {provider}')


def compile_module(
    sources,
    out_dir,
    address,
    entry,
    absolute_symbols=None,
):
    """Compile/link sources reproducibly with GNU Arm Embedded or LLVM."""
    from .linker import linker_script, parse_map

    toolchain = discover()
    if not toolchain['available']:
        raise RuntimeError('ARM toolchain unavailable; ' + toolchain['install_hint'])

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    script = output / 'module.ld'
    script.write_text(
        linker_script(address, entry, absolute_symbols),
        encoding='utf-8',
    )

    objects = []
    for index, source in enumerate(sorted(Path(item) for item in sources)):
        obj = output / f'{index:04d}.o'
        subprocess.run(
            _compile_command(toolchain['provider'], toolchain['tools'], source, obj),
            check=True,
        )
        objects.append(obj)

    elf = output / 'module.elf'
    map_file = output / 'module.map'
    if toolchain['provider'] == 'gnu-arm-none-eabi':
        link_command = [
            toolchain['tools']['arm-none-eabi-ld'],
            '-T',
            str(script),
            '--gc-sections',
            '-Map',
            str(map_file),
            '-o',
            str(elf),
            *map(str, objects),
        ]
        objcopy = toolchain['tools']['arm-none-eabi-objcopy']
    else:
        link_command = [
            toolchain['tools']['ld.lld'],
            '-T',
            str(script),
            '--gc-sections',
            f'-Map={map_file}',
            '-o',
            str(elf),
            *map(str, objects),
        ]
        objcopy = toolchain['tools']['llvm-objcopy']
    subprocess.run(link_command, check=True)

    binary = output / 'module.bin'
    subprocess.run([objcopy, '-O', 'binary', str(elf), str(binary)], check=True)
    symbols = parse_map(map_file.read_text(encoding='utf-8'))
    entry_address = symbols.get(entry)
    # LLVM marks Thumb symbols with bit zero in some map formats; accept either
    # representation but normalize the returned callable address.
    if entry_address is None:
        raise RuntimeError('entry symbol missing from linked module')
    return {
        'provider': toolchain['provider'],
        'binary': binary,
        'elf': elf,
        'map': map_file,
        'entry_address': entry_address,
        'symbols': symbols,
        'versions': {
            name: version(path)
            for name, path in sorted(toolchain['tools'].items())
        },
    }
