"""Bounded mGBA/GDB smoke harness; socket polling never consumes the GDB connection."""
import argparse,shutil,subprocess,time
from pathlib import Path

def _listening(port):
 needle=f'{port:04X}'
 try:
  for name in ('/proc/net/tcp','/proc/net/tcp6'):
   with open(name,encoding='ascii') as handle:
    for line in handle:
     fields=line.split()
     if len(fields)>3 and fields[1].rsplit(':',1)[-1].upper()==needle and fields[3]=='0A':return True
 except OSError:return False
 return False

def run(rom,mgba='mgba',gdb='gdb-multiarch',port=2345,timeout=10):
 rom_path=Path(rom).resolve();command=f'{mgba} -g {rom_path.name}; {gdb} -ex "target remote 127.0.0.1:{port}"'
 if not shutil.which(mgba) or not shutil.which(gdb):return {'status':'unexecuted','reason':'mGBA or gdb-multiarch unavailable','command':command}
 process=subprocess.Popen([mgba,'-g',rom_path.name],cwd=rom_path.parent,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  deadline=time.time()+timeout
  while time.time()<deadline and not _listening(port):
   if process.poll() is not None:return {'status':'failed','reason':'mGBA exited before opening GDB port','command':command}
   time.sleep(.1)
  if not _listening(port):return {'status':'failed','reason':'GDB port timeout','command':command}
  script=f'target remote 127.0.0.1:{port}\ninfo registers\np/x $pc\ncontinue&\nshell sleep 1\ninterrupt\ninfo registers pc\ndisconnect\nquit\n'
  result=subprocess.run([gdb,'-q','-nx','-batch'],input=script,text=True,capture_output=True,timeout=timeout)
  return {'status':'passed' if result.returncode==0 and process.poll() is None else 'failed','command':command,'transcript':(result.stdout+result.stderr)[-4000:]}
 finally:
  if process.poll() is None:process.terminate()
  try:process.wait(3)
  except subprocess.TimeoutExpired:process.kill()
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('rom');parser.add_argument('--mgba',default='mgba');parser.add_argument('--gdb',default='gdb-multiarch');args=parser.parse_args();print(run(args.rom,args.mgba,args.gdb))
