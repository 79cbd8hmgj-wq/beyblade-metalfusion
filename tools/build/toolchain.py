import shutil,subprocess
def discover():
 names=['arm-none-eabi-gcc','arm-none-eabi-as','arm-none-eabi-ld','arm-none-eabi-objcopy'];found={n:shutil.which(n) for n in names}
 return {'available':all(found.values()),'tools':found,'install_hint':'sudo apt-get install gcc-arm-none-eabi binutils-arm-none-eabi'}
def version(exe):return subprocess.run([exe,'--version'],check=True,text=True,capture_output=True).stdout.splitlines()[0]
def compile_module(sources,out_dir,address,entry):
 """Compile/link sources reproducibly; raises when the optional toolchain is absent."""
 from pathlib import Path
 from .linker import linker_script,parse_map
 tc=discover()
 if not tc['available']:raise RuntimeError('GNU Arm toolchain unavailable; '+tc['install_hint'])
 out=Path(out_dir);out.mkdir(parents=True,exist_ok=True);script=out/'module.ld';script.write_text(linker_script(address))
 objects=[]
 for i,src in enumerate(sorted(map(str,sources))):
  obj=out/f'{i:04d}.o';subprocess.run([tc['tools']['arm-none-eabi-gcc'],'-c',src,'-o',obj,'-mcpu=arm7tdmi','-mthumb','-ffreestanding','-fno-ident','-fno-asynchronous-unwind-tables','-frandom-seed=spirit-unbound'],check=True);objects.append(obj)
 elf=out/'module.elf';mp=out/'module.map';subprocess.run([tc['tools']['arm-none-eabi-ld'],'-T',script,'-Map',mp,'-o',elf,*objects],check=True)
 binary=out/'module.bin';subprocess.run([tc['tools']['arm-none-eabi-objcopy'],'-O','binary',elf,binary],check=True)
 symbols=parse_map(mp.read_text())
 if entry not in symbols:raise RuntimeError('entry symbol missing from linked module')
 return {'binary':binary,'entry_address':symbols[entry],'symbols':symbols}
