"""Deterministic BPS1 encoder using SourceRead/TargetRead actions."""
import binascii
class BPSError(ValueError):pass
def _v(n):
 out=bytearray()
 while True:
  x=n&0x7f;n>>=7
  if n==0:out.append(x|0x80);return bytes(out)
  out.append(x);n-=1
def _read(data,p):
 n=0;shift=1
 while True:
  if p>=len(data):raise BPSError('truncated variable integer')
  x=data[p];p+=1;n+=(x&0x7f)*shift
  if x&0x80:return n,p
  shift<<=7;n+=shift

def create(source,target,metadata=b'spirit-unbound-task7'):
 out=bytearray(b'BPS1'+_v(len(source))+_v(len(target))+_v(len(metadata))+metadata);i=0
 while i<len(target):
  same=i<len(source) and source[i]==target[i];j=i+1
  while j<len(target) and (j<len(source) and source[j]==target[j])==same:j+=1
  out+=_v(((j-i-1)<<2)|(0 if same else 1))
  if not same:out+=target[i:j]
  i=j
 out+=binascii.crc32(source).to_bytes(4,'little')+binascii.crc32(target).to_bytes(4,'little')
 out+=binascii.crc32(out).to_bytes(4,'little');return bytes(out)
def apply(patch,source):
 if len(patch)<16 or patch[:4]!=b'BPS1':raise BPSError('invalid BPS header')
 if binascii.crc32(patch[:-4])!=(int.from_bytes(patch[-4:],'little')):raise BPSError('patch CRC mismatch')
 p=4;ss,p=_read(patch,p);ts,p=_read(patch,p);ms,p=_read(patch,p);p+=ms
 if ss!=len(source):raise BPSError('source size mismatch')
 if binascii.crc32(source)!=int.from_bytes(patch[-12:-8],'little'):raise BPSError('source CRC mismatch')
 out=bytearray()
 while len(out)<ts:
  action,p=_read(patch,p);n=(action>>2)+1;kind=action&3
  if kind==0:out+=source[len(out):len(out)+n]
  elif kind==1:out+=patch[p:p+n];p+=n
  else:raise BPSError('unsupported copy action')
 if len(out)!=ts:raise BPSError('target size mismatch')
 if binascii.crc32(out)!=int.from_bytes(patch[-8:-4],'little'):raise BPSError('target CRC mismatch')
 return bytes(out)
